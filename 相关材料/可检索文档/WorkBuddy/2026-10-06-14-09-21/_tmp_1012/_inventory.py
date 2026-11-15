# -*- coding: utf-8 -*-
"""快速清点：本机现存的项目相关材料位置（只读，不移动）。"""
import os, io, sys, json

ROOTS = [
    r"C:\Users\wardc\Desktop",
    r"C:\Users\wardc\Documents",
    r"C:\Users\wardc\WorkBuddy AI",
]

# 只要这些名字命中的目录/文件，就算“项目相关”
KEYS = ["井邻", "洞台", "陈晔", "在场与回应", "中期汇报", "乡村美育", "栗壳", "植墨",
        "澜沧", "支教", "文件传输助手", "聊天记录", "留光回声", "三方向", "栗约",
        "印迹", "碳迹", "制版", "丝网", "甲马", "木刻"]

SKIP = {"node_modules", ".git", "$Recycle.Bin", "site-packages", "__pycache__",
        ".obsidian", "Windows", "AppData"}

def walk(root, maxdepth=3, maxitems=4000):
    out = []
    n = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP and not d.startswith(".")]
        depth = dirpath[len(root):].count(os.sep)
        if depth >= maxdepth:
            dirnames[:] = []
        base = os.path.basename(dirpath)
        hit = any(k in base for k in KEYS)
        if hit:
            # 统计该目录规模
            sz = 0; cnt = 0
            for dp2, dn2, fn2 in os.walk(dirpath):
                dn2[:] = [d for d in dn2 if d not in SKIP]
                for f in fn2:
                    try:
                        sz += os.path.getsize(os.path.join(dp2, f)); cnt += 1
                    except Exception:
                        pass
            out.append((dirpath, cnt, sz))
            dirnames[:] = []   # 已统计，不再下钻
            n += 1
            if n > maxitems: break
    return out

print("=" * 100)
print("项目相关目录（按路径）")
print("=" * 100)
allr = []
for r in ROOTS:
    if not os.path.isdir(r):
        continue
    for p, c, s in walk(r):
        allr.append((p, c, s))

allr.sort(key=lambda x: x[0])
for p, c, s in allr:
    print("%-92s %6d 文件 %9.1f MB" % (p, c, s / 1048576))
print()
print("合计目录数:", len(allr))
print("合计体积: %.1f MB" % (sum(s for _, _, s in allr) / 1048576))

# 顶层目录清点
print()
print("=" * 100)
print("Desktop 顶层")
print("=" * 100)
d = r"C:\Users\wardc\Desktop"
for e in sorted(os.listdir(d)):
    fp = os.path.join(d, e)
    if os.path.isdir(fp):
        sz = 0; cnt = 0
        for dp2, dn2, fn2 in os.walk(fp):
            dn2[:] = [x for x in dn2 if x not in SKIP]
            for f in fn2:
                try: sz += os.path.getsize(os.path.join(dp2, f)); cnt += 1
                except Exception: pass
        print("  %-52s %7d 文件 %10.1f MB" % (e, cnt, sz / 1048576))
    else:
        try: print("  %-52s            %10.1f MB" % (e, os.path.getsize(fp) / 1048576))
        except Exception: pass
