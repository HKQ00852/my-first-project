# 採訊 CaiXun

資訊擷取產品落地頁（Python / Flask）。

## 啟動

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

開啟 http://127.0.0.1:5000

## 結構

- `app.py` — Flask 路由與表單驗證
- `templates/index.html` — 落地頁
- `static/css/style.css` — 樣式與動效
- `static/js/main.js` — 捲動進場
