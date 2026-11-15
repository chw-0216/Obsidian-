# -*- coding: utf-8 -*-
"""只读：尚弋斐 私聊全文 + 会话统计"""
import sqlite3, datetime, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
c = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True); c.execute('PRAGMA query_only=ON')
TZ = datetime.timezone(datetime.timedelta(hours=8))
def ts(t): return datetime.datetime.fromtimestamp(int(t), tz=TZ).strftime('%Y-%m-%d %H:%M:%S')
T='shenaijj520520'
print('== sessions 行 ==')
print(c.execute('select * from sessions where talker=?',(T,)).fetchone())
q=c.execute('select count(*),min(ts),max(ts) from messages where session_key=?',(T,)).fetchone()
print('count/min/max:', q[0], ts(q[1]), '->', ts(q[2]))
print('\n-- role x type --')
for r in c.execute('select role,type,count(*) from messages where session_key=? group by role,type order by count(*) desc',(T,)):
    print(r)
print('\n== 全文 ==')
for r in c.execute('select ts, role, type, content from messages where session_key=? order by ts, id',(T,)):
    content=(r[3] or '').replace('\n','\\n')
    if len(content)>1200: content=content[:1200]+f'…[原长{len(r[3])}]'
    print(f'[{ts(r[0])}] {r[1]}/{r[2]} | {content}')
