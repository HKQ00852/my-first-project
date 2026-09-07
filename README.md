# 採訊 CoiSeon — 短视频带货脚本诊断

Flask 网页 Demo：上传短视频或粘贴脚本，自动转写后按钩子、同质化、转化引导、留存进行诊断。

## 功能

- **诊断 API（香港可用）**：走 **HKBU GenAI** 闸道（`gpt-4.1-mini`），粤／EN／简都可用
- **粘贴脚本诊断**：有 HKBU Key 用 GenAI；否则本地规则
- **上传视频**：需要额外的 Whisper／智谱 ASR Key（HKBU 闸道目前是对话接口，不做语音转写）
- **多语言 UI**：粵 / EN / 简

## 为什么不用官方 OpenAI？

香港经常无法直连 `api.openai.com`。浸会 GenAI（`genai.hkbu.edu.hk`）用学校 Key，以 Azure 风格接口转发 GPT 等模型，适合本项目。

## 运行

```bash
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env：
#   HKBU_API_KEY=你的浸会 GenAI Key
python3 app.py
```

打开 http://127.0.0.1:5000

系统依赖：视频上传需 **ffmpeg**。

## 安全提醒

请勿把 API Key 写进代码或提交 `.env`。Key 若曾出现在聊天中，请尽快在学校平台轮换。

## 说明

本 Demo 不抓取抖音/TikTok；仅处理用户主动上传或粘贴的内容。
