# -*- coding: utf-8 -*-
"""收尾：压缩 §十三 引言（细节已在引擎 + 打通页）。"""
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
    "> **★ 那轮「系统跑通」的真正发现**：**Obsidian 侧早已完全打通**（`王利敏.md` / `海燕.md` / `01_个人信息\\项目\\中传交互技术课-旁听.md`），**引擎侧四层全空** → 已按维护协议**以 Obsidian 为准并入**。★ **这是「信息配合不起来」的第 2 次现形**（第 1 次＝台账 `persons`/`aliases` 是空表）。\n",
    "> **★ 那轮「系统跑通」的真正发现**：**Obsidian 侧早已完全打通**（`王利敏.md` / `海燕.md` / `01_个人信息\\项目\\中传交互技术课-旁听.md`），**引擎侧四层全空** → 已**以 Obsidian 为准并入**。★ 这是「信息配合不起来」的第 2 次现形。\n",
)
swap(
    "- ★★ **修正 Q7**：母亲 09-11「**不要说你是央美的**」「就说**动画学院**的」「**低调些**」→ 与「Q7＝好面子」**方向相反** → **新表述：不是「他爱面子」，是「他在身份上做风险管理，母亲是主要风控人」**。★ 10-09「**没有领导查课。就进去**」＝**第 2 次实证**。\n",
    "- ★★ **修正 Q7**：母亲 09-11「**不要说你是央美的**」「就说**动画学院**的」「**低调些**」→ 与「Q7＝好面子」**方向相反** → **新表述：不是「他爱面子」，是「他在身份上做风险管理，母亲是主要风控人」**。★ 10-09「**没有领导查课。就进去**」＝第 2 次实证。\n",
)

io.open(p, "w", encoding="utf-8").write(s)
after = len(s.encode("utf-8"))
print("bytes: %d -> %d | lines: %d | sections: %d" % (before, after, s.count("\n") + 1, s.count("\n## ")))
