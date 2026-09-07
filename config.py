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


def hkbu_key() -> str:
    # Prefer HKBU_API_KEY; also accept mistaken paste into ZHIPUAI_API_KEY
    # when it looks like a university UUID key (no dot).
    primary = _env("HKBU_API_KEY")
    if primary:
        return primary
    legacy = _env("ZHIPUAI_API_KEY")
    if legacy and "." not in legacy:
        return legacy
    return ""


def zhipu_key() -> str:
    key = _env("ZHIPUAI_API_KEY")
    # UUID-only keys are treated as HKBU, not Zhipu.
    if key and "." not in key and not _env("HKBU_API_KEY"):
        return ""
    return key


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


def hkbu_base_url() -> str:
    return _env("HKBU_API_BASE", "https://genai.hkbu.edu.hk/general/rest")


def hkbu_deployment() -> str:
    return _env("HKBU_DEPLOYMENT", "gpt-4.1-mini")


def hkbu_api_version() -> str:
    return _env("HKBU_API_VERSION", "2024-05-01-preview")


def whisper_model_name() -> str:
    return _env("WHISPER_MODEL", "base")


def asr_provider(lang: str | None = None) -> str:
    """
    Default: local Whisper (works in Hong Kong without OpenAI).
    Optional cloud: openai / zhipu when keys exist.
    HKBU GenAI is chat-only and is not used for ASR.
    """
    bucket = lang_bucket(lang)
    legacy = _env("ASR_PROVIDER").lower()
    default = "local"
    per_lang = {
        "yue": _env("ASR_PROVIDER_YUE", legacy or default).lower(),
        "cmn": _env("ASR_PROVIDER_CMN", legacy or default).lower(),
        "en": _env("ASR_PROVIDER_EN", legacy or default).lower(),
    }
    provider = per_lang[bucket]
    if provider not in {"local", "zhipu", "openai"}:
        provider = default

    if provider == "openai" and not openai_key():
        if zhipu_key():
            return "zhipu"
        return "local"
    if provider == "zhipu" and not zhipu_key():
        if openai_key():
            return "openai"
        return "local"
    return provider


def diagnosis_provider(lang: str | None = None) -> str:
    """
    Default for HK students:
      all UI languages → HKBU GenAI (Azure-shaped OpenAI models via school gateway)
    Falls back to zhipu / openai / deepseek / local if configured.
    """
    bucket = lang_bucket(lang)
    legacy = _env("DIAGNOSIS_PROVIDER").lower()
    default = "hkbu" if hkbu_key() else ("zhipu" if bucket == "cmn" else "openai")
    per_lang = {
        "yue": _env("DIAGNOSIS_PROVIDER_YUE", legacy or default).lower(),
        "cmn": _env("DIAGNOSIS_PROVIDER_CMN", legacy or default).lower(),
        "en": _env("DIAGNOSIS_PROVIDER_EN", legacy or default).lower(),
    }
    provider = per_lang[bucket]
    if provider not in {"hkbu", "zhipu", "openai", "deepseek", "local"}:
        provider = default

    if provider == "hkbu" and not hkbu_key():
        if zhipu_key():
            return "zhipu"
        if openai_key():
            return "openai"
        if deepseek_key():
            return "deepseek"
        return "local"
    if provider == "openai" and not openai_key():
        if hkbu_key():
            return "hkbu"
        if zhipu_key():
            return "zhipu"
        if deepseek_key():
            return "deepseek"
        return "local"
    if provider == "zhipu" and not zhipu_key():
        if hkbu_key():
            return "hkbu"
        if openai_key():
            return "openai"
        if deepseek_key():
            return "deepseek"
        return "local"
    if provider == "deepseek" and not deepseek_key():
        if hkbu_key():
            return "hkbu"
        if zhipu_key():
            return "zhipu"
        if openai_key():
            return "openai"
        return "local"
    return provider
