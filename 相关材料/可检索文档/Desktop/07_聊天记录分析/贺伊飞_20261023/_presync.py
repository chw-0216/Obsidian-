# -*- coding: utf-8 -*-
"""同步前基准：message 总数 / max(id) / 目标会话状态 → 写 _prestate.json"""
import sqlite3, json, datetime, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_prestate.json')
c = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True); c.execute('PRAGMA query_only=ON')
n = c.execute('select count(*) from messages').fetchone()[0]
mx = c.execute('select max(id) from messages').fetchone()[0]
mts = c.execute('select max(ts) from messages').fetchone()[0]
targets = {}
for tk in ['hyf782877122','19944550391@chatroom','huxiaomi123','shuixiaoxie','liuyuhan1012','guo647789','a35599192','wxid_1wa75s1kze3o22','wxid_wdnk6ue9kiyn22']:
    r = c.execute('select count(*), max(ts) from messages where session_key=?', (tk,)).fetchone()
    targets[tk] = {'count': r[0], 'last_ts': r[1]}
state = {'count': n, 'max_id': mx, 'max_ts': mts, 'targets': targets}
json.dump(state, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('pre:', n, 'max_id=', mx, 'latest=', datetime.datetime.fromtimestamp(mts, tz=datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S'))
for k, v in targets.items():
    print(k, v)
