# -*- coding: utf-8 -*-
"""只读：群公告 + 群成员（媒体部/新群）"""
import sqlite3, sys, io, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DB = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\contact\contact.db'
c = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
c.execute('PRAGMA query_only=ON')
TZ = datetime.timezone(datetime.timedelta(hours=8))
def ts(t):
    try: return datetime.datetime.fromtimestamp(int(t), tz=TZ).strftime('%Y-%m-%d %H:%M')
    except Exception: return str(t)

rooms = ['19944550391@chatroom','44223351827@chatroom','45490054651@chatroom']
ids = {}
for room in rooms:
    r = c.execute('select id, username from chat_room where username=?', (room,)).fetchone()
    ids[room] = r[0] if r else None
    print(room, '-> id', r[0] if r else None)
    if r:
        d = c.execute('select * from chat_room_info_detail where username_=?', (room,)).fetchone()
        if d:
            ann = d[2] or ''
            print('  公告发布:', ts(d[4]) if d[4] else '-')
            print('  公告内容:', ann[:800] if ann else '(空)')
        else:
            print('  无 info_detail 行')

print('\n== 群成员（名字经 contact 反查） ==')
def member_names(room_id, limit=80):
    rows = c.execute('select member_id from chatroom_member where room_id=?', (room_id,)).fetchall()
    out=[]
    for (mid,) in rows[:limit]:
        r = c.execute('select username, nick_name, remark from contact where id=?', (mid,)).fetchone()
        out.append(r if r else (mid,))
    return len(rows), out

for room in rooms:
    rid = ids.get(room)
    if not rid: continue
    n, names = member_names(rid)
    print(f'-- {room} 成员 {n} --')
    for x in names[:40]:
        print('   ', x)

print('\n== 所有有公告的群（最近公告时间倒序前 20） ==')
for d in c.execute("""select username_, announcement_, announcement_publish_time_ from chat_room_info_detail
                      where announcement_ is not null and announcement_ != ''
                      order by announcement_publish_time_ desc limit 20"""):
    print('---', d[0], '|', ts(d[2]))
    print('   ', (d[1] or '')[:400])
