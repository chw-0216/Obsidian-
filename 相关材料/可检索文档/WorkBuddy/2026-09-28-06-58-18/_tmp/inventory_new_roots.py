# -*- coding: utf-8 -*-
import os, sys, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
IMG = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".gif", ".webp", ".heic", ".hevc",
       ".raw", ".cr2", ".cr3", ".arw", ".dng", ".nef", ".orf", ".raf", ".psd", ".ai", ".xcf"}
SKIP = {"node_modules", ".git", "__pycache__", "site-packages"}

ROOTS = [
    (r"C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出\朋友圈\media", "朋友圈media"),
    (r"C:\Users\wardc\Desktop\05_井邻项目_视觉与丝网印刷", "井邻项目"),
    (r"C:\Users\wardc\Desktop\06_井邻项目_宣传申报与合作", "井邻宣传"),
    (r"C:\Users\wardc\Desktop\08_图片素材", "图片素材"),
    (r"C:\Users\wardc\Desktop\_定稿图_1002晚", "定稿图"),
    (r"C:\Users\wardc\Desktop\新增RAW优化版", "RAW优化版"),
    (r"C:\Users\wardc\Desktop\澜沧支教_提交包", "澜沧提交包"),
    (r"C:\Users\wardc\Desktop\知行计划最终材料", "知行最终材料"),
    (r"C:\Users\wardc\Desktop\知行计划最终版", "知行最终版"),
    (r"C:\Users\wardc\Desktop\_media_export", "媒体导出"),
    (r"C:\Users\wardc\Pictures\Capture One Catalog\Originals", "C1原片"),
    (r"C:\Users\wardc\Desktop\微信导出_窗口期_20260930", "微信导出窗口期"),
    (r"C:\Users\wardc\Documents\WeFlow\Images", "WeFlow图片"),
]
for root, name in ROOTS:
    if not os.path.isdir(root):
        print("%-14s ★不存在  %s" % (name, root)); continue
    n = 0; sz = 0; ext = collections.Counter(); sub = collections.Counter()
    for dp, ds, fs in os.walk(root):
        ds[:] = [d for d in ds if d not in SKIP]
        for f in fs:
            e = os.path.splitext(f)[1].lower()
            if e in IMG:
                n += 1; ext[e] += 1
                try: sz += os.path.getsize(os.path.join(dp, f))
                except Exception: pass
                rel = os.path.relpath(dp, root)
                sub[rel.split(os.sep)[0]] += 1
    print("%-14s n=%-6d %7.1f MB  ext=%s" % (name, n, sz / 1e6, dict(ext.most_common(5))))
    if n and len(sub) > 1:
        for k, v in sub.most_common(8):
            print("      %-46s %d" % (k[:46], v))
