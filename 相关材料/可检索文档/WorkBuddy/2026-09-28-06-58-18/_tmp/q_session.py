# -*- coding: utf-8 -*-
import sqlite3, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = sqlite3.connect("file:" + r"C:/Users/wardc/WorkBuddy AI/2026-09-28-06-58-18/_tmp/batch/batch.sqlite".replace("\\","/") + "?mode=ro", uri=True)
c.row_factory = sqlite3.Row
for kw in ["北京台","梅宸羽","厦门","集美"]:
    print("="*70); print("会话名含 %s" % kw); print("="*70)
    rows = list(c.execute("select root,date,date_src,role,session_name,width,height,path from photos where session_name like ? order by date desc limit 25", ("%"+kw+"%",)))
    print("  %d 条" % len(rows))
    for r in rows:
        print("   %-12s %-11s %-6s w=%-5s %-24s %s" % (r["root"], r["date"], str(r["role"]), r["width"], (r["session_name"] or "")[:24], os.path.basename(r["path"])[:34]))
