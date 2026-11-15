# -*- coding: utf-8 -*-
"""周雯娟：群成员关系 + 朋友圈 + DeepSeek 工作区"""
import sqlite3, io, os, json, glob

DEC = r'C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted'
out = []
def P(*a):
    t = ' '.join(str(x) for x in a); out.append(t); print(t)

WX = 'wxid_uhulgmrvfq4a12'
d = sqlite3.connect('file:%s/contact/contact.db?mode=ro' % DEC, uri=True)
d.row_factory = sqlite3.Row

me = d.execute("select id,username,remark,nick_name from contact where username=?", (WX,)).fetchone()
P('=== 1. 她的 contact.id ===')
P('  ', tuple(me) if me else None)
cid = me['id'] if me else None

P('')
P('=== 2. chatroom_member（room_id / member_id 为数字）===')
P('  样例:', d.execute("select * from chatroom_member limit 3").fetchall().__str__())
rooms = d.execute("select room_id from chatroom_member where member_id=?", (cid,)).fetchall()
P('  她所在群数 =', len(rooms))
room_ids = [r[0] for r in rooms]

P('')
P('=== 3. 群名 ===')
for rid in room_ids[:40]:
    r = d.execute("select id,username,owner from chat_room where id=?", (rid,)).fetchone()
    if r:
        nm = d.execute("select nick_name,remark from contact where username=?", (r['username'],)).fetchone()
        P('   id=%s | %s | nick=%s remark=%s' % (rid, r['username'], nm['nick_name'] if nm else '', nm['remark'] if nm else ''))
    else:
        P('   id=%s 无 chat_room 记录' % rid)

P('')
P('=== 4. 对照：李博文 / 程颂孟秋 所在群数 ===')
for nm, wx in [('李博文', 'wxid_4yurl8wrbi4a22'), ('程颂孟秋', 'wxid_j5ekmvhqltug22')]:
    r = d.execute("select id from contact where username=?", (wx,)).fetchone()
    if r:
        n = d.execute("select count(*) from chatroom_member where member_id=?", (r['id'],)).fetchone()[0]
        P('  %s: contact.id=%s 群数=%s' % (nm, r['id'], n))

P('')
P('=== 5. 朋友圈 sns.db：她的痕迹 ===')
try:
    s = sqlite3.connect('file:%s/sns/sns.db?mode=ro' % DEC, uri=True)
    s.row_factory = sqlite3.Row
    tabs = [r[0] for r in s.execute("select name from sqlite_master where type='table'")]
    P('  sns 表:', tabs)
    for t in tabs:
        cols = [x[1] for x in s.execute('pragma table_info("%s")' % t)]
        if 'user_name' in cols or 'username' in cols:
            key = 'user_name' if 'user_name' in cols else 'username'
            try:
                n = s.execute('select count(*) from "%s" where %s=?' % (t, key), (WX,)).fetchone()[0]
                if n:
                    P('  [%s] %s 命中 %d' % (t, key, n))
                    for r in s.execute('select * from "%s" where %s=? limit 5' % (t, key), (WX,)):
                        P('     ', dict(r))
            except Exception as e:
                pass
    # SnsTopItem 里的 last_read / 帖
    for t in tabs:
        cols = [x[1] for x in s.execute('pragma table_info("%s")' % t)]
        if 'tid' in cols and 'username' in cols:
            rows = s.execute('select * from "%s" where username=? limit 5' % t, (WX,)).fetchall()
            P('  [%s] 她的行数 = %d' % (t, len(rows)))
            for r in rows:
                P('     ', dict(r))
except Exception as e:
    P('  sns err:', e)

P('')
P('=== 6. DeepSeek 工作区（472 人画像）===')
WS = r'C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区'
P('  目录存在:', os.path.isdir(WS))
if os.path.isdir(WS):
    for root, dirs, files in os.walk(WS):
        for f in files:
            if '周雯娟' in f or 'Sora' in f:
                P('  命中文件:', os.path.join(root, f))
    # 找 sqlite
    for f in glob.glob(os.path.join(WS, '**', '*.sqlite'), recursive=True) + glob.glob(os.path.join(WS, '**', '*.db'), recursive=True):
        P('  DB:', f, os.path.getsize(f))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_wj_group.txt', 'w', encoding='utf-8').write('\n'.join(out))
P('')
P('-> _tmp\\probe_wj_group.txt')
