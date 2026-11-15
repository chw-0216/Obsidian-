# -*- coding: utf-8 -*-
import sqlite3, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DB = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\batch\batch.sqlite"
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

print("=== kind 分布 ===")
for r in c.execute("select kind, count(*) from materials group by 1 order by 2 desc limit 30"):
    print("  %-22s %d" % (str(r[0]), r[1]))

print("\n=== ext 抽样 ===")
for r in c.execute("select distinct ext from materials limit 40"):
    print("  ", repr(r[0]))

print("\n=== root 分布 ===")
for r in c.execute("select root, count(*) from materials group by 1 order by 2 desc limit 30"):
    print("  %-60s %d" % (str(r[0])[:60], r[1]))

print("\n=== 图片 kind：按 root ===")
for r in c.execute("select root, count(*) from materials where kind='image' group by 1 order by 2 desc limit 40"):
    print("  %-60s %d" % (str(r[0])[:60], r[1]))
