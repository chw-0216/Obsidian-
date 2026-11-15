# -*- coding: utf-8 -*-
import sqlite3, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DB = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\batch\batch.sqlite"
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

print("=== 表 ===")
for r in c.execute("select name,type from sqlite_master where type in ('table','view')"):
    print(" ", r[0], r[1])

print("\n=== photos 列 ===")
for r in c.execute("pragma table_info(photos)"):
    print(" ", r[1], r[2])

print("\n=== photos 统计 ===")
print(" 总数:", c.execute("select count(*) from photos").fetchone()[0])
for r in c.execute("select root, count(*) n, sum(case when ts is not null then 1 else 0 end) wt, sum(case when width>=800 and bytes>=80000 then 1 else 0 end) usable from photos group by root order by n desc"):
    print("  %-14s n=%-6d 有ts=%-5d 可用=%d" % (r[0], r[1], r[2] or 0, r[3] or 0))

print("\n=== category ===")
for r in c.execute("select category, count(*) from photos group by category order by 2 desc"):
    print("  %-40s %d" % (r[0], r[1]))

print("\n=== role ===")
for r in c.execute("select role, count(*) from photos group by role order by 2 desc"):
    print("  %-12s %d" % (str(r[0]), r[1]))

print("\n=== date_src ===")
for r in c.execute("select date_src, count(*) from photos group by date_src order by 2 desc"):
    print("  %-16s %d" % (str(r[0]), r[1]))
