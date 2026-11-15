# -*- coding: utf-8 -*-
"""第九轮（收尾）压缩 MEMORY.md —— 合并 §五 低价值行。"""
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
    "| 35 | 七层检修；`距离地图.csv` 曾严重过期；建立 `00-真相源` |\n"
    "| 36/37 | 微信支付×美团 2,207 条；2026-08 支出峰值＝央美学费 ¥20,000 |\n",
    "| 35–37 | 七层检修；建立 `00-真相源`；微信支付×美团 2,207 条；2026-08 支出峰值＝央美学费 ¥20,000 |\n",
)
swap(
    "| 32 | 这两年六阶段；真拐点 **2025-09 央美入学**（2025-08 是订阅潮非社交扩张） |\n"
    "| 33 | 这一年钱是主线；债务线跨 20 个月（起点 2025-03-10）；关系「工程化」 |\n",
    "| 32/33 | 两年六阶段，真拐点 **2025-09 央美入学**；这一年钱是主线，债务线跨 20 个月（起点 2025-03-10）；关系「工程化」 |\n",
)
swap(
    "- **一次只问一个问题**，口语化 + A/B/C/D 选项（术语堆叠会失效）。",
    "- **一次只问一个问题**，口语化 + A/B/C/D 选项（术语堆叠会失效）；**提问前先扫「已答/未答总账」**。",
)
swap(
    "2. 「父母冷战」不得当数据事实引用（全库零命中，只有本人自述；引用必标来源）。",
    "2. 「父母冷战」不得当数据事实引用（全库零命中，只有本人自述；引用必标来源）。\n",
)

io.open(p, "w", encoding="utf-8").write(s)
after = len(s.encode("utf-8"))
print("bytes: %d -> %d | lines: %d" % (before, after, s.count("\n") + 1))
