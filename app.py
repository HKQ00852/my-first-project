from __future__ import annotations

import os

from flask import Flask, flash, make_response, render_template, request

from diagnosis import diagnose_and_save, init_db
from i18n import COOKIE_NAME, MESSAGES, get_locale, score_label, t
from media import save_upload, transcribe_media

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "caixun-demo-dev-key")
app.config["MAX_CONTENT_LENGTH"] = 80 * 1024 * 1024

init_db()


@app.context_processor
def inject_i18n():
    lang = get_locale()
    return {
        "lang": lang,
        "t": lambda key, **kwargs: t(key, lang, **kwargs),
        "score_label": lambda raw: score_label(raw, lang),
        "i18n_messages": MESSAGES,
    }


def render_page(*, result=None, form_data=None, status=200):
    lang = get_locale()
    html = render_template(
        "index.html",
        result=result,
        form_data=form_data,
        lang=lang,
    )
    response = make_response(html, status)
    response.set_cookie(
        COOKIE_NAME,
        lang,
        max_age=60 * 60 * 24 * 365,
        samesite="Lax",
    )
    return response


@app.get("/")
def home():
    return render_page(result=None, form_data=None)


@app.post("/analyze")
def analyze():
    lang = get_locale()
    shop_name = (request.form.get("shop_name") or "").strip()
    industry = (request.form.get("industry") or "").strip()
    district = (request.form.get("district") or "").strip()
    script = (request.form.get("script") or "").strip()
    upload = request.files.get("video")
    uploaded_name = ""

    form_data = {
        "shop_name": shop_name,
        "industry": industry,
        "district": district,
        "script": script,
    }

    if not shop_name or not industry:
        flash(t("flash.need_shop", lang), "error")
        return render_page(result=None, form_data=form_data, status=400)

    try:
        if upload and upload.filename:
            path = save_upload(upload)
            uploaded_name = upload.filename
            script = transcribe_media(path)
            form_data["script"] = script
        elif not script:
            flash(t("flash.need_input", lang), "error")
            return render_page(result=None, form_data=form_data, status=400)
        elif len(script) < 10:
            flash(t("flash.script_short", lang), "error")
            return render_page(result=None, form_data=form_data, status=400)

        result = diagnose_and_save(
            shop_name,
            industry,
            district,
            script,
            filename=uploaded_name or None,
        )
    except Exception as exc:  # noqa: BLE001 - surface processing errors to UI
        flash(f"{t('flash.fail_prefix', lang)}{exc}", "error")
        return render_page(result=None, form_data=form_data, status=502)

    if uploaded_name:
        flash(t("flash.ok_video", lang, name=uploaded_name), "ok")
    elif result.get("source") == "local":
        flash(t("flash.ok_local", lang), "ok")
    else:
        flash(t("flash.ok_ai", lang), "ok")

    return render_page(result=result, form_data=form_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
