from __future__ import annotations

import hashlib
from urllib.parse import urlparse

from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "caixun-demo-dev-key"

KEYWORD_POOL = [
    ("口播節奏", "內容結構"),
    ("產品賣點", "商業轉化"),
    ("情緒鉤子", "開頭吸引力"),
    ("場景真實感", "畫面質感"),
    ("行動呼籲", "轉化設計"),
    ("話題熱度", "趨勢相關"),
    ("字幕清晰度", "可讀性"),
    ("品牌露出", "品牌識別"),
    ("評論互動", "社群訊號"),
    ("完播潛力", "留存表現"),
    ("痛點共鳴", "受眾貼合"),
    ("資訊密度", "表達效率"),
]

EVAL_NOTES = [
    "開頭前三秒有明確鉤子，關鍵詞集中，適合做系列化內容。",
    "賣點出現偏晚，建議把核心關鍵詞提前到前五秒。",
    "情緒與資訊平衡不錯，可再強化一次明確的行動呼籲。",
    "畫面與口播關鍵詞一致，評價穩定，適合品牌監測對照。",
    "話題相關性高，但字幕關鍵詞重複偏多，可精簡表達。",
]


def is_public_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value.strip())
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def demo_analyze(video_url: str) -> dict:
    """Deterministic demo result for a short-video URL."""
    digest = hashlib.sha256(video_url.encode("utf-8")).hexdigest()
    seed = int(digest[:8], 16)
    score = 62 + (seed % 35)  # 62–96
    start = seed % len(KEYWORD_POOL)
    keywords = []
    seen = set()
    offset = 0
    while len(keywords) < 5 and offset < len(KEYWORD_POOL):
        term, aspect = KEYWORD_POOL[(start + offset * 2) % len(KEYWORD_POOL)]
        offset += 1
        if term in seen:
            continue
        seen.add(term)
        weight = 92 - len(keywords) * 11 - (seed % 5)
        keywords.append(
            {
                "term": term,
                "aspect": aspect,
                "weight": max(48, weight),
            }
        )
    note = EVAL_NOTES[seed % len(EVAL_NOTES)]
    if score >= 85:
        grade = "優秀"
    elif score >= 72:
        grade = "良好"
    else:
        grade = "待優化"
    return {
        "url": video_url,
        "score": score,
        "grade": grade,
        "keywords": keywords,
        "note": note,
    }


@app.get("/")
def home():
    return render_template("index.html", result=None)


@app.post("/analyze")
def analyze():
    video_url = (request.form.get("url") or "").strip()
    if not is_public_http_url(video_url):
        flash("請輸入有效的短視頻公開連結（http 或 https）。", "error")
        return redirect(url_for("home") + "#start")

    result = demo_analyze(video_url)
    flash("已完成示範分析：關鍵詞提取與內容評價已生成。", "ok")
    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
