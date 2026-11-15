# -*- coding: utf-8 -*-
import csv, collections, os, io

F = r"C:\Users\wardc\Desktop\disk-cleanup-2026-10-13\重复处置日志_删除.csv"
rows = list(csv.DictReader(io.open(F, encoding="utf-8-sig")))
print("记录数:", len(rows))

tot = collections.Counter(); cnt = collections.Counter()

def key_of(p):
    for root in ("Desktop", "Documents"):
        seg = "\\" + root + "\\"
        if seg in p:
            rest = p.split(seg, 1)[1]
            parts = rest.split("\\")
            return root + "\\" + parts[0]
    parts = p.split("\\")
    return "\\".join(parts[:3])

for r in rows:
    try: v = float(r["MB"])
    except Exception: v = 0.0
    k = key_of(r["Path"])
    tot[k] += v; cnt[k] += 1

print()
print("%-56s %9s %6s" % ("目录", "MB", "条数"))
for k, v in tot.most_common(30):
    print("%-56s %9.1f %6d" % (k, v, cnt[k]))

print()
print("=== 中期汇报_2026-09 明细（按二级目录）===")
sub = collections.Counter(); subn = collections.Counter()
for r in rows:
    if "Desktop\\中期汇报_2026-09\\" in r["Path"]:
        rest = r["Path"].split("Desktop\\中期汇报_2026-09\\", 1)[1]
        parts = rest.split("\\")
        k = parts[0] if len(parts) > 1 else "(顶层文件)"
        try: v = float(r["MB"])
        except Exception: v = 0.0
        sub[k] += v; subn[k] += 1
for k, v in sub.most_common():
    print("  %-40s %9.1f MB  %5d 条" % (k, v, subn[k]))
print("  合计: %.1f MB / %d 条" % (sum(sub.values()), sum(subn.values())))

print()
print("=== Desktop\\123 明细 ===")
sub2 = collections.Counter(); sub2n = collections.Counter()
for r in rows:
    if "Desktop\\123\\" in r["Path"]:
        rest = r["Path"].split("Desktop\\123\\", 1)[1]
        parts = rest.split("\\")
        k = "\\".join(parts[:2]) if len(parts) > 2 else parts[0]
        try: v = float(r["MB"])
        except Exception: v = 0.0
        sub2[k] += v; sub2n[k] += 1
for k, v in sub2.most_common():
    print("  %-52s %9.1f MB  %5d 条" % (k, v, sub2n[k]))
print("  合计: %.1f MB / %d 条" % (sum(sub2.values()), sum(sub2n.values())))

print()
print("=== 结果字段分布 ===")
print(collections.Counter(r["Result"] for r in rows).most_common(6))

print()
print("=== 我 10-12 生成的交付物是否被删 ===")
KEY = ["井邻全梳", "定位索引", "交接清单", "陈晔导师聊天记录", "17_陈晔会话图片", "全部信息总表", "思路总纲"]
for k in KEY:
    hit = [r for r in rows if k in r["Path"]]
    print("  %-24s %3d 条" % (k, len(hit)))
    for r in hit[:3]:
        print("        %s  %s MB  %s" % (r["Path"], r["MB"], r["Result"]))
