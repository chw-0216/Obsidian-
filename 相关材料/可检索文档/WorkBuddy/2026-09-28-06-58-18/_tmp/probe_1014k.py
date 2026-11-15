# -*- coding: utf-8 -*-
import sqlite3, io, time
IDX = r'C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite'
out=[]
def p(*a): out.append(' '.join(str(x) for x in a))
def ts2s(t):
    try: return time.strftime('%Y-%m-%d %H:%M', time.localtime(int(t)))
    except Exception: return str(t)
d=sqlite3.connect(IDX)
T1=int(time.mktime(time.strptime('2026-09-10','%Y-%m-%d')))
T2=int(time.mktime(time.strptime('2026-09-14','%Y-%m-%d')))
p('#### 母亲会话 2026-09-10~14 全部（wxid_1wa75s1kze3o22）####')
for r in d.execute("select ts,role,substr(content,1,120) from messages where session_key='wxid_1wa75s1kze3o22' and ts>=? and ts<? order by ts",(T1,T2)):
    p('   %s [%s] %s'%(ts2s(r[0]),r[1],r[2]))
p()
p('#### 全库搜「动画学院」「不要说是央美」（不限时间）####')
for kw in ('动画学院','不要说是央美','不要说你是央美','央美的'):
    rows=d.execute("select session_key,ts,role,substr(content,1,100) from messages where content like ? order by ts desc limit 10",('%'+kw+'%',)).fetchall()
    p('  --- %s: %d ---'%(kw,len(rows)))
    for r in rows: p('   %s %s [%s] %s'%((r[0] or '')[:22],ts2s(r[1]),r[2],r[3]))
p()
p('#### guo647789 contact ####')
import os
DEC = r'C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted'
c=sqlite3.connect(os.path.join(DEC,'contact','contact.db'))
for r in c.execute("select username,alias,remark,nick_name,quan_pin from contact where username like '%guo647789%'"):
    p('   %s'%(str(r),))
io.open(r'C:/Users/wardc/WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1014k.txt','w',encoding='utf-8').write('\n'.join(out))
print('DONE',len(out))
