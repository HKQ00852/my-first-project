from __future__ import annotations

from flask import request

SUPPORTED = ("zh-Hant", "zh-Hans", "en")
DEFAULT_LANG = "zh-Hant"
COOKIE_NAME = "caixun_lang"

MESSAGES: dict[str, dict[str, str]] = {
    "zh-Hant": {
        "meta.description": "採訊 — 短視頻帶貨腳本診斷：開頭鉤子、同質化、CTA、完播驅動力。",
        "meta.title": "採訊 CoiSeon — 短視頻腳本診斷",
        "brand.name": "採訊",
        "brand.logo_alt": "採訊標誌",
        "nav.how": "流程",
        "nav.fields": "適用場景",
        "nav.start": "開始分析",
        "lang.label": "語言",
        "lang.zh-Hant": "繁",
        "lang.zh-Hans": "简",
        "lang.en": "EN",
        "hero.h1": "上傳短視頻或貼腳本，直接完成診斷。",
        "hero.lede": "支援上傳帶貨短視頻自動轉寫口播，再從開頭鉤子、同質化、行動號召與完播驅動力四個面向給出建議。",
        "hero.cta_primary": "開始檢測視頻",
        "hero.cta_secondary": "看診斷流程",
        "how.kicker": "診斷流程",
        "how.h2": "三步，把腳本變成可執行診斷。",
        "how.lede": "不用逐句人工批註。填入商家資訊與腳本後，系統會輸出四維評分與優先改進點。",
        "how.step1.title": "上傳視頻或貼腳本",
        "how.step1.body": "上傳你有權使用的短視頻檔案，或直接貼入口播／分鏡文案。",
        "how.step2.title": "轉寫與四維診斷",
        "how.step2.body": "視頻會先轉成口播文字，再評估鉤子、同質化、CTA、完播驅動力。",
        "how.step3.title": "輸出優先改進",
        "how.step3.body": "每個維度給出高／中／低評分與建議，並標出最該先改的一點。",
        "fields.kicker": "適用場景",
        "fields.h2": "為小商家帶貨短視頻而設計。",
        "fields.lede": "適合門店老闆、代運營與內容審校——先看腳本問題，再決定怎麼改下一支。",
        "fields.item1.title": "門店自查",
        "fields.item1.body": "快速檢查自己的口播是否太平、有沒有 CTA、開頭夠不夠抓人。",
        "fields.item2.title": "代運營批改",
        "fields.item2.body": "批量對照不同商家腳本，統一診斷維度與改進優先級。",
        "fields.item3.title": "行業對標",
        "fields.item3.body": "依行業保存診斷結果，後續可做同業基準比較。",
        "fields.item4.title": "內容審校",
        "fields.item4.body": "上線前檢查同質化與完播節奏，降低「只有報價」的片子比例。",
        "start.h2": "開始檢測短視頻",
        "start.lede": "上傳短視頻（自動轉寫口播），或貼上腳本；兩者擇一即可。",
        "form.shop": "店名",
        "form.shop_ph": "例如：李老闆麵館",
        "form.industry": "行業",
        "form.industry_ph": "例如：餐飲",
        "form.district": "區域（選填）",
        "form.district_ph": "例如：旺角",
        "form.video": "上傳短視頻／音訊（選填）",
        "form.script": "或直接貼腳本（選填）",
        "form.script_ph": "若不上傳視頻，可在此貼口播文案或分鏡腳本……",
        "form.submit": "開始診斷",
        "form.submitting": "診斷中…",
        "form.submitting_video": "轉寫並診斷中…",
        "form.fineprint": "直接檢測視頻需設定 ZHIPUAI_API_KEY（語音轉文字）。僅貼腳本時，無金鑰也可用本地規則診斷。請只上傳你有權使用的內容。",
        "result.priority": "優先改進",
        "result.file": "檔案",
        "result.source": "診斷來源：",
        "result.source_zhipu": "智譜 AI",
        "result.source_local": "本地規則",
        "result.video_id": "影片 ID",
        "result.dims": "四維診斷",
        "result.hook": "開頭鉤子",
        "result.homogeneity": "內容同質化",
        "result.cta": "行動號召 CTA",
        "result.retention": "完播驅動力",
        "result.cta_yes": "有",
        "result.cta_no": "無",
        "result.transcript": "轉寫／腳本文案",
        "score.high": "高",
        "score.mid": "中",
        "score.low": "低",
        "footer.tagline": "短視頻腳本診斷 · Python / Flask",
        "flash.need_shop": "請填寫店名與行業。",
        "flash.need_input": "請上傳短視頻，或貼上腳本文案（二選一即可）。",
        "flash.script_short": "腳本內容過短，請貼上更完整的口播／分鏡文案。",
        "flash.fail_prefix": "診斷失敗：",
        "flash.ok_video": "已從「{name}」轉寫口播並完成診斷。",
        "flash.ok_local": "已完成本地規則診斷（未偵測到 ZHIPUAI_API_KEY，未呼叫智譜 API）。",
        "flash.ok_ai": "已完成 AI 診斷，結果已寫入資料庫。",
    },
    "zh-Hans": {
        "meta.description": "采讯 — 短视频带货脚本诊断：开头钩子、同质化、CTA、完播驱动力。",
        "meta.title": "采讯 CoiSeon — 短视频脚本诊断",
        "brand.name": "采讯",
        "brand.logo_alt": "采讯标志",
        "nav.how": "流程",
        "nav.fields": "适用场景",
        "nav.start": "开始分析",
        "lang.label": "语言",
        "lang.zh-Hant": "繁",
        "lang.zh-Hans": "简",
        "lang.en": "EN",
        "hero.h1": "上传短视频或贴脚本，直接完成诊断。",
        "hero.lede": "支持上传带货短视频自动转写口播，再从开头钩子、同质化、行动号召与完播驱动力四个面向给出建议。",
        "hero.cta_primary": "开始检测视频",
        "hero.cta_secondary": "看诊断流程",
        "how.kicker": "诊断流程",
        "how.h2": "三步，把脚本变成可执行诊断。",
        "how.lede": "不用逐句人工批注。填入商家信息与脚本后，系统会输出四维评分与优先改进点。",
        "how.step1.title": "上传视频或贴脚本",
        "how.step1.body": "上传你有权使用的短视频文件，或直接贴入口播／分镜文案。",
        "how.step2.title": "转写与四维诊断",
        "how.step2.body": "视频会先转成口播文字，再评估钩子、同质化、CTA、完播驱动力。",
        "how.step3.title": "输出优先改进",
        "how.step3.body": "每个维度给出高／中／低评分与建议，并标出最该先改的一点。",
        "fields.kicker": "适用场景",
        "fields.h2": "为小商家带货短视频而设计。",
        "fields.lede": "适合门店老板、代运营与内容审校——先看脚本问题，再决定怎么改下一支。",
        "fields.item1.title": "门店自查",
        "fields.item1.body": "快速检查自己的口播是否太平、有没有 CTA、开头够不够抓人。",
        "fields.item2.title": "代运营批改",
        "fields.item2.body": "批量对照不同商家脚本，统一诊断维度与改进优先级。",
        "fields.item3.title": "行业对标",
        "fields.item3.body": "按行业保存诊断结果，后续可做同业基准比较。",
        "fields.item4.title": "内容审校",
        "fields.item4.body": "上线前检查同质化与完播节奏，降低「只有报价」的片子比例。",
        "start.h2": "开始检测短视频",
        "start.lede": "上传短视频（自动转写口播），或贴上脚本；两者择一即可。",
        "form.shop": "店名",
        "form.shop_ph": "例如：李老板面馆",
        "form.industry": "行业",
        "form.industry_ph": "例如：餐饮",
        "form.district": "区域（选填）",
        "form.district_ph": "例如：旺角",
        "form.video": "上传短视频／音频（选填）",
        "form.script": "或直接贴脚本（选填）",
        "form.script_ph": "若不上传视频，可在此贴口播文案或分镜脚本……",
        "form.submit": "开始诊断",
        "form.submitting": "诊断中…",
        "form.submitting_video": "转写并诊断中…",
        "form.fineprint": "直接检测视频需设定 ZHIPUAI_API_KEY（语音转文字）。仅贴脚本时，无密钥也可用本地规则诊断。请只上传你有权使用的内容。",
        "result.priority": "优先改进",
        "result.file": "文件",
        "result.source": "诊断来源：",
        "result.source_zhipu": "智谱 AI",
        "result.source_local": "本地规则",
        "result.video_id": "影片 ID",
        "result.dims": "四维诊断",
        "result.hook": "开头钩子",
        "result.homogeneity": "内容同质化",
        "result.cta": "行动号召 CTA",
        "result.retention": "完播驱动力",
        "result.cta_yes": "有",
        "result.cta_no": "无",
        "result.transcript": "转写／脚本文案",
        "score.high": "高",
        "score.mid": "中",
        "score.low": "低",
        "footer.tagline": "短视频脚本诊断 · Python / Flask",
        "flash.need_shop": "请填写店名与行业。",
        "flash.need_input": "请上传短视频，或贴上脚本文案（二选一即可）。",
        "flash.script_short": "脚本内容过短，请贴上更完整的口播／分镜文案。",
        "flash.fail_prefix": "诊断失败：",
        "flash.ok_video": "已从「{name}」转写口播并完成诊断。",
        "flash.ok_local": "已完成本地规则诊断（未检测到 ZHIPUAI_API_KEY，未调用智谱 API）。",
        "flash.ok_ai": "已完成 AI 诊断，结果已写入数据库。",
    },
    "en": {
        "meta.description": "CoiSeon — short-video sales script diagnosis: hook, sameness, CTA, and retention.",
        "meta.title": "CoiSeon — Short-video script diagnosis",
        "brand.name": "採訊",
        "brand.logo_alt": "CoiSeon logo",
        "nav.how": "How it works",
        "nav.fields": "Use cases",
        "nav.start": "Start",
        "lang.label": "Language",
        "lang.zh-Hant": "繁",
        "lang.zh-Hans": "简",
        "lang.en": "EN",
        "hero.h1": "Upload a short video or paste a script for instant diagnosis.",
        "hero.lede": "Upload a sales short video for auto transcription, then get advice on hook, sameness, CTA, and retention.",
        "hero.cta_primary": "Diagnose a video",
        "hero.cta_secondary": "See the flow",
        "how.kicker": "Flow",
        "how.h2": "Three steps from script to actionable diagnosis.",
        "how.lede": "No line-by-line manual markup. Enter shop details and a script to get four scores and a top priority fix.",
        "how.step1.title": "Upload video or paste script",
        "how.step1.body": "Upload a short video you have rights to use, or paste spoken / storyboard copy.",
        "how.step2.title": "Transcribe and score",
        "how.step2.body": "Video is transcribed first, then scored on hook, sameness, CTA, and retention.",
        "how.step3.title": "Get the priority fix",
        "how.step3.body": "Each dimension gets a high / mid / low score with advice, plus what to fix first.",
        "fields.kicker": "Use cases",
        "fields.h2": "Built for small-business sales shorts.",
        "fields.lede": "For shop owners, agencies, and content reviewers — spot script issues before the next shoot.",
        "fields.item1.title": "Shop self-check",
        "fields.item1.body": "Quickly check if delivery is flat, whether there is a CTA, and if the opening hooks viewers.",
        "fields.item2.title": "Agency review",
        "fields.item2.body": "Compare scripts across clients with the same diagnosis dimensions and priorities.",
        "fields.item3.title": "Industry benchmarks",
        "fields.item3.body": "Save diagnoses by industry for later peer benchmarking.",
        "fields.item4.title": "Content QA",
        "fields.item4.body": "Check sameness and pacing before publish to cut price-only clips.",
        "start.h2": "Start diagnosing",
        "start.lede": "Upload a short video (auto-transcribe), or paste a script — either works.",
        "form.shop": "Shop name",
        "form.shop_ph": "e.g. Lee’s Noodle House",
        "form.industry": "Industry",
        "form.industry_ph": "e.g. Food & beverage",
        "form.district": "District (optional)",
        "form.district_ph": "e.g. Mong Kok",
        "form.video": "Upload short video / audio (optional)",
        "form.script": "Or paste a script (optional)",
        "form.script_ph": "If you are not uploading a video, paste spoken or storyboard copy here…",
        "form.submit": "Run diagnosis",
        "form.submitting": "Diagnosing…",
        "form.submitting_video": "Transcribing & diagnosing…",
        "form.fineprint": "Video diagnosis needs ZHIPUAI_API_KEY (speech-to-text). Script-only works with local rules when no key is set. Upload only content you have rights to use.",
        "result.priority": "Priority fix",
        "result.file": "File",
        "result.source": "Source:",
        "result.source_zhipu": "Zhipu AI",
        "result.source_local": "Local rules",
        "result.video_id": "Video ID",
        "result.dims": "Four-dimension diagnosis",
        "result.hook": "Opening hook",
        "result.homogeneity": "Sameness",
        "result.cta": "Call to action",
        "result.retention": "Retention drive",
        "result.cta_yes": "Yes",
        "result.cta_no": "No",
        "result.transcript": "Transcript / script",
        "score.high": "High",
        "score.mid": "Mid",
        "score.low": "Low",
        "footer.tagline": "Short-video script diagnosis · Python / Flask",
        "flash.need_shop": "Please enter shop name and industry.",
        "flash.need_input": "Upload a short video or paste a script (either is fine).",
        "flash.script_short": "Script is too short. Paste a fuller spoken or storyboard draft.",
        "flash.fail_prefix": "Diagnosis failed: ",
        "flash.ok_video": "Transcribed “{name}” and finished diagnosis.",
        "flash.ok_local": "Local-rule diagnosis done (no ZHIPUAI_API_KEY; Zhipu API not called).",
        "flash.ok_ai": "AI diagnosis complete; result saved to the database.",
    },
}


