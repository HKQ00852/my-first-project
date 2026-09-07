from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load project .env once (does not override already-set env vars).
load_dotenv(Path(__file__).resolve().parent / ".env")


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _normalize_lang(lang: str | None) -> str:
    raw = (lang or "zh-Hant").strip()
    aliases = {
        "zh": "zh-Hant",
        "zh-HK": "zh-Hant",
        "zh-TW": "zh-Hant",
        "zh-MO": "zh-Hant",
        "zh-CN": "zh-Hans",
        "zh-SG": "zh-Hans",
        "yue": "zh-Hant",
        "cmn": "zh-Hans",
    }
    if raw in aliases:
        return aliases[raw]
    if raw in {"zh-Hant", "zh-Hans", "en"}:
        return raw
    lower = raw.lower()
    for code in ("zh-Hant", "zh-Hans", "en"):
        if lower == code.lower():
            return code
    return "zh-Hant"


def lang_bucket(lang: str | None) -> str:
    """Map UI locale to API routing bucket: yue | cmn | en."""
    code = _normalize_lang(lang)
    if code == "zh-Hans":
        return "cmn"
    if code == "en":
        return "en"
    return "yue"


def zhipu_key() -> str:
    return _env("ZHIPUAI_API_KEY")


def openai_key() -> str:
    return _env("OPENAI_API_KEY")


def deepseek_key() -> str:
    return _env("DEEPSEEK_API_KEY")


def zhipu_asr_model() -> str:
    return _env("ZHIPU_ASR_MODEL", "glm-asr-2512")


def openai_asr_model() -> str:
    return _env("OPENAI_ASR_MODEL", "whisper-1")


def zhipu_chat_model() -> str:
    return _env("ZHIPU_CHAT_MODEL", "glm-4-flash")


def openai_chat_model() -> str:
    return _env("OPENAI_CHAT_MODEL", "gpt-4o-mini")


def deepseek_chat_model() -> str:
    return _env("DEEPSEEK_CHAT_MODEL", "deepseek-chat")


def asr_provider(lang: str | None = None) -> str:
    """
    Default routing:
      粵 (zh-Hant) → openai Whisper
      普 (zh-Hans) → zhipu ASR
      EN           → openai Whisper
    Override with ASR_PROVIDER_YUE / ASR_PROVIDER_CMN / ASR_PROVIDER_EN
    or legacy ASR_PROVIDER for all locales.
    """
    bucket = lang_bucket(lang)
    legacy = _env("ASR_PROVIDER").lower()
    per_lang = {
        "yue": _env("ASR_PROVIDER_YUE", legacy or "openai").lower(),
        "cmn": _env("ASR_PROVIDER_CMN", legacy or "zhipu").lower(),
        "en": _env("ASR_PROVIDER_EN", legacy or "openai").lower(),
    }
    provider = per_lang[bucket]
    if provider not in {"zhipu", "openai"}:
        provider = "openai" if bucket != "cmn" else "zhipu"

    # If chosen key missing, fall back to the other when available.
    if provider == "openai" and not openai_key() and zhipu_key():
        return "zhipu"
    if provider == "zhipu" and not zhipu_key() and openai_key():
        return "openai"
    return provider


def diagnosis_provider(lang: str | None = None) -> str:
    """
    Default routing:
      粵 (zh-Hant) → openai
      普 (zh-Hans) → zhipu
      EN           → openai
    Override with DIAGNOSIS_PROVIDER_YUE / _CMN / _EN
    or legacy DIAGNOSIS_PROVIDER for all locales.
    """
    bucket = lang_bucket(lang)
    legacy = _env("DIAGNOSIS_PROVIDER").lower()
    per_lang = {
        "yue": _env("DIAGNOSIS_PROVIDER_YUE", legacy or "openai").lower(),
        "cmn": _env("DIAGNOSIS_PROVIDER_CMN", legacy or "zhipu").lower(),
        "en": _env("DIAGNOSIS_PROVIDER_EN", legacy or "openai").lower(),
    }
    provider = per_lang[bucket]
    if provider not in {"zhipu", "openai", "deepseek", "local"}:
        provider = "openai" if bucket != "cmn" else "zhipu"

    if provider == "openai" and not openai_key():
        if zhipu_key():
            return "zhipu"
        if deepseek_key():
            return "deepseek"
        return "local"
    if provider == "zhipu" and not zhipu_key():
        if openai_key():
            return "openai"
        if deepseek_key():
            return "deepseek"
        return "local"
    if provider == "deepseek" and not deepseek_key():
        if zhipu_key():
            return "zhipu"
        if openai_key():
            return "openai"
        return "local"
    return provider
