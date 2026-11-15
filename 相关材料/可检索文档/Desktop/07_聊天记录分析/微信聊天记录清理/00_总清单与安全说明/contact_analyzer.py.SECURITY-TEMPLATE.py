"""
脱敏安全模板（仅作配置示例，不是完整分析器）。

原始文件位于：
C:\\Users\\wardc\\Documents\\New project gpt\\AI-archive\\apps\\WeChat-MiMo-Analyzer\\src\\contact_analyzer.py

原文件没有复制到桌面归档，因为历史版本在源码中包含明文 MiMo 凭据。
请先轮换旧凭据，再通过环境变量提供新凭据；不要把真实 Token 写回源码。
"""

import os

MIMO_API_KEY = os.environ["MIMO_API_KEY"]
MIMO_BASE_URL = os.environ.get(
    "MIMO_BASE_URL",
    "https://api.xiaomimimo.com/anthropic",
)

# 在完整分析器中使用：
# headers = {"Authorization": f"Bearer {MIMO_API_KEY}"}
# endpoint = f"{MIMO_BASE_URL.rstrip('/')}/v1/messages"
