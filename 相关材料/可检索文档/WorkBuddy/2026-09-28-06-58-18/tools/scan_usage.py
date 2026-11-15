# -*- coding: utf-8 -*-
"""scan_usage.py — 统计目录占用（只读）"""
import os
import sys
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\wardc\Desktop\07_聊天记录分析"


def size_of(path):
    total = 0
    files = 0
    newest = 0
    for dp, dns, fns in os.walk(path):
        for f in fns:
            fp = os.path.join(dp, f)
            try:
                st = os.stat(fp)
                total += st.st_size
                files += 1
                if st.st_mtime > newest:
                    newest = st.st_mtime
            except OSError:
                pass
    return total, files, newest


def human(n):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}PB"


import time

rows = []
for name in sorted(os.listdir(ROOT)):
    p = os.path.join(ROOT, name)
    if os.path.isdir(p):
        s, f, mt = size_of(p)
        rows.append((s, f, mt, name, "dir"))
    else:
        try:
            st = os.stat(p)
            rows.append((st.st_size, 1, st.st_mtime, name, "file"))
        except OSError:
            pass

rows.sort(reverse=True)
print(f"根目录：{ROOT}")
print(f"{'大小':>10}  {'文件数':>7}  {'最后修改':<12}  名称")
print("-" * 70)
total = 0
for s, f, mt, name, kind in rows:
    total += s
    t = time.strftime("%Y-%m-%d", time.localtime(mt)) if mt else "?"
    print(f"{human(s):>10}  {f:>7}  {t:<12}  {name}{'/' if kind=='dir' else ''}")
print("-" * 70)
print(f"合计：{human(total)}")
