# -*- coding: utf-8 -*-
import sqlite3, os, datetime, glob
base = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
con = sqlite3.connect('file:%s?mode=ro' % os.path.join(base, 'contact', 'contact.db').replace('\\', '/'), uri=True)
con.row_factory = sqlite3.Row
M = 1 << 64
def fmt(t):
    return datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M') if t else '-'

print('=== contact.db 全字段搜「娟」 ===')
rows = list(con.execute(
    "select username,remark,nick_name,alias,description,local_type from contact "
    "where nick_name like '%娟%' or remark like '%娟%' or alias like '%娟%' or description like '%娟%'"))
print('  hits:', len(rows))
for r in rows[:40]:
    print('   %-26s remark=%-14s nick=%-18s alias=%-14s desc=%s' % (
        r['username'], r['remark'], r['nick_name'], r['alias'], (r['description'] or '')[:20]))

print()
print('=== contact.db 搜「周」「环球」 ===')
for kw in ('周文', '环球'):
    rr = list(con.execute(
        "select username,remark,nick_name,alias from contact where nick_name like ? or remark like ? or alias like ?",
        ('%'+kw+'%', '%'+kw+'%', '%'+kw+'%')))
    print('  %s -> %d' % (kw, len(rr)))
    for r in rr[:15]:
        print('     %-26s remark=%-16s nick=%s' % (r['username'], r['remark'], r['nick_name']))

print()
print('=== 李博文 wxid 是否出现在朋友圈 feed ===')
scon = sqlite3.connect('file:%s?mode=ro' % os.path.join(base, 'sns', 'sns.db').replace('\\', '/'), uri=True)
scon.row_factory = sqlite3.Row
for wx in ('wxid_4yurl8wrbi4a22',):
    rr = list(scon.execute('select tid,username,create_time,last_read_time,is_read from SnsTopItem_1 where username=?', (wx,)))
    print('  %s -> feed hits %d' % (wx, len(rr)))
    for r in rr[-10:]:
        print('     post=%s read=%s is_read=%s' % (fmt(r['create_time']), fmt(r['last_read_time']), r['is_read']))
    rr2 = list(scon.execute('select tid,user_name,content from SnsTimeLine where user_name=? or content like ?', (wx, '%'+wx+'%')))
    print('  SnsTimeLine hits', len(rr2))

print()
print('=== 今天(10-11) feed 全部条目 ===')
today0 = int(datetime.datetime(2026, 10, 11).timestamp())
rr = list(scon.execute('select tid,username,create_time,last_read_time,is_read from SnsTopItem_1 where create_time>=? order by create_time', (today0,)))
print('  count:', len(rr))
seen = {}
for r in rr:
    seen.setdefault(r['username'], []).append(r['create_time'])
for u, tsl in seen.items():
    print('   %-26s n=%d  %s .. %s' % (u, len(tsl), fmt(min(tsl)), fmt(max(tsl))))
