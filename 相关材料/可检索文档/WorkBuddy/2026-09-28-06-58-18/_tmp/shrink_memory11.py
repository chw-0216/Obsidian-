# -*- coding: utf-8 -*-
"""最后一轮压缩 —— 目标 ≤15,950 字节。"""
import io

p = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\.workbuddy-ai\memory\MEMORY.md"
s = io.open(p, encoding="utf-8").read()
before = len(s.encode("utf-8"))


def swap(o, n):
    global s
    if o in s:
        s = s.replace(o, n, 1)
        return True
    print("MISS:", o[:45].replace("\n", " "))
    return False


swap(
    "- ✅ **合订本** `自我理解引擎_统一排查台_2026-10-05.html` —— **后续轮次往这一份加节，不新增文件**。决策中枢最新 = `决策中枢_2026-10-08.html`。\n",
    "- ✅ **合订本** `自我理解引擎_统一排查台_2026-10-05.html` —— **后续轮次往这一份加节，不新增文件**。\n",
)
swap(
    "- ★★ **实例最大发现（临汾）：「必须去满 5 天」是假约束** → **时间冲突可能不存在**。\n",
    "- ★★ **实例（临汾）：「必须去满 5 天」是假约束** → **时间冲突可能不存在**。\n",
)
swap(
    "2. 「父母冷战」不得当数据事实引用（全库零命中，只有本人自述；引用必标来源）。\n",
    "2. 「父母冷战」不得当数据事实引用（全库零命中，只有本人自述；引用必标来源）。",
)
swap(
    "- **数据主权**：微信原始数据全程本地，绝不上传第三方；网页版 AI 禁传聊天原文（只传画像/报告）。",
    "- **数据主权**：微信原始数据全程本地，绝不上传第三方；网页版 AI 禁传聊天原文。",
)

io.open(p, "w", encoding="utf-8").write(s)
after = len(s.encode("utf-8"))
print("bytes: %d -> %d | lines %d | sections %d" % (before, after, s.count("\n") + 1, s.count("\n## ")))
