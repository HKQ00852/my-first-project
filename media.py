from __future__ import annotations

import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path

import requests

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
ASR_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/audio/transcriptions"
ASR_MODEL = os.getenv("ZHIPU_ASR_MODEL", "glm-asr-2512")


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
        # nested common shapes
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


def transcribe_wav_chunk(wav_path: Path, api_key: str) -> str:
    with wav_path.open("rb") as audio_file:
        response = requests.post(
            ASR_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (wav_path.name, audio_file, "audio/wav")},
            data={"model": ASR_MODEL, "stream": "false"},
            timeout=120,
        )
    if response.status_code >= 400:
        raise RuntimeError(f"語音轉文字失敗（{response.status_code}）：{response.text[:300]}")

    try:
        payload = response.json()
    except json.JSONDecodeError:
        payload = response.text
    text = _parse_asr_payload(payload)
    if not text:
        raise RuntimeError("語音轉文字未返回可用內容")
    return text


def transcribe_media(media_path: Path) -> str:
    api_key = os.getenv("ZHIPUAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "直接檢測視頻需要設定環境變數 ZHIPUAI_API_KEY（用於語音轉文字）。"
            "若暫時沒有金鑰，請改貼腳本文案。"
        )

    with tempfile.TemporaryDirectory(prefix="caixun_asr_") as tmp:
        tmp_dir = Path(tmp)
        wav_path = tmp_dir / "audio.wav"
        extract_wav(media_path, wav_path)
        chunks = split_wav(wav_path, tmp_dir / "chunks")
        parts: list[str] = []
        for chunk in chunks:
            parts.append(transcribe_wav_chunk(chunk, api_key))
        script = "\n".join(p for p in parts if p).strip()
        if len(script) < 8:
            raise RuntimeError("未能從視頻中識別出足夠的口播內容，請換一支有清晰人聲的短視頻，或改貼腳本。")
        return script
