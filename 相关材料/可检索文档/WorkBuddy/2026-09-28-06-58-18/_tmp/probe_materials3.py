# -*- coding: utf-8 -*-
import sqlite3, os, sys, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DB = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\batch\batch.sqlite"
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

print("=== 图片：按 root ===")
for r in c.execute("select root, count(*) from materials where kind='图片' group by 1 order by 2 desc"):
    print("  %-14s %d" % (str(r[0]), r[1]))

print("\n=== 图片：按 root + 二级目录 ===")
rows = list(c.execute("select path, root from materials where kind='图片'"))
cnt = collections.Counter()
for r in rows:
    p = r["path"]
    # 取 root 之后的 2 层
    parts = p.split(os.sep)
    key = os.sep.join(parts[:6]) if len(parts) > 6 else os.sep.join(parts[:-1])
    cnt[key] += 1
for k, v in cnt.most_common(50):
    print("  %-95s %d" % (k[:95], v))
