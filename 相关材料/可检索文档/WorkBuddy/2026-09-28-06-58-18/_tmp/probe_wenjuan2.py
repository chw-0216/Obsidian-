# -*- coding: utf-8 -*-
import sqlite3, os, datetime, glob, json
base = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
M = 1 << 64
def fmt(t):
    return datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M') if t else '-'

WEN = 'wxid_uhulgmrvfq4a12'   # 周雯娟 Sora
LI  = 'wxid_4yurl8wrbi4a22'   # 李博文 城市学院

print('=== index.sqlite 是否有这两个会话 ===')
ic = sqlite3.connect('file:%s?mode=ro' % IDX, uri=True); ic.row_factory = sqlite3.Row
for wx, nm in ((WEN, '周雯娟'), (LI, '李博文')):
    r = ic.execute('select talker,display_name,session_type,message_count,first_ts,last_ts from sessions where talker=?', (wx,)).fetchone()
    print('  %s %s -> %s' % (nm, wx, dict(r) if r else 'NO SESSION'))
    n = ic.execute("select count(*) from messages where session_key=?", (wx,)).fetchone()[0]
    print('     messages rows:', n)
    if n:
        for rr in ic.execute("select role,count(*) c from messages where session_key=? group by role", (wx,)):
            print('       role=%s %d' % (rr['role'], rr['c']))

print()
print('=== sns: 周雯娟 / 李博文 的 feed 记录 ===')
sc = sqlite3.connect('file:%s?mode=ro' % os.path.join(base, 'sns', 'sns.db').replace('\\', '/'), uri=True)
sc.row_factory = sqlite3.Row
for wx, nm in ((WEN, '周雯娟'), (LI, '李博文')):
    rr = list(sc.execute('select tid,username,create_time,last_read_time,is_read from SnsTopItem_1 where username=? order by create_time', (wx,)))
    print('  %s -> feed %d 条' % (nm, len(rr)))
    for r in rr[-8:]:
        print('     post=%s  last_read=%s  is_read=%s' % (fmt(r['create_time']), fmt(r['last_read_time']), r['is_read']))
    rr2 = list(sc.execute('select tid,user_name from SnsTimeLine where user_name=?', (wx,)))
    print('     SnsTimeLine(有正文) hits:', len(rr2))
    rr3 = list(sc.execute('select count(*) from SnsMessage_tmp3 where from_username=? or to_username=?', (wx, wx)))
    print('     互动表 hits:', rr3[0][0])

print()
print('=== SnsTimeLine 全部 304 条：找「影城/环球/游乐园/过山车/哈利」 ===')
rows = list(sc.execute('select tid,user_name,content from SnsTimeLine'))
for kw in ('影城', '环球', '哈利', '过山车', '游乐园', '环球影城'):
    h = [r for r in rows if kw in (r['content'] or '')]
    print('  %s -> %d' % (kw, len(h)))

print()
print('=== 找本机朋友圈导出 JSON ===')
pats = [
    r'C:\Users\wardc\Desktop\**\朋友圈导出*.json',
    r'C:\Users\wardc\Desktop\**\朋友圈\*.json',
    r'C:\Users\wardc\Documents\**\朋友圈导出*.json',
]
for p in pats:
    for f in glob.glob(p, recursive=True)[:20]:
        print('  ', f, os.path.getsize(f))
