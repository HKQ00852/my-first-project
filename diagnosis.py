from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import requests

import config

DB_PATH = Path(__file__).resolve().parent / "diagnosis.db"

DIAGNOSE_PROMPT = """你是一个短视频诊断专家，专门帮小商家分析带货视频脚本的问题。

请按以下 4 个维度分析这段脚本，每个维度给出「高/中/低」评分和一句具体建议。

【开头钩子】
- 前 3 秒是否有悬念？反常识画面？提问？冲突？还是直接介绍产品？

【内容同质化】
- 是否只是产品展示+价格，缺少人物出镜、场景故事、人设？
- 注意：同质化分数「高」表示同质化严重（更需要改进）。

【行动号召 CTA】
- 结尾是否有明确引导（评论/关注/到店/点击链接）？

【完播驱动力】
- 中段是否有节奏变化（音乐、镜头切换、信息密度）？

【重要】你必须且只能输出以下JSON格式，不要加任何其他文字、解释或markdown标记：
{
  "hook": {"score": "高/中/低", "advice": "建议"},
  "homogeneity": {"score": "高/中/低", "advice": "建议"},
  "cta": {"has_cta": true/false, "advice": "建议"},
  "retention": {"score": "高/中/低", "advice": "建议"},
  "priority": "最优先改这一点"
}

待诊断脚本：
"""


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


def diagnose_with_hkbu(script: str) -> str:
    api_key = config.hkbu_key()
    if not api_key:
        raise RuntimeError("缺少環境變數 HKBU_API_KEY（浸會 GenAI）")

    deployment = config.hkbu_deployment()
    version = config.hkbu_api_version()
    url = (
        f"{config.hkbu_base_url().rstrip('/')}/deployments/{deployment}"
        f"/chat/completions?api-version={version}"
    )
    response = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "api-key": api_key,
        },
        json={
            "messages": [{"role": "user", "content": DIAGNOSE_PROMPT + script}],
            "temperature": 0.3,
            "max_tokens": 1200,
        },
        timeout=120,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"HKBU GenAI 失敗（{response.status_code}）：{response.text[:300]}")
    payload = response.json()
    try:
        return payload["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("HKBU GenAI 返回格式異常") from exc


def diagnose_with_zhipu(script: str) -> str:
    api_key = config.zhipu_key()
    if not api_key:
        raise RuntimeError("缺少環境變數 ZHIPUAI_API_KEY")

    from zhipuai import ZhipuAI

    client = ZhipuAI(api_key=api_key)
    response = client.chat.completions.create(
        model=config.zhipu_chat_model(),
        messages=[{"role": "user", "content": DIAGNOSE_PROMPT + script}],
    )
    return response.choices[0].message.content or ""


def diagnose_with_openai_compatible(
    script: str,
    *,
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
            "messages": [{"role": "user", "content": DIAGNOSE_PROMPT + script}],
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


def local_fallback_diagnose(script: str) -> dict:
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

    return {
        "hook": {
            "score": hook_score,
            "advice": "前三秒加入提问或反差画面，避免直接报产品名。"
            if hook_score != "高"
            else "开头已有钩子，可再压缩到更明确的一句悬念。",
        },
        "homogeneity": {
            "score": homogeneity_score,
            "advice": "加入人物出镜与到店场景，减少纯卖点罗列。"
            if homogeneity_score == "高"
            else "已有一定场景感，可强化老板人设或顾客互动。",
        },
        "cta": {
            "has_cta": has_cta,
            "advice": "结尾补一句明确行动号召，例如评论关键词或到店引导。"
            if not has_cta
            else "已有行动号召，可让CTA更具体（时间/优惠/动作）。",
        },
        "retention": {
            "score": retention_score,
            "advice": "中段增加镜头切换或信息节点，避免平铺直叙。"
            if retention_score != "高"
            else "节奏信息不错，可在中段再设一个小反转。",
        },
        "priority": "先改开头钩子"
        if hook_score == "低"
        else ("先补行动号召" if not has_cta else "先降同质化、补场景故事"),
        "source": "local",
    }


def diagnose(script: str, lang: str | None = None) -> dict:
    provider = config.diagnosis_provider(lang)

    if provider == "local":
        return local_fallback_diagnose(script)

    if provider == "hkbu":
        raw = diagnose_with_hkbu(script)
        source = "hkbu"
    elif provider == "zhipu":
        raw = diagnose_with_zhipu(script)
        source = "zhipu"
    elif provider == "openai":
        raw = diagnose_with_openai_compatible(
            script,
            api_key=config.openai_key(),
            base_url="https://api.openai.com/v1",
            model=config.openai_chat_model(),
        )
        source = "openai"
    elif provider == "deepseek":
        raw = diagnose_with_openai_compatible(
            script,
            api_key=config.deepseek_key(),
            base_url="https://api.deepseek.com/v1",
            model=config.deepseek_chat_model(),
        )
        source = "deepseek"
    else:
        return local_fallback_diagnose(script)

    data = extract_json(raw)
    if data is None:
        raise ValueError("AI 診斷結果無法解析為 JSON")
    data["source"] = source
    return data


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
) -> dict:
    data = diagnose(script, lang=lang)
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
