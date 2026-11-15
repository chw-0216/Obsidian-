# -*- coding: utf-8 -*-
import csv, sys, collections
p = r"_tmp_jinglin\接待证据_原始.csv"
rows = list(csv.DictReader(open(p, encoding='utf-8-sig')))
# 只保留 2026-06-01 之后
rows = [r for r in rows if r['时间'] >= '2026-06-01']
print("条数:", len(rows))
byd = collections.OrderedDict()
for r in rows:
    byd.setdefault(r['时间'][:10], []).append(r)
for d, rs in byd.items():
    print("\n=== %s (%d) ===" % (d, len(rs)))
    for r in rs:
        print("  [%s|%s|%s] %s" % (r['时间'][11:], r['会话'][:14], r['发送方'], r['内容'][:220]))
