# -*- coding: utf-8 -*-
"""只读：媒体部群核实 + 贺伊飞联系人信息 + 群系统消息"""
import sqlite3, datetime, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
c = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
c.execute('PRAGMA query_only=ON')
TZ = datetime.timezone(datetime.timedelta(hours=8))
def ts(t): return datetime.datetime.fromtimestamp(int(t), tz=TZ).strftime('%Y-%m-%d %H:%M:%S')

print('===== 群 19944550391 全部消息 =====')
for r in c.execute("select ts, role, sender, type, content from messages where session_key='19944550391@chatroom' order by ts"):
    content=(r[4] or '').replace('\n',' ')
    if len(content)>240: content=content[:240]+'…'
    print(f'[{ts(r[0])}] role={r[1]} sender={r[2]} {r[3]} | {content}')

print('\n===== 群 19944550391 sessions 行 =====')
print(c.execute("select * from sessions where talker='19944550391@chatroom'").fetchone())
print('\n===== 群 44223351827 sessions 行 =====')
print(c.execute("select * from sessions where talker='44223351827@chatroom'").fetchone())
print('\n===== 45490054651 sessions 行 =====')
print(c.execute("select * from sessions where talker='45490054651@chatroom'").fetchone())

print('\n===== 我在媒体部群的发言（sender=本人） =====')
me='wxid_zn4ozsnn8esr21'
for r in c.execute("select ts, role, type, content from messages where session_key='19944550391@chatroom' and (sender=? or role='me') order by ts",(me,)):
    print(ts(r[0]), r[1], r[2], (r[3] or '')[:200])

print('\n===== 全库：sender 含 hyf 的消息（跨会话） =====')
for r in c.execute("select session_key, ts, role, content from messages where sender like '%hyf%' order by ts limit 50"):
    print(r[0], ts(r[1]), r[2], (r[3] or '')[:120])

print('\n===== 全库：10-23 09:00-20:00 且 content 含「贺/伊飞/Yifi」 =====')
for r in c.execute("""select m.session_key, s.display_name, m.ts, m.role, m.content from messages m
                      left join sessions s on s.talker=m.session_key
                      where m.ts>=? and (m.content like '%Yifi%' or m.content like '%伊飞%' or m.content like '%贺哥%')
                      order by m.ts""", (int(datetime.datetime(2026,10,23,0,0,tzinfo=TZ).timestamp()),)):
    print(r[0], r[1], ts(r[2]), r[3], (r[4] or '')[:120])