def normalize_lang(value: str | None) -> str:
    if not value:
        return DEFAULT_LANG
    raw = value.strip()
    aliases = {
        "zh": "zh-Hant",
        "zh-TW": "zh-Hant",
        "zh-HK": "zh-Hant",
        "zh-MO": "zh-Hant",
        "zh-CN": "zh-Hans",
        "zh-SG": "zh-Hans",
        "zh-hant": "zh-Hant",
        "zh-hans": "zh-Hans",
        "en-US": "en",
        "en-GB": "en",
    }
    if raw in SUPPORTED:
        return raw
    if raw in aliases:
        return aliases[raw]
    lower = raw.lower()
    for code in SUPPORTED:
        if lower == code.lower():
            return code
    return DEFAULT_LANG


def get_locale() -> str:
    form_lang = request.form.get("lang") if request.method == "POST" else None
    if form_lang:
        return normalize_lang(form_lang)
    cookie = request.cookies.get(COOKIE_NAME)
    if cookie:
        return normalize_lang(cookie)
    # Prefer Traditional Chinese for HK/TW browsers; else Accept-Language.
    header = request.accept_languages.best_match(
        ["zh-Hant", "zh-TW", "zh-HK", "zh-Hans", "zh-CN", "en"]
    )
    return normalize_lang(header)


def t(key: str, lang: str | None = None, **kwargs: str) -> str:
    code = normalize_lang(lang or get_locale())
    text = MESSAGES.get(code, MESSAGES[DEFAULT_LANG]).get(key)
    if text is None:
        text = MESSAGES[DEFAULT_LANG].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def score_label(raw: str, lang: str | None = None) -> str:
    mapping = {
        "高": "score.high",
        "中": "score.mid",
        "低": "score.low",
        "High": "score.high",
        "Mid": "score.mid",
        "Low": "score.low",
    }
    key = mapping.get((raw or "").strip())
    return t(key, lang) if key else raw
