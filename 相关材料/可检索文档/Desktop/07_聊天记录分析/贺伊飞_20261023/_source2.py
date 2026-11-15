# -*- coding: utf-8 -*-
"""只读：源库核对 v2（微信4.x 解密库 schema）"""
import sqlite3, hashlib, datetime, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
BASE = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\message'
TZ = datetime.timezone(datetime.timedelta(hours=8))
def ts(t): return datetime.datetime.fromtimestamp(int(t), tz=TZ).strftime('%Y-%m-%d %H:%M:%S')
p = BASE + r'\message_1.db'
c = sqlite3.connect(f'file:{p}?mode=ro', uri=True); c.execute('PRAGMA query_only=ON')
print('== tables ==')
for r in c.execute("select name from sqlite_master where type='table' order by name"):
    print(r[0])
tbl = 'Msg_' + hashlib.md5(b'hyf782877122').hexdigest()
print('\ntarget table:', tbl)
try:
    n = c.execute(f'select count(*) from "{tbl}"').fetchone()[0]
    print('rows:', n)
    print('sample:', c.execute(f'select * from "{tbl}" limit 2').fetchall())
except Exception as e:
    print('ERR', e)
