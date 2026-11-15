# -*- coding: utf-8 -*-
"""第七轮压缩 MEMORY.md —— 目标 ≤15,950 字符。"""
import io

p = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\.workbuddy-ai\memory\MEMORY.md"
s = io.open(p, encoding="utf-8").read()
orig = len(s)


def swap(o, n):
    global s
    if o in s:
        s = s.replace(o, n, 1)
        return True
    print("MISS:", o[:45].replace("\n", " "))
    return False


swap(
    "- 交付标准：直接可用 · 结构清晰 · 逻辑严密 · 可迭代 · 专业美观。**拒绝半成品与「只给建议不给方案」**。\n",
    "- 交付标准：直接可用 · 结构清晰 · 逻辑严密 · 可迭代 · 专业美观。**拒绝半成品、拒绝「只给建议不给方案」**。\n",
)
swap(
    "- ✅ **合订本** `自我理解引擎_统一排查台_2026-10-05.html` —— **后续轮次往这一份加节，不新增文件**。\n"
    "- ✅ 决策中枢最新 = `决策中枢_2026-10-08.html`（六线 · 同步后 11:47）。\n",
    "- ✅ **合订本** `自我理解引擎_统一排查台_2026-10-05.html` —— **后续轮次往这一份加节，不新增文件**。决策中枢最新 = `决策中枢_2026-10-08.html`。\n",
)
swap(
    "- **本机闸门** `SAFE_DELETE_BULK_CONFIRM_REQUIRED`（50/轮，**覆盖已存在文件也算删除**）→ 产物写**独立时间戳目录**；删除走 `tools\\recycle.py`。\n"
    "- **`HTML_ARTIFACTS` 必须列全所有对外 HTML**（漏一个＝版本对不上）。**数字不写死**；**打包脚本排在打戳之后**。\n"
    "- **Windows 控制台中文/emoji 会截断** → 长结果写文件再 Read。\n"
    "- **朋友圈 tid**：`ts_ms=(tid & 0xFFFF...FFFF) >> 23`（**不是 >>32**）。\n"
    "- **FTS 用 trigram，查询词 ≥3 字**（2 字人名用 `LIKE`）；导师 `display_name` 是备注名。\n",
    "- **本机闸门** `SAFE_DELETE_BULK_CONFIRM_REQUIRED`（50/轮，**覆盖已存在文件也算删除**）→ 产物写**独立时间戳目录**；删除走 `tools\\recycle.py`。\n"
    "- **`HTML_ARTIFACTS` 必须列全所有对外 HTML**（漏一个＝版本对不上）。**数字不写死**；**打包脚本排在打戳之后**。\n"
    "- **Windows 控制台中文/emoji 会截断** → 长结果写文件再 Read。**朋友圈 tid**：`>>23`（**不是 >>32**）。\n"
    "- **FTS 用 trigram，查询词 ≥3 字**（2 字人名用 `LIKE`）；导师 `display_name` 是备注名。\n",
)
swap(
    "| 引擎（裁定层） | `C:\\Users\\wardc\\.workbuddy-ai\\skills\\self-understanding-engine\\references\\` |\n",
    "| 引擎（裁定层） | `…\\.workbuddy-ai\\skills\\self-understanding-engine\\references\\` |\n",
)

io.open(p, "w", encoding="utf-8").write(s)
print("chars: %d -> %d | bytes -> %d" % (orig, len(s), len(s.encode("utf-8"))))
