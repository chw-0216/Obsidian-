# -*- coding: utf-8 -*-
"""只读补齐：10-23 当天上下文 + 中传线 + 可能的发布会群"""
import sqlite3, datetime, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
c = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
c.execute('PRAGMA query_only=ON')
TZ = datetime.timezone(datetime.timedelta(hours=8))
def ts(t): return datetime.datetime.fromtimestamp(int(t), tz=TZ).strftime('%Y-%m-%d %H:%M:%S')

def day_start(s):
    dt = datetime.datetime.strptime(s, '%Y-%m-%d').replace(tzinfo=TZ)
    return int(dt.timestamp())

D23 = day_start('2026-10-23')
D22 = day_start('2026-10-22')
D20 = day_start('2026-10-20')

print('===== 10-23 当天所有会话的条数（按会话聚合） =====')
for r in c.execute("""select m.session_key, s.display_name, s.session_type, count(*) n, min(m.ts), max(m.ts)
                      from messages m left join sessions s on s.talker=m.session_key
                      where m.ts>=? group by m.session_key order by n desc""", (D23,)):
    print(f'{r[0]} | {r[1]} | type={r[2]} | {r[3]} 条 | {ts(r[4])} -> {ts(r[5])}')

print('\n===== 10-22 起，内容含 美术馆/发布会/开幕/拍摄 的消息（限 200 条） =====')
seen = 0
for r in c.execute("""select m.session_key, s.display_name, m.ts, m.role, m.content
                      from messages m left join sessions s on s.talker=m.session_key
                      where m.ts>=? and (m.content like '%美术馆%' or m.content like '%发布会%'
                        or m.content like '%开幕%' or m.content like '%拍摄%' or m.content like '%贺伊飞%'
                        or m.content like '%贺哥%')
                      order by m.ts""", (D22,)):
    content = (r[4] or '').replace('\n', ' ')
    if len(content) > 260: content = content[:260] + '…'
    print(f'[{ts(r[2])}] {r[0]} | {r[1]} | {r[3]} | {content}')
    seen += 1
    if seen >= 200: break
print('(命中', seen, '条)')

print('\n===== 10-20 起 名称含 央美/媒体/宣传/开幕/发布 的会话 =====')
for r in c.execute("""select talker, display_name, session_type, message_count, first_ts, last_ts from sessions
                      where display_name like '%央美%' or display_name like '%媒体%' or display_name like '%宣传%'
                         or display_name like '%开幕%' or display_name like '%发布%' or display_name like '%美术馆%'
                      order by last_ts desc limit 40"""):
    print(f'{r[0]} | {r[1]} | type={r[2]} | {r[3]} 条 | {ts(r[4])} -> {ts(r[5])}')

print('\n===== 10-20 起 新建/活跃的空名会话（可能是新群） =====')
for r in c.execute("""select talker, display_name, session_type, message_count, first_ts, last_ts from sessions
                      where first_ts>=? order by first_ts desc limit 40""", (D20,)):
    print(f'{r[0]} | {r[1]} | type={r[2]} | {r[3]} 条 | {ts(r[4])} -> {ts(r[5])}')

print('\n===== 中传线：海燕/王利敏 10-20 起 =====')
for tk in ('guo647789', 'a35599192'):
    print(f'--- {tk} ---')
    for r in c.execute("select ts, role, type, content from messages where session_key=? and ts>=? order by ts", (tk, D20)):
        content = (r[3] or '').replace('\n', ' ')
        if len(content) > 300: content = content[:300] + '…'
        print(f'[{ts(r[0])}] {r[1]}/{r[2]} | {content}')
