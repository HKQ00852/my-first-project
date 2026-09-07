# 採訊 CoiSeon — 短视频带货脚本诊断

Flask 网页 Demo：上传短视频或粘贴脚本，自动转写后按钩子、同质化、转化引导、留存进行诊断，并给出优先改进建议。

## 功能

- **上传视频诊断**：抽音轨 → 按语系选 ASR → 诊断
- **粘贴脚本诊断**：无 Key 时走本地规则兜底
- **语系分流 API**：
  - **粵語 / English** → OpenAI（Whisper + GPT）
  - **简体普通话** → 智谱（ASR + GLM）
- **多语言 UI**：粵 / EN / 简
- 诊断结果写入 SQLite（`diagnosis.db`）

## 运行

```bash
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入：
#   OPENAI_API_KEY=...     # 粵語 + 英文
#   ZHIPUAI_API_KEY=...    # 简体
python3 app.py
```

打开 http://127.0.0.1:5000

系统依赖：需安装 **ffmpeg**（用于从视频抽音频）。

## 安全提醒

请勿把 API Key 写进代码或提交 `.env`。若密钥曾出现在对话中，请尽快轮换。

## 说明

本 Demo 不抓取抖音/TikTok 等平台内容；仅处理用户主动上传的视频或粘贴的脚本。
