# -*- coding: utf-8 -*-
import csv, collections, os
D = r"C:\Users\wardc\Desktop\07_聊天记录分析\陈晔会话图片_2026-10-14"
rows = list(csv.DictReader(open(os.path.join(D, "01_定位索引.csv"), encoding="utf-8-sig")))
print("总行数:", len(rows))
ok = [r for r in rows if r["解密产物"]]
miss = [r for r in rows if not r["解密产物"]]
print("有产物:", len(ok), " MISS:", len(miss))
print("匹配层级:", dict(collections.Counter(r["匹配层级"] for r in rows)))
print()
print("按年 · 总 / 已归档 / MISS")
for y in sorted({r["时间"][:4] for r in rows}):
    s = [r for r in rows if r["时间"][:4] == y]
    o = sum(1 for r in s if r["解密产物"])
    print("  %s  %3d  %3d  %3d" % (y, len(s), o, len(s) - o))
print()
print("发送方:", dict(collections.Counter(r["发送方"] for r in rows)))
print("校验:", dict(collections.Counter(r["校验"] for r in rows)))
print()
print("=== MISS 明细（%d 条）===" % len(miss))
for r in miss:
    print("  %s  %s  %s" % (r["时间"], r["发送方"], r["月份"]))
