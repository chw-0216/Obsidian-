# -*- coding: utf-8 -*-
"""两年窗口 · 定向核验（只读）
- 逐月曲线：父亲/母亲/同门/Eloise/甘泉/关系更替链/文件传输助手
- 首次出现上下文：琢 / 养肥
- 2026-10 前 4 天活跃
"""
import sqlite3, os, sys, collections

IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
uri = "file:" + IDX.replace("\\", "/") + "?mode=ro"
c = sqlite3.connect(uri, uri=True)

def ym(ts):
    import time
    return time.strftime("%Y-%m", time.localtime(ts))

# 名称 -> session_key 映射
name2key = {}
key2name = {}
for tk, dn in c.execute("select talker, display_name from sessions"):
    if dn:
        name2key.setdefault(dn, tk)
        key2name[tk] = dn

TARGETS = ["蔡峰峰", "刘丽萍", "蔡黎明", "琢", "养肥", "王博", "Eloise", "甘泉",
           "小苹果", "🍬🍬", "陈昶文", "笑一", "沐茜妍", "文件传输助手", "安奇",
           "陈晔", "杨丁懿", "子辰", "李紫玥", "汪伊俊", "舒泽林", "Parapluie"]

want = {}
for t in TARGETS:
    k = name2key.get(t)
    if k:
        want[k] = t

# 单次全表扫描
series = collections.defaultdict(lambda: collections.Counter())
first_last = {}
for sk, ts in c.execute("select session_key, ts from messages"):
    if sk in want:
        m = ym(ts)
        series[want[sk]][m] += 1
        nm = want[sk]
        if nm not in first_last:
            first_last[nm] = [m, m]
        else:
            if m < first_last[nm][0]: first_last[nm][0] = m
            if m > first_last[nm][1]: first_last[nm][1] = m

MONTHS = []
y, mo = 2024, 11
while (y, mo) <= (2026, 10):
    MONTHS.append(f"{y}-{mo:02d}")
    mo += 1
    if mo > 12: y, mo = y + 1, 1

print("=" * 100)
print("A. 逐月曲线（首现 / 末现 / 峰值）")
print("=" * 100)
hdr = "  {:<12}".format("名称") + "".join(f"{m[2:].replace('-','')[:4]:>6}" for m in MONTHS) + "   Σ"
print(hdr)
for nm in TARGETS:
    if nm not in series: 
        print("  {:<12}  —— 库中无此会话".format(nm)); continue
    s = series[nm]
    row = "  {:<12}".format(nm)
    tot = 0
    for m in MONTHS:
        v = s.get(m, 0)
        tot += v
        row += "{:>6}".format(v if v else "·")
    fl = first_last[nm]
    print(row + f"  {tot:>7}   首={fl[0]} 末={fl[1]} 峰={max(s, key=s.get)}={max(s.values())}")

print()
print("=" * 100)
print("B. 2026-10 前 4 天 · 活跃会话 TOP20")
print("=" * 100)
import time
start = int(time.mktime(time.strptime("2026-10-01", "%Y-%m-%d")))
cnt = collections.Counter()
for sk, n in c.execute("select session_key, count(*) from messages where ts>=? group by session_key order by 2 desc limit 25", (start,)):
    print("  {:>6}  {}".format(n, key2name.get(sk, sk)))
print()
print("scanned ok")
