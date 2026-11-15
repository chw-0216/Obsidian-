# -*- coding: utf-8 -*-
import sqlite3, io, os, datetime

DEC = 'C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted'.replace('\\', '/')
IDX = 'C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite'
WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
OUT = io.open(os.path.join(WS, '_tmp', 'probe_circle4.txt'), 'w', encoding='utf-8')
def P(*a):
    OUT.write(' '.join(str(x) for x in a) + '\n')

cd = sqlite3.connect('file:%s/contact/contact.db?mode=ro' % DEC, uri=True)
ix = sqlite3.connect('file:%s?mode=ro' % IDX, uri=True)

me_id, me_un = cd.execute("select id,username from contact where username='wxid_zn4ozsnn8esr21'").fetchone()
P('本人 id=%s username=%s' % (me_id, me_un))

rooms = {}
for rid, un, nn in cd.execute("select id,username,nick_name from contact where username like '%@chatroom'"):
    rooms[rid] = (un, nn)

my_rooms = [r[0] for r in cd.execute("select room_id from chatroom_member where member_id=?", (me_id,))]
P()
P('=== 本人在的群 %d 个（按 2 年条数降序）===' % len(my_rooms))
rows = []
for rid in my_rooms:
    un, nn = rooms.get(rid, ('?', '?'))
    cnt = cd.execute("select count(*) from chatroom_member where room_id=?", (rid,)).fetchone()[0]
    n2 = ix.execute("select count(*) from messages where session_key=?", (un,)).fetchone()[0]
    rows.append((n2, cnt, nn or '', un))
rows.sort(reverse=True)
P('%-34s %-22s %6s %8s' % ('群名', 'talker', '人数', '2年条数'))
for n2, cnt, nn, un in rows:
    P('%-34s %-22s %6d %8d' % (nn[:34], un, cnt, n2))

# 13 人 wxid
P13 = {
    '程颂孟秋': 'wxid_j5ekmvhqltug22', '尹诗琪': 'wxid_i2o78wu1pzgz21',
    '李博文': 'wxid_4yurl8wrbi4a22', '李莉丽': 'wxid_05offrd7pvf632',
    '肖宇': 'wxid_zwutgxzu1ppt22', '李子轩': 'wxid_sgzi99h3mx4n22',
    '闻一青': 'wxid_l28x8imwmi0g21', '王婧潭': 'wxid_4x0ry32wco6212',
    '裴青青': 'wxid_g2k94eukarg222', '蔡静文': 'wxid_uxbth1xufvoq22',
    '李澳': 'wxid_ywxfo6b4w4xr22', '张学鹏': 'wxid_swp8wyarjmbj22',
    '陈飞': 'wxid_0bg5zimzn2th11', '周雯娟': 'wxid_uhulgmrvfq4a12',
}

P()
P('=== 13 人 + 周雯娟 的群交集（本科班群）===')
BENKE = {
    '10012158143@chatroom': '17区经2班',
    '5508117906@chatroom': '17级公管三班通知群',
    '5193229600@chatroom': '三班候选群',
    '6650862877@chatroom': '公管三，四班计算机',
    '7186809469@chatroom': '城市学院学生会13.0',
    '18144316201@chatroom': '2021届城院毕业生通知群',
}
for nm, wx in P13.items():
    cid = cd.execute("select id from contact where username=?", (wx,)).fetchone()
    if not cid:
        P('%-10s NOT FOUND' % nm); continue
    cid = cid[0]
    rids = [r[0] for r in cd.execute("select room_id from chatroom_member where member_id=?", (cid,))]
    hit = []
    for rid in rids:
        un = rooms.get(rid, ('?',))[0]
        if un in BENKE:
            hit.append(BENKE[un])
    P('%-10s 群数 %2d | 本科班群命中: %s' % (nm, len(rids), ' / '.join(hit) if hit else '—'))

# 导出 13 人对话正文
OUT2 = io.open(os.path.join(WS, '_tmp', 'benke_msgs.txt'), 'w', encoding='utf-8')
for nm, wx in P13.items():
    if nm == '周雯娟':
        continue
    r = ix.execute("select count(*) from messages where session_key=?", (wx,)).fetchone()[0]
    OUT2.write('\n\n########## %s (%s) — %d 条 ##########\n' % (nm, wx, r))
    if r == 0:
        continue
    for ts, role, typ, content in ix.execute(
            "select ts, role, type, content from messages where session_key=? order by ts", (wx,)):
        t = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
        c = (content or '').replace('\n', ' ')
        OUT2.write('[%s] %-5s t%-3s %s\n' % (t, role, typ, c[:220]))
OUT2.close()
P()
P('已导出 _tmp/benke_msgs.txt')
OUT.close()
print('done')
