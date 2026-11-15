# -*- coding: utf-8 -*-
import sqlite3, io, time, os
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
DEC = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
CON = os.path.join(DEC,'contact','contact.db')
out=[]
def p(*a): out.append(' '.join(str(x) for x in a))
def ts2s(t):
    try: return time.strftime('%Y-%m-%d %H:%M', time.localtime(int(t)))
    except Exception: return str(t)
d=sqlite3.connect(IDX); c=sqlite3.connect(CON)
T3=int(time.mktime(time.strptime('2026-10-12','%Y-%m-%d')))

p('#### 0. 关键联系人 contact ####')
for u in ('shuixiaoxie','huxiaomi123','wxid_87gthrpz43j121'):
    for r in c.execute("select username,alias,remark,nick_name from contact where username=?",(u,)):
        p('   %s'%(str(r),))
p('   -- 搜 remark 含 岳/沙/马钰 --')
try:
    for r in c.execute("select username,alias,remark,nick_name from contact where remark like '%岳%' or remark like '%何一沙%' or remark like '%马钰%' limit 20"):
        p('   %s'%(str(r),))
except Exception as e: p('   ERR %s'%e)

p()
p('#### 1. 全库「寻星」「系外行星」####')
for kw in ('寻星','系外行星','星球'):
    p('  --- %s ---'%kw)
    for r in d.execute("select session_key,ts,role,substr(content,1,110) from messages where content like ? order by ts desc limit 12",('%'+kw+'%',)):
        p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))

p()
p('#### 2. 央美美术馆公众号 gh_615f56b92184 最近 25 条 ####')
for r in d.execute("select ts,role,substr(content,1,140) from messages where session_key='gh_615f56b92184' order by ts desc limit 25"):
    p('   %s [%s] %s'%(ts2s(r[0]),r[1],r[2]))

p()
p('#### 3. 近 3 天 全部含「展」####')
for r in d.execute("select session_key,ts,role,substr(content,1,110) from messages where content like '%展%' and ts>=? order by ts desc limit 40",(T3,)):
    p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))

p()
p('#### 4. 近 3 天 我发的全部（role=me）####')
for r in d.execute("select session_key,ts,substr(content,1,110) from messages where role='me' and ts>=? order by ts desc limit 60",(T3,)):
    p('   %s %s %s'%((r[0] or '')[:24],ts2s(r[1]),r[2]))

p()
p('#### 5. 群 7416567525 是什么 ####')
for r in c.execute("select username,remark,nick_name from contact where username='7416567525@chatroom'"):
    p('   %s'%(str(r),))
for r in d.execute("select ts,substr(content,1,90) from messages where session_key='7416567525@chatroom' order by ts desc limit 6"):
    p('   %s %s'%(ts2s(r[0]),r[1]))

p()
p('#### 6. 马钰泽 私聊？全库含「马钰泽」的 session 分布 ####')
for r in d.execute("select session_key,count(*) from messages where content like '%马钰泽%' group by session_key"):
    p('   %s : %s'%(r[0],r[1]))

p()
p('#### 7. 近 30 天「视频号/短视频/剪辑/拍摄/短视频」####')
T30=int(time.mktime(time.strptime('2026-09-14','%Y-%m-%d')))
for kw in ('视频号','短视频','剪辑','拍摄','成片','横屏','竖屏'):
    rows=d.execute("select session_key,ts,role,substr(content,1,90) from messages where content like ? and ts>=? order by ts desc limit 8",('%'+kw+'%',T30)).fetchall()
    p('  --- %s: %d ---'%(kw,len(rows)))
    for r in rows: p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))

p()
p('#### 8. shuixiaoxie 全部 ####')
rows=d.execute("select ts,role,substr(content,1,120) from messages where session_key='shuixiaoxie' order by ts").fetchall()
p('   共 %d 条'%len(rows))
for r in rows: p('   %s [%s] %s'%(ts2s(r[0]),r[1],r[2]))

p()
p('#### 9. huxiaomi123 全部 ####')
rows=d.execute("select ts,role,substr(content,1,120) from messages where session_key='huxiaomi123' order by ts").fetchall()
p('   共 %d 条'%len(rows))
for r in rows: p('   %s [%s] %s'%(ts2s(r[0]),r[1],r[2]))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1014m.txt','w',encoding='utf-8').write('\n'.join(out))
print('DONE',len(out))
