from __future__ import annotations

from urllib.parse import urlparse

from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "caixun-demo-dev-key"


def is_public_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value.strip())
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


@app.get("/")
def home():
    return render_template("index.html", analyzed_url=None)


@app.post("/analyze")
def analyze():
    source_url = (request.form.get("url") or "").strip()
    if not is_public_http_url(source_url):
        flash("請輸入有效的公開網頁網址（http 或 https）。", "error")
        return redirect(url_for("home") + "#start")

    flash("已收到來源網址。這是示範介面，尚未實際抓取。", "ok")
    return render_template("index.html", analyzed_url=source_url)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
