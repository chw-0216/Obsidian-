# -*- coding: utf-8 -*-
import sqlite3, io, time, os
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
DEC = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
out=[]
def p(*a): out.append(' '.join(str(x) for x in a))
def ts2s(t):
    try: return time.strftime('%Y-%m-%d %H:%M', time.localtime(int(t)))
    except Exception: return str(t)
d=sqlite3.connect(IDX)
T7=int(time.mktime(time.strptime('2026-10-07','%Y-%m-%d')))
T30=int(time.mktime(time.strptime('2026-09-14','%Y-%m-%d')))

p('#### 1. 全库「助教」####')
for r in d.execute("select session_key,ts,role,substr(content,1,120) from messages where content like '%助教%' order by ts desc limit 20"):
    p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))
p()
p('#### 2. 近 7 天 含「周六」或「下午」+「报」####')
for kw in ('周六','报名','填写','研讨会','论坛','工作坊','学术'):
    rows=d.execute("select session_key,ts,role,substr(content,1,100) from messages where content like ? and ts>=? order by ts desc limit 10",('%'+kw+'%',T7)).fetchall()
    p('  --- %s: %d ---'%(kw,len(rows)))
    for r in rows: p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))
p()
p('#### 3. 公众号 近 14 天 含「讲座/论坛/工作坊/研讨会/沙龙」####')
T14=int(time.mktime(time.strptime('2026-09-30','%Y-%m-%d')))
for kw in ('讲座','论坛','工作坊','研讨会','沙龙','对谈'):
    rows=d.execute("select session_key,ts,substr(content,1,110) from messages where session_key like 'gh_%' and content like ? and ts>=? order by ts desc limit 12",('%'+kw+'%',T14)).fetchall()
    p('  --- %s: %d ---'%(kw,len(rows)))
    for r in rows: p('   %s %s %s'%((r[0] or '')[:24],ts2s(r[1]),r[2]))
p()
p('#### 4. 全库「岳」（不限）####')
for r in d.execute("select session_key,ts,role,substr(content,1,100) from messages where content like '%岳%' order by ts desc limit 20"):
    p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))
p()
p('#### 5. 近 7 天「吕越」+「闭展/延展」####')
for kw in ('吕越','延展','闭展','倒计时'):
    rows=d.execute("select session_key,ts,role,substr(content,1,110) from messages where content like ? order by ts desc limit 8",('%'+kw+'%',)).fetchall()
    p('  --- %s: %d ---'%(kw,len(rows)))
    for r in rows: p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))
p()
p('#### 6. 群聊里含「美术馆」的 chatroom 分布（近 30 天）####')
for r in d.execute("select session_key,count(*) from messages where session_key like '%@chatroom' and content like '%美术馆%' and ts>=? group by session_key order by 2 desc limit 15",(T30,)):
    p('   %s : %s'%(r[0],r[1]))
p()
p('#### 7. 近 3 天 含「发布会」或「媒体部」或「何主任」####')
T3=int(time.mktime(time.strptime('2026-10-12','%Y-%m-%d')))
for kw in ('发布会','媒体部','何主任','何老师','视频'):
    rows=d.execute("select session_key,ts,role,substr(content,1,110) from messages where content like ? and ts>=? order by ts desc limit 12",('%'+kw+'%',T3)).fetchall()
    p('  --- %s: %d ---'%(kw,len(rows)))
    for r in rows: p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))
p()
p('#### 8. 陈晔会话 10-14 全部（含图片原始 xml）####')
for r in d.execute("select ts,role,content from messages where session_key='deerluna' and ts>=? order by ts",(T3,)):
    p('   %s [%s] %s'%(ts2s(r[0]),r[1],(r[2] or '')[:600]))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1014n.txt','w',encoding='utf-8').write('\n'.join(out))
print('DONE',len(out))
