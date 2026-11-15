# -*- coding: utf-8 -*-
"""scan_docs.py — 扫描目录下的文档/成果类文件（只读）"""
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\wardc\Desktop\07_聊天记录分析"
EXTS = {".md", ".csv", ".json", ".txt", ".html", ".jsonl", ".py", ".ps1", ".js"}
SKIP_DIRS = {"node_modules", "__pycache__", ".git", "01_WeFlow可读导出",
             "02_原始数据备份", "01_WeFlow可读导出".lower()}

rows = []
for dp, dns, fns in os.walk(ROOT):
    dns[:] = [d for d in dns if d not in SKIP_DIRS]
    for f in fns:
        ext = os.path.splitext(f)[1].lower()
        if ext not in EXTS:
            continue
        fp = os.path.join(dp, f)
        try:
            st = os.stat(fp)
        except OSError:
            continue
        if st.st_size > 3_000_000:
            continue
        rows.append((st.st_mtime, st.st_size, fp))

rows.sort(reverse=True)
print(f"文档类文件：{len(rows)} 个（已排除媒体与原始备份）\n")
cur = None
for mt, sz, fp in rows:
    rel = os.path.relpath(fp, ROOT)
    top = rel.split(os.sep)[0]
    if top != cur:
        cur = top
        print(f"\n── {top} ──")
    t = time.strftime("%m-%d", time.localtime(mt))
    print(f"  {t}  {sz/1024:>8.1f}KB  {rel}")
