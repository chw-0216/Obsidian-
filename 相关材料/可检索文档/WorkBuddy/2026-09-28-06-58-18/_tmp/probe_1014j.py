# -*- coding: utf-8 -*-
import sqlite3, io, time
IDX = r'C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite'
out=[]
def p(*a): out.append(' '.join(str(x) for x in a))
def ts2s(t):
    try: return time.strftime('%Y-%m-%d %H:%M', time.localtime(int(t)))
    except Exception: return str(t)
d=sqlite3.connect(IDX)

p('#### 李老师（guo647789）全部 ####')
rows=d.execute("select ts,role,substr(content,1,110) from messages where session_key='guo647789' order by ts").fetchall()
p('   共 %d 条'%len(rows))
for r in rows: p('   %s [%s] %s'%(ts2s(r[0]),r[1],r[2]))

p()
p('#### 王利敏会话 搜「课」（最近 15）####')
for r in d.execute("select ts,role,substr(content,1,110) from messages where session_key='a35599192' and content like '%课%' order by ts desc limit 15"):
    p('   %s [%s] %s'%(ts2s(r[0]),r[1],r[2]))

p()
p('#### 王利敏会话 首末 ####')
r=d.execute("select min(ts),max(ts),count(*) from messages where session_key='a35599192'").fetchone()
p('   %s -> %s  共 %d 条'%(ts2s(r[0]),ts2s(r[1]),r[2]))

p()
p('#### 公众号 gh_71133962d203（访客入校系统）最近 20 条 ####')
for r in d.execute("select ts,role,substr(content,1,120) from messages where session_key='gh_71133962d203' order by ts desc limit 20"):
    p('   %s [%s] %s'%(ts2s(r[0]),r[1],r[2]))

p()
p('#### 2026-10-09 前后 我发/收 全部含「中传/课/入校/预约/李老师/王」 ####')
T1=int(time.mktime(time.strptime('2026-10-08','%Y-%m-%d')))
T2=int(time.mktime(time.strptime('2026-10-14','%Y-%m-%d')))
for kw in ('入校','预约','李老师','中传','上课'):
    rows=d.execute("select session_key,ts,role,substr(content,1,90) from messages where content like ? and ts>=? and ts<? order by ts",('%'+kw+'%',T1,T2)).fetchall()
    p('  --- %s: %d ---'%(kw,len(rows)))
    for r in rows: p('   %s %s [%s] %s'%((r[0] or '')[:22],ts2s(r[1]),r[2],r[3]))

io.open(r'C:/Users/wardc/WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1014j.txt','w',encoding='utf-8').write('\n'.join(out))
print('DONE',len(out))
