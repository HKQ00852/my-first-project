# 採訊 CaiXun

短視頻**帶貨腳本診斷**網站（Python / Flask）。

診斷維度：開頭鉤子、內容同質化、行動號召 CTA、完播驅動力。

## 啟動

```bash
pip install -r requirements.txt
export ZHIPUAI_API_KEY="你的智譜金鑰"   # 選填；未設定則用本地規則診斷
python3 app.py
```

瀏覽器開啟 http://127.0.0.1:5000

## 結構

| 路徑 | 說明 |
|------|------|
| `app.py` | Flask 路由 |
| `diagnosis.py` | 建表、智譜診斷、本地 fallback、寫入 SQLite |
| `diagnosis.db` | 本地資料庫（執行後產生，不進版控） |
| `templates/index.html` | 落地頁與診斷表單 |
| `static/` | 樣式、腳本、logo |

## 安全

請把 `ZHIPUAI_API_KEY` 放在環境變數，不要寫進程式碼或提交到 Git。
若金鑰曾貼在聊天或截圖中，請到智譜後台盡快輪換。
