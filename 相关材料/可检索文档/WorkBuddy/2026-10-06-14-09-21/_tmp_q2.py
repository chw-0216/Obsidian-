# -*- coding: utf-8 -*-
import sqlite3
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
c = con.cursor()
print("== 井邻/洞台 关键词命中的会话 TOP（剔除刷屏群）==")
active = set(r[0] for r in c.execute("select distinct session_key from messages where role='me'"))
rows = c.execute("""select session_key, count(*) n,
  datetime(min(ts),'unixepoch','localtime'), datetime(max(ts),'unixepoch','localtime')
  from messages
  where content like '%井邻%' or content like '%洞台%' or content like '%乡村美育%'
     or content like '%美育工作站%' or content like '%驻村%'
  group by session_key order by n desc""").fetchall()
for sk,n,a,b in rows:
    if sk.endswith('@chatroom') and sk not in active:
        tag='[刷屏群剔除]'
    else:
        tag=''
    dn = c.execute("select display_name,session_type from sessions where talker=?",(sk,)).fetchone()
    print("  %-42s | %-8s | %5d | %s ~ %s %s" % ((dn[0] if dn else '?')[:42], (dn[1] if dn else '?'), n, a[:10], b[:10], tag))
print()
print("== 陈晔候选（按名匹配）==")
for t,dn,st,mc,lt in c.execute("select talker,display_name,session_type,message_count,last_ts from sessions").fetchall():
    if dn and ('陈晔' in dn or '陈老师' in dn or 'deerluna' in dn.lower()):
        print("  %-30s | %s | %s | %s" % (dn, st, mc, t))
