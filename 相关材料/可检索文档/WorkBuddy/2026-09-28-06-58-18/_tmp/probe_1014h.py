# -*- coding: utf-8 -*-
import sqlite3, io, time, os
IDX = r'C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite'
DEC = r'C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted'
CON = os.path.join(DEC, 'contact', 'contact.db')
out=[]
def p(*a): out.append(' '.join(str(x) for x in a))
def ts2s(t):
    try: return time.strftime('%Y-%m-%d %H:%M', time.localtime(int(t)))
    except Exception: return str(t)
d=sqlite3.connect(IDX); c=sqlite3.connect(CON)
T30=int(time.mktime(time.strptime('2026-09-14','%Y-%m-%d')))

p('#### 近 30 天搜「美术馆」（前 25）####')
for r in d.execute("select session_key,ts,role,substr(content,1,70) from messages where content like '%美术馆%' and ts>=? order by ts desc limit 25",(T30,)):
    p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))

p()
p('#### 近 30 天搜「报道 / 报到」（前 20）####')
for kw in ('报道','报到'):
    rows=d.execute("select session_key,ts,role,substr(content,1,70) from messages where content like ? and ts>=? order by ts desc limit 20",('%'+kw+'%',T30)).fetchall()
    p('  --- %s: %d ---'%(kw,len(rows)))
    for r in rows: p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))

p()
p('#### 「何一沙」全库（前 15）####')
for r in d.execute("select session_key,ts,role,substr(content,1,70) from messages where content like '%何一沙%' order by ts desc limit 15"):
    p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))

p()
p('#### 「媒体部」全库（前 15）####')
for r in d.execute("select session_key,ts,role,substr(content,1,70) from messages where content like '%媒体部%' order by ts desc limit 15"):
    p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))

p()
p('#### 笑一 2026-10-09 起全部（按时间正序）####')
T9=int(time.mktime(time.strptime('2026-10-09','%Y-%m-%d')))
rows=d.execute("select ts,role,substr(content,1,80) from messages where session_key='wxid_wdnk6ue9kiyn22' and ts>=? order by ts",(T9,)).fetchall()
p('   共 %d 条'%len(rows))
for r in rows: p('   %s [%s] %s'%(ts2s(r[0]),r[1],r[2]))

p()
p('#### 近 30 天搜「实习」（前 20）####')
for r in d.execute("select session_key,ts,role,substr(content,1,70) from messages where content like '%实习%' and ts>=? order by ts desc limit 20",(T30,)):
    p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))

io.open(r'C:/Users/wardc/WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1014h.txt','w',encoding='utf-8').write('\n'.join(out))
print('DONE',len(out))
