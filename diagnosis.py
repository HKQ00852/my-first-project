from __future__ import annotations

import json
import re
import sqlite3
import time
from pathlib import Path

import requests

import config

DB_PATH = Path(__file__).resolve().parent / "diagnosis.db"

def diagnose_prompt(media_kind: str = "script") -> str:
    """Build the diagnosis prompt. Audio/script must not judge camera shots."""
    kind = media_kind if media_kind in {"video", "audio", "script"} else "script"
    if kind == "video":
        extra = """【输入类型】带画面的短视频（已转写成口播文字）。
可以评价镜头、出镜、画面节奏；建议须能从文案合理推断，不要虚构没出现的画面细节。

【开头钩子】
- 前 3 秒口播／画面是否有悬念、提问、冲突，还是直接报产品？

【内容同质化】
- 是否只是产品展示+价格，缺少人物、场景故事、人设？
- 同质化分数「高」表示同质化严重（更需要改进）。

【行动号召 CTA】
- 结尾是否有明确引导（评论/关注/到店/点击链接）？

【完播驱动力】
- 中段口播信息密度如何；可结合「镜头切换／画面节奏」给建议。
"""
    else:
        source = "录音转写的口播" if kind == "audio" else "用户粘贴的脚本文案"
        extra = f"""【输入类型】{source}。没有画面、没有镜头。
【严禁】建议里不得出现：镜头、出镜、画面、分镜、运镜、切镜、特写、空镜、景别。
完播维度只评口播节奏、停顿、信息点、语气变化，不要叫用户改镜头。

【开头钩子】
- 前几句口播是否有提问、悬念、反差，还是直接报产品名／价格？

【内容同质化】
- 是否只有卖点堆砌+报价，缺少人物故事、场景描述、老板人设？
- 同质化分数「高」表示同质化严重（更需要改进）。

【行动号召 CTA】
- 结尾是否有明确引导（评论/关注/到店/点击链接）？

【完播驱动力】
- 中段口播是否太平、信息是否过密或过疏、有没有节奏停顿或小反转？只评声音／文案，不评画面。
"""

    return f"""你是一个短视频带货内容诊断专家，只根据给定文字做分析。

{extra}
【重要】你必须且只能输出以下JSON格式，不要加任何其他文字、解释或markdown标记：
{{
  "hook": {{"score": "高/中/低", "advice": "建议"}},
  "homogeneity": {{"score": "高/中/低", "advice": "建议"}},
  "cta": {{"has_cta": true/false, "advice": "建议"}},
  "retention": {{"score": "高/中/低", "advice": "建议"}},
  "priority": "最优先改这一点"
}}

待诊断文本：
"""


_VISUAL_TERMS = (
    "镜头切换",
    "鏡頭切換",
    "镜头",
    "鏡頭",
    "出镜",
    "出鏡",
    "画面",
    "畫面",
    "分镜",
    "分鏡",
    "运镜",
    "運鏡",
    "切镜",
    "切鏡",
    "特写",
    "特寫",
    "空镜",
    "空鏡",
    "景别",
    "景別",
)


