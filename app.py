from __future__ import annotations

import os

from flask import Flask, flash, redirect, render_template, request, url_for

from diagnosis import diagnose_and_save, init_db

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "caixun-demo-dev-key")

init_db()


@app.get("/")
def home():
    return render_template("index.html", result=None, form_data=None)


@app.post("/analyze")
def analyze():
    shop_name = (request.form.get("shop_name") or "").strip()
    industry = (request.form.get("industry") or "").strip()
    district = (request.form.get("district") or "").strip()
    script = (request.form.get("script") or "").strip()

    form_data = {
        "shop_name": shop_name,
        "industry": industry,
        "district": district,
        "script": script,
    }

    if not shop_name or not industry or not script:
        flash("請填寫店名、行業與腳本內容。", "error")
        return render_template("index.html", result=None, form_data=form_data), 400

    if len(script) < 10:
        flash("腳本內容過短，請貼上更完整的口播／分鏡文案。", "error")
        return render_template("index.html", result=None, form_data=form_data), 400

    try:
        result = diagnose_and_save(shop_name, industry, district, script)
    except Exception as exc:  # noqa: BLE001 - surface API/config errors to UI
        flash(f"診斷失敗：{exc}", "error")
        return render_template("index.html", result=None, form_data=form_data), 502

    if result.get("source") == "local":
        flash("已完成本地規則診斷（未偵測到 ZHIPUAI_API_KEY，未呼叫智譜 API）。", "ok")
    else:
        flash("已完成 AI 診斷，結果已寫入資料庫。", "ok")

    return render_template("index.html", result=result, form_data=form_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
