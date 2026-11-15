# -*- coding: utf-8 -*-
"""扫描各分版批次的文件生成时间（最早/最晚），用于建立 出图→打印→制版 时间对照"""
import os, datetime, collections

def scan(base, label, maxdepth=6):
    """返回 (文件数, 总大小, 最早mtime, 最晚mtime)"""
    n = 0; sz = 0; mn = None; mx = None
    for root, dirs, files in os.walk(base):
        if root[len(base):].count(os.sep) > maxdepth:
            dirs[:] = []; continue
        for f in files:
            p = os.path.join(root, f)
            try:
                st = os.stat(p)
            except OSError:
                continue
            n += 1; sz += st.st_size
            t = st.st_mtime
            mn = t if mn is None else min(mn, t)
            mx = t if mx is None else max(mx, t)
    if n == 0:
        return None
    fmt = lambda t: datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M")
    return n, sz, fmt(mn), fmt(mx)

def rsize(n):
    for u in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.0f}B" if u == "B" else f"{n:.1f}{u}"
        n /= 1024

CODEX = r"C:\Users\wardc\Documents\Codex\2026-09-30\new-chat-6\outputs"
S5 = r"C:\Users\wardc\Desktop\05_井邻项目_视觉与丝网印刷"

print("=" * 100)
print("【A】Codex 输出目录（26 个版本）")
print("=" * 100)
for d in sorted(os.listdir(CODEX)):
    p = os.path.join(CODEX, d)
    if not os.path.isdir(p):
        continue
    r = scan(p, d)
    if r:
        print(f"{d}\n    {r[0]:>4} 文件  {rsize(r[1]):>8}   最早 {r[2]}   最晚 {r[3]}")

print()
print("=" * 100)
print("【B】桌面 05_ 井邻项目_视觉与丝网印刷 相关子目录")
print("=" * 100)
TARGETS = [
    "位图", "制版", "悲鸿",
    "偏移四型A4满版竖构图_CMYK四色硫酸纸_原Codex主视觉_20260819",
    "偏移四型CMYK四色A4硫酸纸分版_原Codex主视觉_20260819",
    "交互文件与主视觉汇总/视觉_06_MBTI八版制版系统",
    "交互文件与主视觉汇总/交互_05_MBTI丝网_活体原型",
    "偏移四型-MediaPipe-v2", "偏移四型-现场预览-重来",
    "12秒丝网版画_9个关键帧_20260721",
    "井邻临时策划", "井邻风景", "刘丽萍检查报告",
    "衬衫单色", "配色优化575", "575周年",
]
for t in TARGETS:
    p = os.path.join(S5, t.replace("/", os.sep))
    if not os.path.isdir(p):
        print(f"{t}  —— 不存在")
        continue
    r = scan(p, t)
    if r:
        print(f"{t}\n    {r[0]:>4} 文件  {rsize(r[1]):>8}   最早 {r[2]}   最晚 {r[3]}")

print()
print("=" * 100)
print("【C】桌面 05_ 顶层子目录一览（含修改时间）")
print("=" * 100)
for d in sorted(os.listdir(S5)):
    p = os.path.join(S5, d)
    if os.path.isdir(p):
        t = datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M")
        n = sum(len(f) for _, _, f in os.walk(p))
        print(f"{t}  {n:>5} 文件  {d}")
