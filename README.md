# 採訊 CoiSeon — 短视频带货脚本诊断

Flask 网页 Demo：上传短视频或粘贴脚本 → 转写（可选）→ 四维诊断。

## 功能

- **诊断**：HKBU GenAI（香港可用，粤／EN／简）
- **上传视频自动检测**：本机 **Whisper** 转写口播 → 再交给 HKBU 诊断（无需官方 OpenAI）
- **粘贴脚本**：可跳过转写直接诊断
- **多语言 UI**：粵 / EN / 简

## 运行

```bash
pip install -r requirements.txt
# 系统需 ffmpeg；首次运行会下载 Whisper 模型
cp .env.example .env
# 编辑 .env：HKBU_API_KEY=你的浸会 Key
python3 app.py
```

打开 http://127.0.0.1:5000 → 上传短视频或贴脚本 → 开始诊断。

## 说明

- 香港常无法直连官方 OpenAI；诊断走学校 GenAI，转写默认本地 Whisper
- 请勿提交 `.env`；Key 若曾泄露请轮换
- 不抓取抖音/TikTok，仅处理用户上传/粘贴内容
