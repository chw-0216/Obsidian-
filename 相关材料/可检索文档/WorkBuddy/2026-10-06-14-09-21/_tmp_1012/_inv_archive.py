# -*- coding: utf-8 -*-
"""清点 AI-archive/outputs 中本项目相关的产物"""
import os

ROOT = r"C:\Users\wardc\Documents\New project gpt\AI-archive\outputs"
KEYS = ["在场与回应", "井邻", "澜沧", "知行", "丝网", "植墨", "栗", "留光", "版画", "悲鸿"]

def size(p):
    s = 0; c = 0
    for dp, dn, fn in os.walk(p):
        dn[:] = [d for d in dn if d not in ("node_modules", "__pycache__", ".git")]
        for f in fn:
            try:
                s += os.path.getsize(os.path.join(dp, f)); c += 1
            except Exception:
                pass
    return c, s

tot = 0
rows = []
for e in sorted(os.listdir(ROOT)):
    if not any(k in e for k in KEYS):
        continue
    fp = os.path.join(ROOT, e)
    if os.path.isdir(fp):
        c, s = size(fp)
        mt = os.path.getmtime(fp)
    else:
        c, s, mt = 1, os.path.getsize(fp), os.path.getmtime(fp)
    import datetime
    rows.append((e, c, s, datetime.datetime.fromtimestamp(mt).strftime("%Y-%m-%d %H:%M"), os.path.isdir(fp)))
    tot += s

print("%-56s %6s %10s  %s" % ("名称", "文件", "MB", "修改时间"))
print("-" * 100)
for e, c, s, mt, isd in rows:
    print("%-56s %6d %10.1f  %s %s" % (e[:56], c, s / 1048576, mt, "[目录]" if isd else ""))
print("-" * 100)
print("命中 %d 项 · 合计 %.1f MB" % (len(rows), tot / 1048576))
