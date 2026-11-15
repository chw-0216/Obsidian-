# -*- coding: utf-8 -*-
import io
p = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\.workbuddy-ai\memory\MEMORY.md"
s = io.open(p, encoding="utf-8").read()
before = len(s.encode("utf-8"))
for o, n in [
  ("## 十三、★★★ 中传交互技术课 · 旁听线（2026-10-08 并入引擎 · 细节见 `05` 三·补·52 / 53）",
   "## 十三、★★★ 中传交互技术课 · 旁听线（细节见 `05` 三·补·52 / 53）"),
  ("## 十一、会话名对照（2026-10-08）", "## 十一、会话名对照（2026-10-09）"),
  ("## 十二、★ 前置闸门（2026-10-08 新增 · 来自《激进构成》落地版 · **整节在 `05-纠偏层.md` 四·补**）",
   "## 十二、★ 前置闸门（来自《激进构成》落地版 · **整节在 `05-纠偏层.md` 四·补**）"),
  ("- **批处理**：`_tmp\batch\batch.sqlite`（materials 64,109 / weeks 81 / experiences 2,207）· 子命令 9 个（`all` 是重活）· ★ 四态分开，重跑前先 delete 本阶段行。",
   "- **批处理**：`_tmp\batch\batch.sqlite`（materials 64,109 / weeks 81 / experiences 2,207）· 子命令 9 个（`all` 是重活）· ★ 四态分开，重跑前先 delete 本阶段行。"),
]:
    if o in s: s = s.replace(o, n, 1)
    else: print("MISS:", o[:40])
io.open(p, "w", encoding="utf-8").write(s)
print("bytes: %d -> %d" % (before, len(s.encode("utf-8"))))
