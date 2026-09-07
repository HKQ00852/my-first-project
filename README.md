# 採訊 CaiXun — 短视频带货脚本诊断

Flask 网页 Demo：上传短视频或粘贴脚本，自动转写后按钩子、同质化、转化引导、留存进行诊断，并给出优先改进建议。

## 功能

- **上传视频诊断**：上传用户自有短视频 → 抽取音轨 → 智谱 ASR 转写 → 诊断
- **粘贴脚本诊断**：直接粘贴脚本文本诊断（无 API Key 时走本地规则兜底）
- 诊断结果写入 SQLite（`diagnosis.db`）
- 首页含产品介绍与诊断表单

## 运行

```bash
pip install -r requirements.txt
# 视频转写与 AI 诊断需要智谱 API Key
export ZHIPUAI_API_KEY="你的密钥"
python3 app.py
```

打开 http://127.0.0.1:5000

系统依赖：需安装 **ffmpeg**（用于从视频抽音频）。macOS 可用 `brew install ffmpeg`。

## 安全提醒

请勿把 API Key 写进代码或 HTML。若密钥曾出现在对话或文件中，请尽快在智谱开放平台轮换。

## 说明

本 Demo 不抓取抖音/TikTok 等平台内容；仅处理用户主动上传的视频或粘贴的脚本。
