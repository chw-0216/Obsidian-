# -*- coding: utf-8 -*-
import sqlite3, io, time
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
out=[]
def p(*a): out.append(' '.join(str(x) for x in a))
def ts2s(t):
    try: return time.strftime('%Y-%m-%d %H:%M', time.localtime(int(t)))
    except Exception: return str(t)
d=sqlite3.connect(IDX)
p('#### 王利敏 a35599192 全部 ####')
rows=d.execute("select ts,role,substr(content,1,120) from messages where session_key='a35599192' order by ts").fetchall()
p('   共 %d 条'%len(rows))
for r in rows: p('   %s [%s] %s'%(ts2s(r[0]),r[1],r[2]))
p()
p('#### 李老师 guo647789 全部 ####')
rows=d.execute("select ts,role,substr(content,1,140) from messages where session_key='guo647789' order by ts").fetchall()
p('   共 %d 条'%len(rows))
for r in rows: p('   %s [%s] %s'%(ts2s(r[0]),r[1],r[2]))
p()
p('#### 全库「周五」「周五上午」（近 30 天）####')
T30=int(time.mktime(time.strptime('2026-09-14','%Y-%m-%d')))
for kw in ('周五','星期五'):
    rows=d.execute("select session_key,ts,role,substr(content,1,110) from messages where content like ? and ts>=? order by ts desc limit 15",('%'+kw+'%',T30)).fetchall()
    p('  --- %s: %d ---'%(kw,len(rows)))
    for r in rows: p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))
io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1014o.txt','w',encoding='utf-8').write('\n'.join(out))
print('DONE',len(out))
