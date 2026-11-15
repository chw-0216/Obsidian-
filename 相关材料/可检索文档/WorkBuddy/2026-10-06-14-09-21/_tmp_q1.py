# -*- coding: utf-8 -*-
import sqlite3
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
c = con.cursor()
print("== 全库水位 ==")
r = c.execute("select count(*), datetime(min(ts),'unixepoch','localtime'), datetime(max(ts),'unixepoch','localtime') from messages").fetchone()
print(" 条数 %d | %s → %s" % r)
print("== sessions 表结构 ==")
print([d[1] for d in c.execute("PRAGMA table_info(sessions)")])
print("== 井邻线候选会话（显示名匹配）==")
kw = ['井邻','洞台','美育','工作站','装置','陈晔','关宇','澜沧','支教','渤海']
rows = c.execute("select talker, display_name, session_type, message_count from sessions").fetchall()
for t,dn,st,mc in rows:
    dn = dn or ''
    if any(k in dn for k in kw):
        print("  %-40s | %-8s | %6s | %s" % (dn[:40], st, mc, t))
