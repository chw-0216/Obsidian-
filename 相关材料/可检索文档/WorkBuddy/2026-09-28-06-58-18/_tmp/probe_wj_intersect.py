# -*- coding: utf-8 -*-
"""用群交集精确定位「同班」：周雯娟 ∩ 李博文 ∩ 程颂孟秋"""
import sqlite3, io

DEC = r'C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted'
out = []
def P(*a):
    t = ' '.join(str(x) for x in a); out.append(t); print(t)

d = sqlite3.connect('file:%s/contact/contact.db?mode=ro' % DEC, uri=True)
d.row_factory = sqlite3.Row

PEOPLE = {
    '周雯娟': 'wxid_uhulgmrvfq4a12',
    '李博文': 'wxid_4yurl8wrbi4a22',
    '程颂孟秋': 'wxid_j5ekmvhqltug22',
    '尹诗琪': None,
}
# 尹诗琪按昵称找
r = d.execute("select username from contact where nick_name='十七' or remark like '%尹诗琪%'").fetchall()
if r: PEOPLE['尹诗琪'] = r[0]['username']

def rooms_of(wx):
    row = d.execute("select id from contact where username=?", (wx,)).fetchone()
    if not row: return {}, None
    rs = d.execute("select room_id from chatroom_member where member_id=?", (row['id'],)).fetchall()
    m = {}
    for x in rs:
        cr = d.execute("select username from chat_room where id=?", (x['room_id'],)).fetchone()
        if cr:
            nm = d.execute("select nick_name from contact where username=?", (cr['username'],)).fetchone()
            m[cr['username']] = nm['nick_name'] if nm else cr['username']
    return m, row['id']

data = {}
for nm, wx in PEOPLE.items():
    if not wx: continue
    m, cid = rooms_of(wx)
    data[nm] = m
    P('%s: %d 个群 (contact.id=%s)' % (nm, len(m), cid))

P('')
P('=== 周雯娟 ∩ 李博文 ===')
zw = data.get('周雯娟', {}); lb = data.get('李博文', {})
inter = set(zw) & set(lb)
P('共同群 %d 个：' % len(inter))
for k in sorted(inter):
    P('   %s | %s' % (k, zw[k]))

P('')
P('=== 周雯娟 ∩ 程颂孟秋 ===')
cs = data.get('程颂孟秋', {})
inter2 = set(zw) & set(cs)
P('共同群 %d 个：' % len(inter2))
for k in sorted(inter2):
    P('   %s | %s' % (k, zw[k]))

P('')
P('=== 周雯娟 ∩ 李博文 ∩ 程颂孟秋（三人同群）===')
inter3 = set(zw) & set(lb) & set(cs)
P('三人共同群 %d 个：' % len(inter3))
for k in sorted(inter3):
    P('   %s | %s' % (k, zw[k]))

P('')
P('=== 各群人数（周雯娟所在群）===')
for k, nm in sorted(zw.items(), key=lambda x: x[1]):
    n = d.execute("select count(*) from chatroom_member m join chat_room c on c.id=m.room_id where c.username=?", (k,)).fetchone()[0]
    P('   %-46s %4d 人' % (nm[:46], n))

P('')
P('=== 17区经2班 / 17级公管三班通知群 成员（前 60）===')
for k, nm in zw.items():
    if '区经2班' in (nm or '') or '公管三班' in (nm or ''):
        P('  --- %s (%s) ---' % (nm, k))
        rows = d.execute("""select c2.remark, c2.nick_name from chatroom_member m
                            join chat_room c on c.id=m.room_id
                            join contact c2 on c2.id=m.member_id
                            where c.username=?""", (k,)).fetchall()
        for x in rows[:60]:
            P('      %s | %s' % (x['remark'] or '', x['nick_name'] or ''))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_wj_intersect.txt', 'w', encoding='utf-8').write('\n'.join(out))
P('')
P('-> _tmp\\probe_wj_intersect.txt')
