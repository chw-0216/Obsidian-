# -*- coding: utf-8 -*-
"""MEMORY.md 第 7 次维护：为本轮「手填区回写闭环」腾出字节预算。
★ 每处必须唯一命中；★ 读写均 newline=''（否则 Windows 下 \n→\r\n，每行 +1 字节）。
"""
import io
import re
import sys

P = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\.workbuddy-ai\memory\MEMORY.md"

OPS = [
    # ---- 压缩（均为冗余交叉引用 / 可从日志复原的细节）----
    (r"（见 `05` 三·补·54）", ""),
    (r"（细节见 `05` 三·补·55–58）", ""),
    (r"（materials 64,109 / weeks 81 / experiences 2,207）", ""),
    (r"（\*\*判据＝视差残差比\*\*）", ""),
    (r"④ 何一沙＝美术馆媒体部主任（\*\*推断\*\*）", "④ 何一沙＝美术馆媒体部主任"),
    (r"脚本 19 天 / 群 / 日期（唯一闸门）", "脚本 19 天 / 群 / 日期"),
    (r"图片 OCR / 视频 ASR / link 补录 · 3 条待核实。", "图片 OCR / 视频 ASR / link 补录。"),
    (r"③ 现金流：借舒 300 → 母 450 → ¥630 ", ""),
    (r"→ Obsidian `01_个人信息\\项目\\格拉斯哥北京校友会-文案与传播\.md`",
     "→ `…\\项目\\格拉斯哥北京校友会-文案与传播.md`"),
    (r"\*\*`recommendations` 11\*\* · \*\*`rec_deps` 22\*\*", "`recommendations` 11 · `rec_deps` 22"),
    (r"（`王利敏\.md` / `海燕\.md` / `项目\\中传交互技术课-旁听\.md`）",
     "（`王利敏.md` / `海燕.md` / `中传交互技术课-旁听.md`）"),
    (r"09-20 领「\*\*交互盒子\*\*」；10-09 用 \*\*Fritzing\*\*。", "09-20 领「交互盒子」；10-09 用 Fritzing。"),
    # ---- 本轮新增内容：压缩版幂等教训 ----
    (r"(?s)- \*\*Windows 控制台中文/emoji 会截断\*\*[^\n]*\n",
     None),  # 占位：下面单独处理
]

s = io.open(P, encoding="utf-8", newline="").read()
n0 = len(s.encode("utf-8"))

for i, (pat, rep) in enumerate(OPS, 1):
    if rep is None:
        continue
    hits = len(re.findall(pat, s))
    if hits != 1:
        print("!! OP%d 命中 %d 次：%s" % (i, hits, pat[:50]))
        sys.exit(1)
    s = re.sub(pat, rep, s, count=1)

# 幂等教训：先删旧的长句，再插压缩版（★ 本文件是 CRLF，字面量必须用 \r\n）
NL = "\r\n"
old_line = ("- **Windows 控制台中文/emoji 会截断** → 长结果写文件再 Read。"
            "**朋友圈 tid**：`>>23`（**不是 >>32**）。**FTS 用 trigram，词 ≥3 字**"
            "（2 字人名用 `LIKE`）。" + NL +
            "- ★ **生成器必须幂等**：任何「读旧文件 → 重写」的 render（如 "
            "`selfmodel.py render`），必须断言**连续两次字节数一致**。"
            "本轮实测漏掉围栏行 → **每轮 +4 字节**，静默不收敛。" + NL)
new_line = ("- **Windows 控制台中文/emoji 会截断** → 长结果写文件再 Read。"
            "**朋友圈 tid**：`>>23`（**不是 >>32**）。**FTS 用 trigram，词 ≥3 字**"
            "（2 字人名用 `LIKE`）。" + NL +
            "- ★ **生成器必须幂等**：任何「读旧文件→重写」的 render，"
            "必须断言**连续两次字节数一致**（本轮漏围栏行 → 每轮 +4 字节）。" + NL)
if s.count(old_line) != 1:
    print("!! 幂等行未唯一命中")
    sys.exit(1)
s = s.replace(old_line, new_line, 1)

io.open(P, "w", encoding="utf-8", newline="").write(s)
n1 = len(s.encode("utf-8"))
print("字节：%d → %d（%+d）· 上限 16,143 · 余 %d" % (n0, n1, n1 - n0, 16143 - n1))
print("节数：", len(re.findall(r"(?m)^## ", s)))
