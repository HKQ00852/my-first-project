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

ALLOWED_SUFFIXES = {
    ".mp4",
    ".mov",
    ".webm",
    ".mkv",
    ".m4a",
    ".mp3",
    ".wav",
    ".aac",
}
MAX_UPLOAD_BYTES = 80 * 1024 * 1024  # 80MB
ASR_CHUNK_SECONDS = 25
ZHIPU_ASR_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/audio/transcriptions"
OPENAI_ASR_ENDPOINT = "https://api.openai.com/v1/audio/transcriptions"


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
    text = _parse_asr_payload(payload)
    if not text:
        raise RuntimeError("智譜語音轉文字未返回可用內容")
    return text


def transcribe_wav_chunk_openai(wav_path: Path, api_key: str) -> str:
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
    text = _parse_asr_payload(payload)
    if not text:
        raise RuntimeError("OpenAI 語音轉文字未返回可用內容")
    return text


def _asr_chunk_fn(lang: str | None = None):
    provider = config.asr_provider(lang)
    if provider == "openai":
        key = config.openai_key()
        if not key:
            raise RuntimeError(
                "粵語／英文轉寫需要 OPENAI_API_KEY（Whisper）。"
                "請在 .env 填入金鑰，切換到简体後可用智譜，或改貼腳本文案。"
            )
        return lambda path: transcribe_wav_chunk_openai(path, key)
    key = config.zhipu_key()
    if not key:
        raise RuntimeError(
            "普通话转写需要 ZHIPUAI_API_KEY。"
            "请在 .env 填入密钥，切换到粵語後可用 OpenAI，或改贴脚本文案。"
        )
    return lambda path: transcribe_wav_chunk_zhipu(path, key)


def transcribe_media(media_path: Path, lang: str | None = None) -> str:
    chunk_fn = _asr_chunk_fn(lang)

    with tempfile.TemporaryDirectory(prefix="caixun_asr_") as tmp:
        tmp_dir = Path(tmp)
        wav_path = tmp_dir / "audio.wav"
        extract_wav(media_path, wav_path)
        chunks = split_wav(wav_path, tmp_dir / "chunks")
        parts: list[str] = []
        for chunk in chunks:
            parts.append(chunk_fn(chunk))
        script = "\n".join(p for p in parts if p).strip()
        if len(script) < 8:
            raise RuntimeError("未能從視頻中識別出足夠的口播內容，請換一支有清晰人聲的短視頻，或改貼腳本。")
        return script
