# -*- coding: utf-8 -*-
"""探查 06/07/08 三段可用照片：厦门集美 / 北京台实习 / 数字人"""
import sqlite3, os, sys, datetime
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DB = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\batch\batch.sqlite"
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

def ts2d(ts):
    if not ts: return ""
    try:
        return datetime.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d")
    except Exception:
        return ""

def show(title, sql, args=()):
    print("\n" + "="*70)
    print(title)
    print("="*70)
    rows = list(c.execute(sql, args))
    if not rows:
        print("  （无）")
        return rows
    for r in rows:
        print("  %-6s %-11s w=%-5s %-11s %-9s %-22s %s" % (
            r["root"], ts2d(r["ts"]), r["width"], str(r["role"] or "-"),
            (r["date_src"] or "")[:8], (r["session_name"] or "-")[:22],
            os.path.basename(r["path"] or "")[:40]))
    return rows

# 可用池门槛
USABLE = "width>=800 and bytes>=80000"

# ---- 06 厦门集美 2026-04-20 ~ 2026-05-15
show("06 厦门集美｜时间窗 2026-04-20~05-15（可用池）",
     "select * from photos where %s and date>='2026-04-20' and date<='2026-05-15' order by date, width desc limit 40" % USABLE)

show("06 厦门｜会话名含 厦门/集美/版画（不限时间）",
     "select * from photos where %s and (session_name like '%%厦门%%' or session_name like '%%集美%%') order by date desc limit 30" % USABLE)

# ---- 07 北京台实习 2026-01-01 ~ 2026-02-20
show("07 北京台｜时间窗 2026-01-01~02-20（可用池）",
     "select * from photos where %s and date>='2026-01-01' and date<='2026-02-20' order by date, width desc limit 40" % USABLE)

show("07 北京台｜会话名含 北京台/广电/短剧/AI",
     "select * from photos where %s and (session_name like '%%北京台%%' or session_name like '%%广播%%' or session_name like '%%短剧%%') order by date desc limit 30" % USABLE)

# ---- 08 数字人 AI产物
show("08 数字人｜AI产物桶（可用池）",
     "select * from photos where %s and root='AI产物' order by date desc, width desc limit 40" % USABLE)

show("08 数字人｜会话名含 数字人/知津/Hyper3D/交互",
     "select * from photos where %s and (session_name like '%%数字人%%' or session_name like '%%知津%%' or session_name like '%%Hyper3D%%') order by date desc limit 30" % USABLE)

print("\n\n===== 可用池总体（按 root / 月份）=====")
for r in c.execute("select root, substr(date,1,7) m, count(*) n from photos where %s group by root, m order by root, m" % USABLE):
    print("  %-14s %s  %d" % (r[0], r[1], r[2]))