def scrub_visual_advice(data: dict, media_kind: str) -> dict:
    """Strip camera/shot language when input is audio or pasted script."""
    if media_kind == "video":
        return data

    replacements = (
        ("镜头切换", "语气节奏变化"),
        ("鏡頭切換", "語氣節奏變化"),
        ("反差画面", "反差口播"),
        ("反差畫面", "反差口播"),
        ("反常识画面", "反差口播"),
        ("反常識畫面", "反差口播"),
        ("人物出镜", "人物故事"),
        ("人物出鏡", "人物故事"),
        ("出镜", "人物故事"),
        ("出鏡", "人物故事"),
        ("镜头", "节奏"),
        ("鏡頭", "節奏"),
        ("画面", "描述"),
        ("畫面", "描述"),
        ("分镜", "文案结构"),
        ("分鏡", "文案結構"),
    )

    def scrub(text: str) -> str:
        out = text or ""
        for old, new in replacements:
            out = out.replace(old, new)
        for term in _VISUAL_TERMS:
            out = out.replace(term, "")
        return out

    for key in ("hook", "homogeneity", "retention"):
        if isinstance(data.get(key), dict) and "advice" in data[key]:
            data[key]["advice"] = scrub(str(data[key]["advice"]))
    if isinstance(data.get("cta"), dict) and "advice" in data["cta"]:
        data["cta"]["advice"] = scrub(str(data["cta"]["advice"]))
    if "priority" in data:
        data["priority"] = scrub(str(data["priority"]))
    return data


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_name TEXT NOT NULL,
            industry TEXT NOT NULL,
            district TEXT,
            script TEXT NOT NULL,
            filename TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS diagnoses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            hook_score TEXT,
            hook_advice TEXT,
            homogeneity_score TEXT,
            homogeneity_advice TEXT,
            has_cta INTEGER,
            cta_advice TEXT,
            retention_score TEXT,
            retention_advice TEXT,
            priority TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos(id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS benchmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            industry TEXT NOT NULL,
            total_videos INTEGER,
            avg_hook_score REAL,
            avg_homogeneity_score REAL,
            avg_retention_score REAL,
            cta_rate REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def extract_json(raw_output: str | None) -> dict | None:
    if not raw_output:
        return None

    match = re.search(r"```json\s*(.*?)\s*```", raw_output, re.DOTALL)
    if match:
        raw_output = match.group(1)
    else:
        raw_output = raw_output.strip()
        # Fallback: take the outermost JSON object if present
        brace = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if brace:
            raw_output = brace.group(0)

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        return None


def diagnose_with_hkbu(script: str, prompt: str) -> str:
    api_key = config.hkbu_key()
    if not api_key:
        raise RuntimeError("缺少環境變數 HKBU_API_KEY（浸會 GenAI）")

    deployment = config.hkbu_deployment()
    version = config.hkbu_api_version()
    url = (
        f"{config.hkbu_base_url().rstrip('/')}/deployments/{deployment}"
        f"/chat/completions?api-version={version}"
    )
    last_error: Exception | None = None
    for attempt in range(3):
        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "api-key": api_key,
            },
            json={
                "messages": [{"role": "user", "content": prompt + script}],
                "temperature": 0.3,
                "max_tokens": 1200,
            },
            timeout=120,
        )
        if response.status_code >= 400:
            last_error = RuntimeError(
                f"HKBU GenAI 失敗（{response.status_code}）：{response.text[:300]}"
            )
            time.sleep(0.7 * (attempt + 1))
            continue
        payload = response.json()
        try:
            return payload["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            last_error = RuntimeError("HKBU GenAI 返回格式異常")
            last_error.__cause__ = exc
            time.sleep(0.7 * (attempt + 1))
            continue
    raise last_error or RuntimeError("HKBU GenAI 失敗")


def diagnose_with_zhipu(script: str, prompt: str) -> str:
    api_key = config.zhipu_key()
    if not api_key:
        raise RuntimeError("缺少環境變數 ZHIPUAI_API_KEY")

    from zhipuai import ZhipuAI

    client = ZhipuAI(api_key=api_key)
    response = client.chat.completions.create(
        model=config.zhipu_chat_model(),
        messages=[{"role": "user", "content": prompt + script}],
    )
    return response.choices[0].message.content or ""


def diagnose_with_openai_compatible(
    script: str,
    *,
    prompt: str,
    api_key: str,
    base_url: str,
    model: str,
) -> str:
    if not api_key:
        raise RuntimeError("缺少診斷 API Key")

    response = requests.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "temperature": 0.3,
            "messages": [{"role": "user", "content": prompt + script}],
        },
        timeout=120,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"診斷 API 失敗（{response.status_code}）：{response.text[:300]}")
    payload = response.json()
    try:
        return payload["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("診斷 API 返回格式異常") from exc


def local_fallback_diagnose(script: str, media_kind: str = "script") -> dict:
    """Rule-based fallback when API key is unavailable."""
    text = script.strip()
    length = len(text)
    questions = "？" in text or "?" in text
    cta_words = ("评论", "評論", "关注", "關注", "到店", "点击", "點擊", "链接", "連結", "私信", "下单", "下單")
    story_words = ("我", "今天", "故事", "老板", "老闆", "顾客", "顧客", "场景", "場景")
    has_cta = any(w in text for w in cta_words)
    has_story = any(w in text for w in story_words)

    hook_score = "高" if questions or text.startswith(("别", "別", "你", "谁", "誰", "为什么", "為什麼")) else ("中" if length > 40 else "低")
    homogeneity_score = "低" if has_story else ("中" if length > 80 else "高")
    retention_score = "高" if length > 120 else ("中" if length > 60 else "低")

    visual = media_kind == "video"
    hook_advice = (
        ("前三秒加入提问或反差画面，避免直接报产品名。" if visual else "开头用提问或反差口播，避免直接报产品名。")
        if hook_score != "高"
        else "开头已有钩子，可再压缩到更明确的一句悬念。"
    )
    homo_advice = (
        ("加入人物出镜与到店场景，减少纯卖点罗列。" if visual else "加入人物故事或到店经历，减少纯卖点罗列。")
        if homogeneity_score == "高"
        else "已有一定场景感，可强化老板人设或顾客互动。"
    )
    retention_advice = (
        ("中段增加镜头切换或信息节点，避免平铺直叙。" if visual else "中段加一个信息节点或语气停顿，避免平铺直叙。")
        if retention_score != "高"
        else ("节奏信息不错，可在中段再设一个小反转。" if visual else "口播节奏不错，可在中段再设一个小反转。")
    )

    return {
        "hook": {"score": hook_score, "advice": hook_advice},
        "homogeneity": {"score": homogeneity_score, "advice": homo_advice},
        "cta": {
            "has_cta": has_cta,
            "advice": "结尾补一句明确行动号召，例如评论关键词或到店引导。"
            if not has_cta
            else "已有行动号召，可让CTA更具体（时间/优惠/动作）。",
        },
        "retention": {"score": retention_score, "advice": retention_advice},
        "priority": "先改开头钩子"
        if hook_score == "低"
        else ("先补行动号召" if not has_cta else "先降同质化、补场景故事"),
        "source": "local",
    }


def _diagnose_raw(provider: str, script: str, prompt: str) -> str:
    if provider == "hkbu":
        return diagnose_with_hkbu(script, prompt)
    if provider == "zhipu":
        return diagnose_with_zhipu(script, prompt)
    if provider == "openai":
        return diagnose_with_openai_compatible(
            script,
            prompt=prompt,
            api_key=config.openai_key(),
            base_url="https://api.openai.com/v1",
            model=config.openai_chat_model(),
        )
    if provider == "deepseek":
        return diagnose_with_openai_compatible(
            script,
            prompt=prompt,
            api_key=config.deepseek_key(),
            base_url="https://api.deepseek.com/v1",
            model=config.deepseek_chat_model(),
        )
    raise RuntimeError(f"未知診斷供應商：{provider}")


def diagnose(script: str, lang: str | None = None, media_kind: str = "script") -> dict:
    preferred = config.diagnosis_provider(lang)
    prompt = diagnose_prompt(media_kind)
    chain: list[str] = []
    for name in (preferred, "hkbu", "zhipu", "local"):
        if name and name not in chain:
            chain.append(name)

    for provider in chain:
        if provider == "local":
            return scrub_visual_advice(local_fallback_diagnose(script, media_kind), media_kind)
        if provider == "hkbu" and not config.hkbu_key():
            continue
        if provider == "zhipu" and not config.zhipu_key():
            continue
        if provider == "openai" and not config.openai_key():
            continue
        if provider == "deepseek" and not config.deepseek_key():
            continue
        try:
            raw = _diagnose_raw(provider, script, prompt)
            data = extract_json(raw)
            if data is None:
                continue
            data["source"] = provider
            return scrub_visual_advice(data, media_kind)
        except Exception:  # noqa: BLE001 - try next provider so the demo still returns
            continue

    return scrub_visual_advice(local_fallback_diagnose(script, media_kind), media_kind)


def insert_video(
    shop_name: str,
    industry: str,
    district: str | None,
    script: str,
    filename: str | None = None,
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO videos (shop_name, industry, district, script, filename)
        VALUES (?, ?, ?, ?, ?)
        """,
        (shop_name, industry, district or "", script, filename or ""),
    )
    video_id = int(cursor.lastrowid)
    conn.commit()
    conn.close()
    return video_id


def save_diagnosis(video_id: int, data: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO diagnoses (
            video_id, hook_score, hook_advice,
            homogeneity_score, homogeneity_advice,
            has_cta, cta_advice,
            retention_score, retention_advice,
            priority
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            video_id,
            data["hook"]["score"],
            data["hook"]["advice"],
            data["homogeneity"]["score"],
            data["homogeneity"]["advice"],
            1 if data["cta"]["has_cta"] else 0,
            data["cta"]["advice"],
            data["retention"]["score"],
            data["retention"]["advice"],
            data["priority"],
        ),
    )
    diagnosis_id = int(cursor.lastrowid)
    conn.commit()
    conn.close()
    return diagnosis_id


def diagnose_and_save(
    shop_name: str,
    industry: str,
    district: str | None,
    script: str,
    filename: str | None = None,
    lang: str | None = None,
    media_kind: str = "script",
) -> dict:
    data = diagnose(script, lang=lang, media_kind=media_kind)
    video_id = insert_video(shop_name, industry, district, script, filename=filename)
    diagnosis_id = save_diagnosis(video_id, data)
    return {
        "video_id": video_id,
        "diagnosis_id": diagnosis_id,
        "shop_name": shop_name,
        "industry": industry,
        "district": district or "",
        "script": script,
        "filename": filename or "",
        "hook": data["hook"],
        "homogeneity": data["homogeneity"],
        "cta": data["cta"],
        "retention": data["retention"],
        "priority": data["priority"],
        "source": data.get("source", "unknown"),
    }
