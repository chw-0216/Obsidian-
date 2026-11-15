# -*- coding: utf-8 -*-
"""同步后：按 id 增量抽取新消息 + 贺伊飞全文 + FTS 验收"""
import sqlite3, json, datetime, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
PRE = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_prestate.json'), encoding='utf-8'))
c = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True); c.execute('PRAGMA query_only=ON')
TZ = datetime.timezone(datetime.timedelta(hours=8))
def ts(t):
    if t is None: return '-'
    return datetime.datetime.fromtimestamp(int(t), tz=TZ).strftime('%Y-%m-%d %H:%M:%S')

n = c.execute('select count(*) from messages').fetchone()[0]
print(f'== 全库 ==\nbefore={PRE["count"]}  after={n}  delta={n-PRE["count"]}')
print('FTS rows =', c.execute('select count(*) from messages_fts').fetchone()[0])

print('\n== 新增消息（id > %d） ==' % PRE['max_id'])
rows = c.execute("""select m.id, m.session_key, s.display_name, m.ts, m.role, m.type, m.content
                    from messages m left join sessions s on s.talker=m.session_key
                    where m.id > ? order by m.id""", (PRE['max_id'],)).fetchall()
print('条数:', len(rows))
for r in rows:
    content = (r[6] or '').replace('\n', ' ')
    if len(content) > 400: content = content[:400] + '…'
    print(f'[{ts(r[3])}] {r[1]} | {r[2]} | {r[4]}/{r[5]} | {content}')

print('\n== 贺伊飞会话全文（同步后） ==')
T = 'hyf782877122'
for r in c.execute('select ts, role, type, content from messages where session_key=? order by ts, id', (T,)):
    content = (r[3] or '').replace('\n', ' ')
    if r[2] == 'voice':
        import re
        m = re.search(r'voicelength="(\d+)"', r[3] or '')
        content = f'[语音 {int(m.group(1))/1000:.1f}s]' if m else '[语音]'
    if len(content) > 400: content = content[:400] + '…'
    print(f'[{ts(r[0])}] {r[1]}/{r[2]} | {content}')

print('\n== 目标会话（同步后） ==')
for tk, v in PRE['targets'].items():
    r = c.execute('select count(*), max(ts) from messages where session_key=?', (tk,)).fetchone()
    flag = '  ← 有新增' if r[0] != v['count'] else ''
    print(f'{tk:24s} {v["count"]:5d} -> {r[0]:5d} | 最新 {ts(r[1])}{flag}')
