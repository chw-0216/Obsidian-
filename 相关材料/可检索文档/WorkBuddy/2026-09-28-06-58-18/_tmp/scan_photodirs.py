# -*- coding: utf-8 -*-
"""扫描「照片密集」目录 —— 找 photo_index 未覆盖的照片来源"""
import os, sys, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOTS = [
    r"C:\Users\wardc\Desktop",
    r"C:\Users\wardc\Documents",
    r"C:\Users\wardc\Pictures",
    r"C:\Users\wardc\Downloads",
]
IMG = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".gif", ".webp", ".heic", ".hevc", ".raw", ".cr2", ".arw", ".dng"}
SKIP = {"node_modules", ".git", "__pycache__", "site-packages", "AppData"}

agg = collections.Counter()
sizes = collections.Counter()
for R in ROOTS:
    if not os.path.isdir(R):
        continue
    for dp, ds, fs in os.walk(R):
        ds[:] = [d for d in ds if d not in SKIP]
        if dp.count(os.sep) > 9:
            ds[:] = []
            continue
        n = 0
        for f in fs:
            e = os.path.splitext(f)[1].lower()
            if e in IMG:
                n += 1
                try:
                    sizes[dp] += os.path.getsize(os.path.join(dp, f))
                except Exception:
                    pass
        if n >= 25:
            agg[dp] = n

print("=== 图片 ≥25 张的目录（按数量） ===")
for d, n in agg.most_common(60):
    print("  %-96s %5d  %6.1f MB" % (d[:96], n, sizes[d] / 1e6))
print("\n合计目录 %d 个，图片 %d 张，%.1f GB" % (len(agg), sum(agg.values()), sum(sizes.values()) / 1e9))
