# -*- coding: utf-8 -*-
"""同步后：验收 + 新消息抽取（ts > 20:07:45 的增量窗口）"""
import sqlite3, datetime, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
c = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True); c.execute('PRAGMA query_only=ON')
TZ = datetime.timezone(datetime.timedelta(hours=8))
def ts(t):
    if t is None: return '-'
    return datetime.datetime.fromtimestamp(int(t), tz=TZ).strftime('%Y-%m-%d %H:%M:%S')

PRE_MAX = 1792757265  # 2026-10-23 20:07:45 同步前最新
PRE_N = 403572

print('== 全库（同步后） ==')
n = c.execute('select count(*) from messages').fetchone()[0]
mx = c.execute('select max(ts) from messages').fetchone()[0]
print(f'messages={n} (delta {n-PRE_N})  latest={ts(mx)}')
print('FTS rows =', c.execute('select count(*) from messages_fts').fetchone()[0])

print('\n== 目标会话（同步后） ==')
targets = {
    'hyf782877122': '贺伊飞 Yifi',
    '19944550391@chatroom': 'CAFAM 媒体部群',
    'huxiaomi123': '何一沙',
    'shuixiaoxie': '岳老师',
    'liuyuhan1012': '刘宇晗',
    'guo647789': '海燕',
    'a35599192': '王利敏',
    'wxid_1wa75s1kze3o22': '母亲',
    'wxid_wdnk6ue9kiyn22': '笑一',
}
for tk, name in targets.items():
    r = c.execute('select count(*), min(ts), max(ts) from messages where session_key=?', (tk,)).fetchone()
    miss = c.execute('select count(*) from messages m left join messages_fts f on f.rowid=m.id where m.session_key=? and f.rowid is null', (tk,)).fetchone()[0]
    orph = c.execute('select count(*) from messages_fts f left join messages m on m.id=f.rowid where f.session_key=? and m.id is null', (tk,)).fetchone()[0]
    mism = c.execute('select count(*) from messages m join messages_fts f on f.rowid=m.id where m.session_key=? and (COALESCE(m.content,\'\')<>COALESCE(f.content,\'\') or COALESCE(m.sender,\'\')<>COALESCE(f.sender,\'\') or COALESCE(m.session_key,\'\')<>COALESCE(f.session_key,\'\'))', (tk,)).fetchone()[0]
    print(f'{tk:24s} {name:12s} 条数={r[0]:5d} 最新={ts(r[2])}  FTS缺失={miss} 孤儿={orph} 错配={mism}')

print('\n== 新消息（ts > 20:07:45） ==')
rows = c.execute("""select m.ts, m.session_key, s.display_name, m.role, m.type, m.content
                    from messages m left join sessions s on s.talker=m.session_key
                    where m.ts > ? order by m.ts""", (PRE_MAX,)).fetchall()
print('条数:', len(rows))
for r in rows:
    content = (r[5] or '').replace('\n', ' ')
    if len(content) > 300: content = content[:300] + '…'
    print(f'[{ts(r[0])}] {r[1]} | {r[2]} | {r[3]}/{r[4]} | {content}')

print('\n== 所有 10-23 19:00 后变更的会话（按最后消息） ==')
for r in c.execute("""select session_key, display_name, count(*), max(ts) from messages m
                      left join sessions s on s.talker=m.session_key
                      where m.ts >= ? group by session_key order by max(ts) desc limit 30""",
                   (int(datetime.datetime(2026,10,23,19,0,tzinfo=TZ).timestamp()),)):
    print(f'{r[0]} | {r[1]} | {r[2]} 条 | 最新 {ts(r[3])}')
