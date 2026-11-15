# -*- coding: utf-8 -*-
import sqlite3, os
base = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
db = os.path.join(base, 'sns', 'sns.db')
con = sqlite3.connect('file:%s?mode=ro' % db.replace('\\', '/'), uri=True)
con.row_factory = sqlite3.Row
tabs = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
print('tables:')
for t in tabs:
    try:
        n = con.execute('select count(*) from "%s"' % t).fetchone()[0]
    except Exception as e:
        n = 'ERR %s' % e
    print('   %-28s %s' % (t, n))

for t in tabs:
    cur = con.execute('select * from "%s" limit 1' % t)
    print('\n== %s cols: %s' % (t, [d[0] for d in cur.description]))
    for r in con.execute('select * from "%s" limit 1' % t):
        d = dict(r)
        for k, v in d.items():
            sv = str(v)
            print('     %-22s %s' % (k, sv[:160]))
