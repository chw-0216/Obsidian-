# -*- coding: utf-8 -*-
import sqlite3, datetime, sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
c = sqlite3.connect('file:C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite?mode=ro', uri=True)
K = 'wxid_1wa75s1kze3o22'

def dump(a, b, tag):
    print('=== %s ===' % tag)
    for ts, role, content in c.execute(
            'select ts,role,content from messages where session_key=? and ts between ? and ? order by ts',
            (K, a, b)):
        t = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
        print('%s %-5s %s' % (t, role, (content or '').replace('\n', ' ')[:110]))
    print()

dump(int(datetime.datetime(2026, 8, 18, 22, 50).timestamp()),
     int(datetime.datetime(2026, 8, 18, 23, 45).timestamp()),
     '2026-08-18 22:50-23:45 母亲会话')

dump(int(datetime.datetime(2026, 9, 22, 0, 0).timestamp()),
     int(datetime.datetime(2026, 9, 23, 0, 0).timestamp()),
     '2026-09-22 全天 母亲会话（找 250）')

dump(int(datetime.datetime(2026, 10, 8, 17, 0).timestamp()),
     int(datetime.datetime(2026, 10, 8, 19, 0).timestamp()),
     '2026-10-08 17:00-19:00 母亲会话（找 250）')
