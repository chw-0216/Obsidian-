# -*- coding: utf-8 -*-
import sqlite3, sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = sqlite3.connect("file:" + r"C:/Users/wardc/WorkBuddy AI/2026-09-28-06-58-18/_tmp/batch/batch.sqlite".replace("\\","/") + "?mode=ro", uri=True)
c.row_factory = sqlite3.Row
print("=== 朋友圈 2026-04-20~05-20 ===")
for r in c.execute("select date,width,height,bytes,note,path from photos where root='朋友圈' and date>='2026-04-20' and date<='2026-05-20' order by date"):
    print("  %s %sx%s %6.1fKB %s" % (r["date"], r["width"], r["height"], (r["bytes"] or 0)/1024, (r["note"] or "")[:40]))
    print("       ", r["path"])
