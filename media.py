from __future__ import annotations

import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path

import requests

import config

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

VIDEO_SUFFIXES = {".mp4", ".mov", ".webm", ".mkv"}
AUDIO_SUFFIXES = {".m4a", ".mp3", ".wav", ".aac"}
ALLOWED_SUFFIXES = VIDEO_SUFFIXES | AUDIO_SUFFIXES


def media_kind(filename: str | None) -> str:
    """video | audio | script — used so diagnosis does not judge shots on audio/text."""
    if not filename:
        return "script"
    suffix = Path(filename).suffix.lower()
    if suffix in AUDIO_SUFFIXES:
        return "audio"
    if suffix in VIDEO_SUFFIXES:
        return "video"
    return "script"


MAX_UPLOAD_BYTES = 80 * 1024 * 1024  # 80MB
ASR_CHUNK_SECONDS = 25
ZHIPU_ASR_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/audio/transcriptions"
OPENAI_ASR_ENDPOINT = "https://api.openai.com/v1/audio/transcriptions"

_WHISPER_MODEL = None
_WHISPER_MODEL_NAME: str | None = None


def save_upload(file_storage) -> Path:
    if not file_storage or not file_storage.filename:
        raise ValueError("未選擇視頻／音訊檔案")

    suffix = Path(file_storage.filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError("僅支援 mp4 / mov / webm / mkv / m4a / mp3 / wav / aac")

    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > MAX_UPLOAD_BYTES:
        raise ValueError("檔案過大，請上傳 80MB 以內的短視頻")

    dest = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
    file_storage.save(dest)
    return dest


def run_ffmpeg(args: list[str]) -> None:
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"音訊處理失敗：{result.stderr[-500:]}")


def extract_wav(media_path: Path, wav_path: Path) -> None:
    run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(media_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(wav_path),
        ]
    )


def split_wav(wav_path: Path, chunk_dir: Path, seconds: int = ASR_CHUNK_SECONDS) -> list[Path]:
    chunk_dir.mkdir(parents=True, exist_ok=True)
    pattern = chunk_dir / "chunk_%03d.wav"
    run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(wav_path),
            "-f",
            "segment",
            "-segment_time",
            str(seconds),
            "-c",
            "copy",
            str(pattern),
        ]
    )
    chunks = sorted(chunk_dir.glob("chunk_*.wav"))
    if not chunks:
        raise RuntimeError("無法切分音訊，請確認檔案含有可讀音軌")
    return chunks


def _parse_asr_payload(payload) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, dict):
        for key in ("text", "transcript", "result"):
            if key in payload and isinstance(payload[key], str):
                return payload[key].strip()
        data = payload.get("data")
        if isinstance(data, dict) and isinstance(data.get("text"), str):
            return data["text"].strip()
        if isinstance(data, list):
            parts = []
            for item in data:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            return "".join(parts).strip()
    if isinstance(payload, list):
        parts = []
        for item in payload:
            parts.append(_parse_asr_payload(item))
        return "".join(parts).strip()
    return str(payload).strip()


def transcribe_wav_chunk_zhipu(wav_path: Path, api_key: str) -> str:
    # Tiny leftover segments from ffmpeg split often have no speech.
    if wav_path.stat().st_size < 8000:
        return ""

    with wav_path.open("rb") as audio_file:
        response = requests.post(
            ZHIPU_ASR_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (wav_path.name, audio_file, "audio/wav")},
            data={"model": config.zhipu_asr_model(), "stream": "false"},
            timeout=120,
        )
    if response.status_code >= 400:
        raise RuntimeError(f"智譜語音轉文字失敗（{response.status_code}）：{response.text[:300]}")
    try:
        payload = response.json()
    except json.JSONDecodeError:
        payload = response.text
    # Empty text is normal for silence / trailing chunks — caller skips them.
    return _parse_asr_payload(payload)


def transcribe_wav_chunk_openai(wav_path: Path, api_key: str) -> str:
    if wav_path.stat().st_size < 8000:
        return ""

    with wav_path.open("rb") as audio_file:
        response = requests.post(
            OPENAI_ASR_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (wav_path.name, audio_file, "audio/wav")},
            data={"model": config.openai_asr_model()},
            timeout=120,
        )
    if response.status_code >= 400:
        raise RuntimeError(f"OpenAI 語音轉文字失敗（{response.status_code}）：{response.text[:300]}")
    try:
        payload = response.json()
    except json.JSONDecodeError:
        payload = response.text
    return _parse_asr_payload(payload)


def transcribe_wav_local(wav_path: Path, lang: str | None = None) -> str:
    """On-device Whisper — no cloud API; suitable for Hong Kong."""
    global _WHISPER_MODEL, _WHISPER_MODEL_NAME
    import whisper

    model_name = config.whisper_model_name()
    if _WHISPER_MODEL is None or _WHISPER_MODEL_NAME != model_name:
        _WHISPER_MODEL = whisper.load_model(model_name)
        _WHISPER_MODEL_NAME = model_name

    bucket = config.lang_bucket(lang)
    language = "en" if bucket == "en" else "zh"

    result = _WHISPER_MODEL.transcribe(
        str(wav_path),
        language=language,
        fp16=False,
        verbose=False,
    )
    text = (result.get("text") or "").strip()
    if not text:
        raise RuntimeError("本地 Whisper 未識別到可用口播內容")
    return text


def _asr_chunk_fn(lang: str | None = None):
    provider = config.asr_provider(lang)
    if provider == "local":
        return lambda path: transcribe_wav_local(path, lang=lang)
    if provider == "openai":
        key = config.openai_key()
        if not key:
            raise RuntimeError(
                "ASR_PROVIDER=openai 但未設定 OPENAI_API_KEY。"
                "可改用本地 Whisper（ASR_PROVIDER=local），或改貼腳本。"
            )
        return lambda path: transcribe_wav_chunk_openai(path, key)
    key = config.zhipu_key()
    if not key:
        raise RuntimeError(
            "ASR_PROVIDER=zhipu 但未設定有效 ZHIPUAI_API_KEY。"
            "可改用本地 Whisper（ASR_PROVIDER=local），或改貼腳本。"
        )
    return lambda path: transcribe_wav_chunk_zhipu(path, key)


def transcribe_media(media_path: Path, lang: str | None = None) -> str:
    provider = config.asr_provider(lang)

    with tempfile.TemporaryDirectory(prefix="caixun_asr_") as tmp:
        tmp_dir = Path(tmp)
        wav_path = tmp_dir / "audio.wav"
        extract_wav(media_path, wav_path)

        # Local Whisper can take the full wav; cloud APIs stay chunked.
        if provider == "local":
            script = transcribe_wav_local(wav_path, lang=lang).strip()
        else:
            chunk_fn = _asr_chunk_fn(lang)
            chunks = split_wav(wav_path, tmp_dir / "chunks")
            parts: list[str] = []
            for chunk in chunks:
                part = (chunk_fn(chunk) or "").strip()
                if part:
                    parts.append(part)
            script = "\n".join(parts).strip()

        if len(script) < 8:
            raise RuntimeError("未能從視頻中識別出足夠的口播內容，請換一支有清晰人聲的短視頻，或改貼腳本。")
        return script
