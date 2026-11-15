# -*- coding: utf-8 -*-
"""微信索引验收：总量 + 目标会话 + FTS 三问题数（只读）"""
import sqlite3, datetime, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
c = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
c.execute('PRAGMA query_only=ON')
TZ = datetime.timezone(datetime.timedelta(hours=8))
def ts(t):
    if t is None: return '-'
    return datetime.datetime.fromtimestamp(int(t), tz=TZ).strftime('%Y-%m-%d %H:%M:%S')

print('== 全库 ==')
n = c.execute('select count(*) from messages').fetchone()[0]
mx = c.execute('select max(ts) from messages').fetchone()[0]
s = c.execute('select count(*) from sessions').fetchone()[0]
print(f'messages={n}  sessions={s}  latest={ts(mx)}')

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
print('\n== 目标会话 ==')
for tk, name in targets.items():
    r = c.execute('select count(*), min(ts), max(ts) from messages where session_key=?', (tk,)).fetchone()
    miss = c.execute('select count(*) from messages m left join messages_fts f on f.rowid=m.id where m.session_key=? and f.rowid is null', (tk,)).fetchone()[0]
    orph = c.execute('select count(*) from messages_fts f left join messages m on m.id=f.rowid where f.session_key=? and m.id is null', (tk,)).fetchone()[0]
    mism = c.execute('select count(*) from messages m join messages_fts f on f.rowid=m.id where m.session_key=? and (COALESCE(m.content,\'\')<>COALESCE(f.content,\'\') or COALESCE(m.sender,\'\')<>COALESCE(f.sender,\'\') or COALESCE(m.session_key,\'\')<>COALESCE(f.session_key,\'\'))', (tk,)).fetchone()[0]
    print(f'{tk:24s} {name:12s} 条数={r[0]:5d} 最新={ts(r[2])}  FTS缺失={miss} 孤儿={orph} 错配={mism}')

# FTS 全库计数核对
print('\n== FTS 全库 ==')
print('messages_fts rows =', c.execute('select count(*) from messages_fts').fetchone()[0])
