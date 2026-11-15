# -*- coding: utf-8 -*-
import sqlite3, os, sys
base = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
db = os.path.join(base, 'contact', 'contact.db')
con = sqlite3.connect('file:%s?mode=ro' % db.replace('\\', '/'), uri=True)
con.row_factory = sqlite3.Row
tabs = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
print('tables:', tabs)
cur = con.execute('select * from contact limit 1')
print('cols:', [d[0] for d in cur.description])
for kw in ('周文娟', '文娟', '李博文', '博文'):
    rows = list(con.execute(
        'select * from contact where nick_name like ? or remark like ? or alias like ?',
        ('%' + kw + '%', '%' + kw + '%', '%' + kw + '%')))
    print('=== %s : %d' % (kw, len(rows)))
    for r in rows[:12]:
        print('   ', dict(r))
