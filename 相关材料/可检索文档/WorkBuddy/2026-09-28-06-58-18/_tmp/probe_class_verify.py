# -*- coding: utf-8 -*-
"""验证：「3班」标签(24) == 17区经2班群(24)？并定位周雯娟的班级"""
import sqlite3, io

DEC = r'C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted'
out = []
def P(*a):
    t = ' '.join(str(x) for x in a); out.append(t); print(t)

d = sqlite3.connect('file:%s/contact/contact.db?mode=ro' % DEC, uri=True)
d.row_factory = sqlite3.Row
lab = {int(i): n for i, n in d.execute("select label_id_, label_name_ from contact_label")}


def read_varint(b, i):
    s = 0; v = 0
    while i < len(b):
        x = b[i]; i += 1
        v |= (x & 0x7F) << s
        if not (x & 0x80): return v, i
        s += 7
    return None, i


def labels(buf):
    if not buf: return []
    if isinstance(buf, str): buf = buf.encode('latin-1', 'ignore')
    j = buf.find(b'\xf2\x01')
    if j < 0: return []
    L, k = read_varint(buf, j + 2)
    if L is None or L <= 0 or k + L > len(buf): return []
    return [int(p) for p in buf[k:k + L].decode('ascii', 'ignore').split(',') if p.strip().isdigit()]


def group_members(room_username):
    rows = d.execute("""select c2.username, c2.remark, c2.nick_name, c2.extra_buffer
                        from chatroom_member m
                        join chat_room c on c.id=m.room_id
                        join contact c2 on c2.id=m.member_id
                        where c.username=?""", (room_username,)).fetchall()
    return rows

# 标签 49 = 3班
tag49 = set()
for r in d.execute("select username, remark, nick_name, extra_buffer from contact"):
    if 49 in labels(r['extra_buffer']):
        tag49.add(r['username'])
P('标签「3班」(49) = %d 人' % len(tag49))

for room, name in [('10012158143@chatroom', '17区经2班'),
                   ('5508117906@chatroom', '17级公管三班通知群'),
                   ('5193229600@chatroom', '三班候选群'),
                   ('6650862877@chatroom', '公管三，四班计算机')]:
    rows = group_members(room)
    us = set(r['username'] for r in rows)
    P('')
    P('=== %s (%s) · %d 人 ===' % (name, room, len(us)))
    P('  ∩「3班」标签 = %d 人' % len(us & tag49))
    P('  「3班」标签中不在本群的 = %s' % sorted([r['remark'] or r['nick_name'] for r in d.execute('select remark,nick_name,username,extra_buffer from contact') if r['username'] in (tag49 - us)]))
    P('  成员：')
    for r in sorted(rows, key=lambda x: (x['remark'] or x['nick_name'] or '')):
        ids = labels(r['extra_buffer'])
        mark = '  ★3班' if 49 in ids else ''
        P('     %-22s | %-18s | %s%s' % ((r['remark'] or '')[:22], (r['nick_name'] or '')[:18], ids, mark))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_class_verify.txt', 'w', encoding='utf-8').write('\n'.join(out))
P('')
P('-> _tmp\\probe_class_verify.txt')
