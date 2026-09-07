# 採訊 CoiSeon — 短视频带货脚本诊断

Flask 网页 Demo：上传短视频或粘贴脚本 → 转写 → 四维诊断。

## 功能

- **诊断**：HKBU GenAI（香港可用，粤／EN／简）
- **上传视频自动检测**：**智谱 ASR** 转写口播 → HKBU 诊断（不使用 Whisper）
- **粘贴脚本**：可跳过转写直接诊断
- **多语言 UI**：粵 / EN / 简

## 运行

```bash
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env：
#   HKBU_API_KEY=浸会 GenAI Key
#   ZHIPUAI_API_KEY=智谱 Key（视频转写）
python3 app.py
```

打开 http://127.0.0.1:5000 → 上传短视频或贴脚本 → 开始诊断。

系统依赖：视频上传需 **ffmpeg**。

## 安全提醒

请勿提交 `.env`。Key 若曾出现在聊天中，请尽快轮换。

## 说明

本 Demo 不抓取抖音/TikTok；仅处理用户上传/粘贴内容。
