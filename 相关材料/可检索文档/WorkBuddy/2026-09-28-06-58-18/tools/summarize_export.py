# -*- coding: utf-8 -*-
"""summarize_export.py — 统计 09 导出：会话量级 / 月度分布 / 最近 68 天热度"""
import json
import os
import sys
import time
from collections import Counter, defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\09_WeFlow增量导出_2026-09-29\01_WeFlow可读导出"
CUT68 = 1784822400  # 2026-07-24 00:00 CST

rows = []
for d in os.listdir(BASE):
    p = os.path.join(BASE, d)
    if not os.path.isdir(p):
        continue
    for fn in os.listdir(p):
        if not fn.endswith(".json"):
            continue
        try:
            j = json.load(open(os.path.join(p, fn), encoding="utf-8"))
        except Exception:
            continue
        ms = j.get("messages") or []
        if not ms:
            continue
        ts = [m.get("createTime") or 0 for m in ms]
        recent = [t for t in ts if t >= CUT68]
        rows.append({
            "name": j.get("displayName") or fn,
            "n": len(ms),
            "n68": len(recent),
            "first": min(ts),
            "last": max(ts),
        })

print(f"会话数：{len(rows)}   消息总数：{sum(r['n'] for r in rows)}")
print(f"最近 68 天（2026-07-24 后）消息：{sum(r['n68'] for r in rows)}")
print()

# 月度分布
mon = Counter()
for r in rows:
    pass
allmonths = Counter()
for d in os.listdir(BASE):
    p = os.path.join(BASE, d)
    if not os.path.isdir(p):
        continue
    for fn in os.listdir(p):
        if not fn.endswith(".json"):
            continue
        try:
            j = json.load(open(os.path.join(p, fn), encoding="utf-8"))
        except Exception:
            continue
        for m in (j.get("messages") or []):
            t = m.get("createTime") or 0
            if t:
                allmonths[time.strftime("%Y-%m", time.localtime(t))] += 1

print("── 月度消息量 ──")
for k in sorted(allmonths):
    bar = "█" * max(1, int(allmonths[k] / 400))
    print(f"  {k}  {allmonths[k]:>7}  {bar}")
print()

print("── 近一年 TOP30 会话（按总消息） ──")
for r in sorted(rows, key=lambda x: -x["n"])[:30]:
    print(f"  {r['n']:>6} 条  近68天{r['n68']:>5}  {str(r['name'])[:30]}")
print()

print("── 最近 68 天 TOP40 会话（盲区主力） ──")
for r in sorted(rows, key=lambda x: -x["n68"])[:40]:
    if r["n68"] == 0:
        break
    print(f"  近68天{r['n68']:>5} / 总{r['n']:>6}  {str(r['name'])[:30]}")
