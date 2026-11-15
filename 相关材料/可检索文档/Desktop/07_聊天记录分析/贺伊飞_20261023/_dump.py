# -*- coding: utf-8 -*-
"""只读取证：贺伊飞会话全文 + 他在群里的发言 + 美术馆线近况"""
import sqlite3, datetime, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
c = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
c.execute('PRAGMA query_only=ON')
TZ = datetime.timezone(datetime.timedelta(hours=8))

def ts(t):
    try:
        return datetime.datetime.fromtimestamp(int(t), tz=TZ).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return str(t)

def dump(talker, title, n=None):
    print(f'\n===== {title} | talker={talker} =====')
    rows = c.execute('select ts, time_text, role, sender, type, content, server_id, local_id from messages where session_key=? order by ts, id', (talker,)).fetchall()
    print(f'# 共 {len(rows)} 条')
    if n:
        rows = rows[-n:]
    for r in rows:
        content = (r[5] or '').replace('\n', '\\n')
        if len(content) > 900:
            content = content[:900] + f'…[截断 原长{len(r[5])}]'
        print(f'[{ts(r[0])}] {r[2]}/{r[4]} | {content}')
    return rows

# 1) 贺伊飞会话全文
dump('hyf782877122', '贺伊飞 私聊全文')

# 2) 贺伊飞作为 sender 出现的所有会话（群聊）
print('\n===== 贺伊飞作为发送者出现的会话 =====')
for r in c.execute("select session_key, count(*) from messages where sender='hyf782877122' group by session_key order by count(*) desc"):
    s = c.execute('select display_name, session_type, message_count from sessions where talker=?', (r[0],)).fetchone()
    print(r[0], '|', s, '| 发言', r[1], '条')

# 3) 美术馆线相关会话近况
for tk, name in [('huxiaomi123','何一沙 媒体部主任'), ('shuixiaoxie','岳老师 美术馆办公室'), ('liuyuhan1012','刘宇晗 美术馆策研部')]:
    dump(tk, name, n=60)

# 4) 名称含"美术馆/发布会/展"的群近 3 天消息概览
print('\n===== 名称含 美术馆/发布会 的会话 =====')
for r in c.execute("select talker, display_name, session_type, message_count from sessions where display_name like '%美术馆%' or display_name like '%发布会%' or display_name like '%展览%' order by message_count desc limit 30"):
    print(r)
