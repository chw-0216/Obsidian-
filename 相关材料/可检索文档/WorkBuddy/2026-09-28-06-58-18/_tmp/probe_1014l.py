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
T30=int(time.mktime(time.strptime('2026-09-14','%Y-%m-%d')))
T60=int(time.mktime(time.strptime('2026-08-15','%Y-%m-%d')))

def search(kw, since=None, limit=20, sess=None):
    p('  --- %s ---'%kw)
    if sess:
        sql="select ts,role,substr(content,1,110) from messages where session_key=? and content like ?"
        args=[sess,'%'+kw+'%']
    else:
        sql="select session_key,ts,role,substr(content,1,100) from messages where content like ?"
        args=['%'+kw+'%']
    if since:
        sql+=" and ts>=?"; args.append(since)
    sql+=" order by ts desc limit %d"%limit
    rows=d.execute(sql,args).fetchall()
    if not rows: p('     (0)')
    for r in rows:
        if sess: p('   %s [%s] %s'%(ts2s(r[0]),r[1],r[2]))
        else: p('   %s %s [%s] %s'%((r[0] or '')[:24],ts2s(r[1]),r[2],r[3]))

p('######## A. 发布会 ########')
search('发布会', T30, 25)
p()
p('######## B. 吕越 ########')
search('吕越', None, 25)
p()
p('######## C. 星球 / 科普展 ########')
search('星球', T60, 15)
search('科普', T60, 15)
p()
p('######## D. 马?泽 ########')
for kw in ('马宇泽','马钰泽','马雨泽','马煜泽','马玉泽','马禹泽','马域泽'):
    search(kw, None, 10)
p()
p('######## E. 讲座 ########')
search('讲座', T30, 25)
p()
p('######## F. 种草 / 公众号 ########')
search('种草', T60, 20)
search('公众号', T30, 15)
p()
p('######## G. 何一沙 ########')
search('何一沙', None, 20)
p()
p('######## H. 美术馆（近 30 天）########')
search('美术馆', T30, 30)
p()
p('######## I. 实习（近 30 天）########')
search('实习', T30, 20)
p()
p('######## J. 陈晔会话（deerluna）近 45 条 ########')
for r in d.execute("select ts,role,substr(content,1,110) from messages where session_key='deerluna' order by ts desc limit 45"):
    p('   %s [%s] %s'%(ts2s(r[0]),r[1],r[2]))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1014l.txt','w',encoding='utf-8').write('\n'.join(out))
print('DONE',len(out))
