# -*- coding: utf-8 -*-
import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = sqlite3.connect("file:" + r"C:/Users/wardc/WorkBuddy AI/2026-09-28-06-58-18/_tmp/batch/batch.sqlite".replace("\\","/") + "?mode=ro", uri=True)
c.row_factory = sqlite3.Row
print("=== 北京台相关 ===")
for r in c.execute("select root,date,date_src,role,session_name,width,height,note,path from photos where session_name like '%北京台%'"):
    print(" ", r["root"], r["date"], r["date_src"][:10], r["role"], r["session_name"], r["width"], r["height"])
    print("   ", r["path"])
print("=== 2026-01-05~02-15 role=me HEVC（前 30）===")
for r in c.execute("select date,session_name,width,path from photos where root like '%HEVC' and role='me' and date>='2026-01-05' and date<='2026-02-15' order by date limit 30"):
    print("  %s %-24s w=%-5s %s" % (r["date"], (r["session_name"] or "")[:24], r["width"], r["path"].split("\\")[-1]))
