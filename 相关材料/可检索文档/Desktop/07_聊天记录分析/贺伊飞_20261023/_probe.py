# -*- coding: utf-8 -*-
"""只读探测：索引库概况 + 定位 yifei 会话"""
import sqlite3, datetime, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
c = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
c.execute('PRAGMA query_only=ON')

def ts2s(t):
    try:
        return datetime.datetime.fromtimestamp(int(t), tz=datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return str(t)

print('== 索引概况 ==')
print('messages:', c.execute('select count(*) from messages').fetchone()[0])
print('sessions:', c.execute('select count(*) from sessions').fetchone()[0])
print('max_ts:', c.execute('select max(ts) from messages').fetchone()[0], ts2s(c.execute('select max(ts) from messages').fetchone()[0]))
print('min_ts:', c.execute('select min(ts) from messages').fetchone()[0], ts2s(c.execute('select min(ts) from messages').fetchone()[0]))

print('\n== 名称含 伊飞/yifei/一飞 的会话 ==')
rows = c.execute("""select talker, display_name, session_type, message_count, first_ts, last_ts
                    from sessions
                    where display_name like '%伊飞%' or display_name like '%yifei%'
                       or display_name like '%一飞%' or display_name like '%亦飞%'
                       or display_name like '%逸飞%' or talker like '%hyf%'
                    order by message_count desc""").fetchall()
for r in rows:
    print(r[0], '|', r[1], '|', r[2], '|', r[3], '条 |', ts2s(r[4]), '->', ts2s(r[5]))

print('\n== 名称含 飞 的私聊会话（前 40） ==')
rows = c.execute("""select talker, display_name, message_count, last_ts from sessions
                    where display_name like '%飞%' and (session_type is null or session_type != 2)
                    order by message_count desc limit 40""").fetchall()
for r in rows:
    print(r[0], '|', r[1], '|', r[2], '条 |', ts2s(r[3]))

print('\n== 贺伊飞会话统计 ==')
T = 'hyf782877122'
q = c.execute('select count(*), min(ts), max(ts) from messages where session_key=?', (T,)).fetchone()
print('count/min/max:', q[0], ts2s(q[1]), '->', ts2s(q[2]))
print('\n-- role x type --')
for r in c.execute('select role, type, count(*) from messages where session_key=? group by role,type order by count(*) desc', (T,)):
    print(r)
print('\n-- 按月 --')
for r in c.execute("select substr(time_text,1,7) m, count(*) from messages where session_key=? group by m order by m", (T,)):
    print(r)
print('\n-- sessions 表行 --')
for r in c.execute('select * from sessions where talker=?', (T,)):
    print(r)
