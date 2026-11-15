# -*- coding: utf-8 -*-
"""只读：群成员与群名，定位贺伊飞/何一沙所在群"""
import sqlite3, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DB = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\contact\contact.db'
c = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
c.execute('PRAGMA query_only=ON')

for t in ['chat_room','chat_room_info_detail','chatroom_member']:
    print(f'== {t} 结构 ==')
    for r in c.execute(f'pragma table_info({t})'):
        print(r)
    print('rows:', c.execute(f'select count(*) from {t}').fetchone()[0])
    print()

# 群名
print('== 群名（chat_room）含 央美/CAFAM/媒体/展/发布 ==')
try:
    for r in c.execute("select * from chat_room limit 5"):
        print('sample:', r)
except Exception as e:
    print('ERR', e)

# 查这几个 room 的成员
def members_of(room):
    try:
        rows = c.execute("select * from chatroom_member where chatroom_id=? or room_id=? limit 5", (room, room)).fetchall()
        return rows
    except Exception:
        return None

for room in ['19944550391@chatroom','44223351827@chatroom','45490054651@chatroom']:
    print(f'-- {room} 成员表探测 --')
    try:
        cols=[x[1] for x in c.execute('pragma table_info(chatroom_member)')]
        # 尝试 1: username 字段
        try:
            rows=c.execute("select * from chatroom_member where chatroom_id=?", (room,)).fetchall()
        except Exception:
            rows=[]
        if not rows:
            try:
                rows=c.execute("select * from chatroom_member where room_id=?", (room,)).fetchall()
            except Exception:
                rows=[]
        print('成员数:', len(rows))
        names=[]
        for r in rows[:15]:
            d=dict(zip(cols,r))
            uname = d.get('username') or d.get('member_id') or d.get('wxid')
            names.append(uname)
        print('前15成员:', names)
    except Exception as e:
        print('ERR', e)

# 贺伊飞/何一沙/本人 出现在哪些群
print('\n== 按成员表反查 ==')
try:
    cols=[x[1] for x in c.execute('pragma table_info(chatroom_member)')]
    print('列:', cols)
    for u in ['hyf782877122','huxiaomi123','wxid_zn4ozsnn8esr21']:
        rows=c.execute("select * from chatroom_member where username=?", (u,)).fetchall()
        print(u, '->', len(rows), 'rooms')
        for r in rows[:10]:
            print('   ', r)
except Exception as e:
    print('ERR', e)
