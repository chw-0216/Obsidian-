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

p('#### 全库搜「小王阿姨」「阿姨」####')
for kw in ('小王阿姨','阿姨'):
    rows=d.execute("select session_key,ts,role,substr(content,1,80) from messages where content like ? order by ts desc limit 12",('%'+kw+'%',)).fetchall()
    p('  --- %s: %d ---'%(kw,len(rows)))
    for r in rows: p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))

p()
p('#### 王利敏会话（a35599192）最近 50 条 ####')
for r in d.execute("select ts,role,substr(content,1,90) from messages where session_key='a35599192' order by ts desc limit 50"):
    p('   %s [%s] %s'%(ts2s(r[0]),r[1],r[2]))

p()
p('#### 王利敏 会话内搜「入校/进校/预约/报备/通行/门/身份证」####')
for kw in ('入校','进校','预约','报备','通行','门','身份证','车','证'):
    rows=d.execute("select ts,role,substr(content,1,80) from messages where session_key='a35599192' and content like ? order by ts desc limit 8",('%'+kw+'%',)).fetchall()
    if rows:
        p('  --- %s: %d ---'%(kw,len(rows)))
        for r in rows: p('   %s [%s] %s'%(ts2s(r[0]),r[1],r[2]))

p()
p('#### 全库近 60 天搜「入校」「进校」（前 20）####')
T60=int(time.mktime(time.strptime('2026-08-15','%Y-%m-%d')))
for kw in ('入校','进校'):
    rows=d.execute("select session_key,ts,role,substr(content,1,80) from messages where content like ? and ts>=? order by ts desc limit 20",('%'+kw+'%',T60)).fetchall()
    p('  --- %s: %d ---'%(kw,len(rows)))
    for r in rows: p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))

p()
p('#### contact 表结构 ####')
cols=[x[1] for x in c.execute("PRAGMA table_info(contact)")]
p('   cols: %s'%cols)
p('#### 王利敏 contact 信息 ####')
try:
    for r in c.execute("select * from contact where username like '%a35599192%' or remark like '%王利敏%' or remark like '%阿姨%'"):
        p('   %s'%(str(r)[:400],))
except Exception as e:
    p('   ERR %s'%e)

p()
p('#### 全库搜「中传」「传媒大学」（近 90 天 · 前 25）####')
T90=int(time.mktime(time.strptime('2026-07-15','%Y-%m-%d')))
for r in d.execute("select session_key,ts,role,substr(content,1,80) from messages where (content like '%中传%' or content like '%传媒大学%') and ts>=? order by ts desc limit 25",(T90,)):
    p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))

io.open(r'C:/Users/wardc/WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1014i.txt','w',encoding='utf-8').write('\n'.join(out))
print('DONE',len(out))
