# 採訊 CaiXun

對**網絡短視頻**進行**關鍵詞提取**與**內容評價**的示範網站（Python / Flask）。

## 啟動

```bash
pip install -r requirements.txt
python3 app.py
```

瀏覽器開啟 http://127.0.0.1:5000

## 功能

1. 貼上公開短視頻連結
2. 示範提取主題關鍵詞與權重
3. 輸出綜合評價分數與簡要建議

> 目前為本地演示分析，不會真正下載或抓取平台內容。

## 結構

| 路徑 | 說明 |
|------|------|
| `app.py` | Flask 路由與示範分析邏輯 |
| `templates/index.html` | 落地頁與結果樣板 |
| `static/css/style.css` | 視覺與動效 |
| `static/js/main.js` | 區塊進場動畫 |
