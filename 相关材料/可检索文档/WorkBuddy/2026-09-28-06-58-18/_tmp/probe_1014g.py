# -*- coding: utf-8 -*-
import sqlite3, io, time
IDX = r'C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite'
out=[]
def p(*a): out.append(' '.join(str(x) for x in a))
def ts2s(t):
    try: return time.strftime('%Y-%m-%d %H:%M', time.localtime(int(t)))
    except Exception: return str(t)
d=sqlite3.connect(IDX)
TAL='wxid_wdnk6ue9kiyn22'

p('#### 笑一会话搜「专业/方向/论文/研究/选题/社会美育/乡村/支教/公益」####')
for kw in ('专业','方向','论文','研究','选题','社会美育','乡村','支教','公益','导师','老师','毕业'):
    rows=d.execute("select ts,role,substr(content,1,70) from messages where session_key=? and content like ? order by ts desc limit 6",(TAL,'%'+kw+'%')).fetchall()
    if rows:
        p('  --- %s: %d ---'%(kw,len(rows)))
        for r in rows: p('   %s [%s] %s'%(ts2s(r[0]),r[1],r[2]))

p()
p('#### 笑一 我发 vs 她发 总量 + 首末 ####')
r=d.execute("select role,count(*) from messages where session_key=? group by role",(TAL,)).fetchall()
for x in r: p('   %s: %s'%(x[0],x[1]))
r=d.execute("select min(ts),max(ts) from messages where session_key=?",(TAL,)).fetchone()
p('   窗口 %s -> %s'%(ts2s(r[0]),ts2s(r[1])))

p()
p('#### 澜沧会话（deerluna=陈晔）最近 15 条 ####')
for r in d.execute("select ts,role,substr(content,1,80) from messages where session_key='deerluna' order by ts desc limit 15"):
    p('   %s [%s] %s'%(ts2s(r[0]),r[1],r[2]))

io.open(r'C:/Users/wardc/WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1014g.txt','w',encoding='utf-8').write('\n'.join(out))
print('DONE',len(out))
