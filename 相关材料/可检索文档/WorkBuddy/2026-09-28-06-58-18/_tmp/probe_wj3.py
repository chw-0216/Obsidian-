# -*- coding: utf-8 -*-
"""周雯娟 全量重查：索引库 + 解密库 + 群成员 + FTS 孤儿"""
import sqlite3, io, re

IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
DEC = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
WXID = 'wxid_uhulgmrvfq4a12'
out = []
def P(*a):
    t = ' '.join(str(x) for x in a)
    out.append(t); print(t)

c = sqlite3.connect('file:%s?mode=ro' % IDX, uri=True)

P('===== 1. 索引库 · 会话 =====')
for r in c.execute("select talker,display_name,session_type,message_count,first_ts,last_ts "
                   "from sessions where talker=?", (WXID,)):
    P('sessions:', r)

P('')
P('===== 2. 索引库 · 消息（按 session_key）=====')
n = c.execute("select count(*) from messages where session_key=?", (WXID,)).fetchone()[0]
P('messages 条数 =', n)
for r in c.execute("select ts,time_text,role,sender,type,substr(content,1,120) from messages "
                   "where session_key=? order by ts limit 20", (WXID,)):
    P('  ', r)

P('')
P('===== 3. 索引库 · 正文 LIKE 命中（2 字人名走 LIKE）=====')
for kw in ('周雯娟', '雯娟', 'Sora', 'sora4811', '周文娟'):
    rows = c.execute("select session_key,ts,role,substr(content,1,100) from messages "
                     "where content like ? order by ts limit 8", ('%'+kw+'%',)).fetchall()
    P('[%s] 命中 %d' % (kw, len(rows)))
    for r in rows:
        P('   ', r)

P('')
P('===== 4. 索引库 · FTS 完整性 =====')
try:
    o = c.execute("select count(*) from messages_fts f left join messages m on m.rowid=f.rowid "
                  "where m.rowid is null").fetchone()[0]
    P('messages_fts 孤儿 =', o)
except Exception as e:
    P('FTS check err:', e)
tot = c.execute("select count(*) from messages").fetchone()[0]
ftstot = c.execute("select count(*) from messages_fts").fetchone()[0]
P('messages =', tot, '| messages_fts =', ftstot)
P('时间范围:', c.execute("select min(ts),max(ts) from messages").fetchone())

P('')
P('===== 5. 解密库 contact.db · 她的完整记录 =====')
DECU = DEC.replace(chr(92), '/')
d = sqlite3.connect('file:%s/contact/contact.db?mode=ro' % DECU, uri=True)
d.row_factory = sqlite3.Row
cols = [x[1] for x in d.execute("pragma table_info(contact)")]
P('contact 列:', ', '.join(cols))
row = d.execute("select * from contact where username=?", (WXID,)).fetchone()
if row:
    for k in cols:
        v = row[k]
        if k == 'extra_buffer' and v:
            v = repr(v)[:400]
        P('  %-24s = %s' % (k, v))
else:
    P('  contact 无此 wxid')

P('')
P('===== 6. 解密库 · 标签字典 =====')
lab = {str(i): n for i, n in d.execute("select label_id_, label_name_ from contact_label")}
P('标签总数 =', len(lab))
TAGRE = re.compile(rb'\xf2\x01(.)(.*?)(?=\xfa\x01|$)', re.S)
if row and row['extra_buffer']:
    eb = row['extra_buffer']
    if isinstance(eb, str):
        eb = eb.encode('latin-1', 'ignore')
    m = TAGRE.search(eb)
    if m:
        ln = m.group(1)[0]
        ids = m.group(2)[:ln]
        P('  解析出的标签 ID =', list(ids), '->', [lab.get(str(b), '?') for b in ids])
    else:
        P('  未匹配到 f2 01 段')

P('')
P('===== 7. 解密库 · 她在哪些群（chatroom_member）=====')
rooms = []
mc = []
try:
    mc = [x[1] for x in d.execute("pragma table_info(chatroom_member)")]
    P('chatroom_member 列:', ', '.join(mc))
    key = 'member_username' if 'member_username' in mc else mc[1]
    rooms = d.execute("select * from chatroom_member where %s=?" % key, (WXID,)).fetchall()
    P('她所在的群 =', len(rooms))
    for r in rooms[:40]:
        P('   ', tuple(r))
except Exception as e:
    P('chatroom_member err:', e)

P('')
P('===== 8. 群名对照（她所在群）=====')
for r in rooms[:40]:
    room = r[0]
    try:
        nm = d.execute("select nick_name,remark from contact where username=?", (room,)).fetchone()
    except Exception:
        nm = None
    P('   %s -> %s' % (room, nm))

P('')
P('===== 9. 对照：李博文（3班+城院）=====')
LBW = 'wxid_4yurl8wrbi4a22'
r2 = d.execute("select username,remark,nick_name,extra_buffer from contact where username=?", (LBW,)).fetchone()
if r2:
    eb = r2['extra_buffer']
    if isinstance(eb, str):
        eb = eb.encode('latin-1', 'ignore')
    m = TAGRE.search(eb or b'')
    ids = list(m.group(2)[:m.group(1)[0]]) if m else []
    P('李博文 标签 =', ids, '->', [lab.get(str(b), '?') for b in ids])

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_wenjuan2.txt',
        'w', encoding='utf-8').write('\n'.join(out))
P('')
P('-> _tmp\\probe_wenjuan2.txt')
