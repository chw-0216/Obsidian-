# -*- coding: utf-8 -*-
"""只读：10-23 母亲会话 + 读书周/中传相关检索"""
import sqlite3, datetime, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
c = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
c.execute('PRAGMA query_only=ON')
TZ = datetime.timezone(datetime.timedelta(hours=8))
def ts(t): return datetime.datetime.fromtimestamp(int(t), tz=TZ).strftime('%Y-%m-%d %H:%M:%S')
D23 = int(datetime.datetime(2026,10,23,0,0,tzinfo=TZ).timestamp())
D22 = int(datetime.datetime(2026,10,22,0,0,tzinfo=TZ).timestamp())

print('===== 母亲 10-23 消息 =====')
for r in c.execute("select ts, role, type, content from messages where session_key='wxid_1wa75s1kze3o22' and ts>=? order by ts", (D23,)):
    print(f'[{ts(r[0])}] {r[1]}/{r[2]} | {(r[3] or "")[:400]}')

print('\n===== 10-22 起 含「读书周/李老师/海燕/王利敏/中传/交互」的消息（跨会话，限 120） =====')
n=0
for r in c.execute("""select m.session_key, s.display_name, m.ts, m.role, m.content from messages m
                      left join sessions s on s.talker=m.session_key
                      where m.ts>=? and (m.content like '%读书周%' or m.content like '%李老师%'
                        or m.content like '%海燕%' or m.content like '%王利敏%' or m.content like '%中传%'
                        or m.content like '%交互技术%')
                      order by m.ts""", (D22,)):
    content=(r[4] or '').replace('\n',' ')
    if len(content)>260: content=content[:260]+'…'
    print(f'[{ts(r[2])}] {r[0]} | {r[1]} | {r[3]} | {content}')
    n+=1
    if n>=120: break

print('\n===== 名称含 交互/中传/课程/技术课 的会话 =====')
for r in c.execute("""select talker, display_name, session_type, message_count, first_ts, last_ts from sessions
                      where display_name like '%交互%' or display_name like '%中传%' or display_name like '%技术课%'
                         or display_name like '%课程%' order by message_count desc limit 30"""):
    print(f'{r[0]} | {r[1]} | type={r[2]} | {r[3]} 条 | {ts(r[4])} -> {ts(r[5])}')
