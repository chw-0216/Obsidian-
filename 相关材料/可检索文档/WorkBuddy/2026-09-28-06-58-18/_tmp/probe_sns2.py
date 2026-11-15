# -*- coding: utf-8 -*-
import sqlite3, os, datetime
base = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
db = os.path.join(base, 'sns', 'sns.db')
con = sqlite3.connect('file:%s?mode=ro' % db.replace('\\', '/'), uri=True)
con.row_factory = sqlite3.Row
M = 1 << 64
def ts_of(tid):
    return (tid % M) >> 23
def fmt(t):
    return datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S') if t else '-'

print('=== SnsTimeLine: 304 rows, time range ===')
rows = list(con.execute('select tid,user_name,content from SnsTimeLine'))
ts = sorted(ts_of(r['tid']) / 1000 for r in rows)
print('  range:', fmt(ts[0]), '->', fmt(ts[-1]))

for kw in ('周文娟', '文娟', '环球影城', '环球', '博文', '李博文'):
    hits = [r for r in rows if kw in (r['content'] or '')]
    print('  SnsTimeLine %-6s hits=%d' % (kw, len(hits)))

print()
print('=== SnsTopItem_1 (feed) keyword scan ===')
top = list(con.execute('select tid,username,summary,create_time,last_read_time,is_read from SnsTopItem_1'))
print('  rows:', len(top))
for kw in ('周文娟', '文娟', '环球影城', '环球'):
    hits = [r for r in top if kw in (r['summary'] or '')]
    print('  %-6s hits=%d' % (kw, len(hits)))

print()
print('=== SnsTopItem_1 最近 25 条（按 create_time desc）===')
for r in sorted(top, key=lambda x: x['create_time'] or 0, reverse=True)[:25]:
    print('  %s | %-22s | read=%s | %s' % (fmt(r['create_time']), r['username'],
          r['is_read'], (r['summary'] or '')[:60].replace('\n', ' ')))

print()
print('=== SnsMessage_tmp3 最近 30 条（点赞/评论）===')
msg = list(con.execute('select * from SnsMessage_tmp3 order by create_time desc limit 30'))
for r in msg:
    print('  %s | type=%s | from=%-24s(%s) | to=%-16s | rel_me=%s | c=%s' % (
        fmt(r['create_time']), r['type'], r['from_username'], (r['from_nickname'] or '')[:12],
        (r['to_username'] or '')[:16], r['is_relative_me'], (r['content'] or '')[:40]))
print('  total:', con.execute('select count(*) from SnsMessage_tmp3').fetchone()[0])
