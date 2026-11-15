# -*- coding: utf-8 -*-
import sqlite3, sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = sqlite3.connect("file:" + r"C:/Users/wardc/WorkBuddy AI/2026-09-28-06-58-18/_tmp/batch/batch.sqlite".replace("\\","/") + "?mode=ro", uri=True)
c.row_factory = sqlite3.Row
print("朋友圈 role=me 共", c.execute("select count(*) from photos where root='朋友圈' and role='me'").fetchone()[0])
for r in c.execute("select date,width,note,path from photos where root='朋友圈' and role='me' order by date desc"):
    print("  %s w=%-5s %s" % (r["date"], r["width"], (r["note"] or "")[:70]))
