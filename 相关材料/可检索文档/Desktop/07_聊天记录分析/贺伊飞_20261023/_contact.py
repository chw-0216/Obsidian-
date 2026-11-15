# -*- coding: utf-8 -*-
"""只读：联系人库核实 贺伊飞 / 群名"""
import sqlite3, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DB = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\contact\contact.db'
c = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
c.execute('PRAGMA query_only=ON')
print('== tables ==')
for r in c.execute("select name from sqlite_master where type='table' order by name"):
    print(r[0])
print('\n== contact 表结构 ==')
for r in c.execute('pragma table_info(contact)'):
    print(r)
print('\n== 查 hyf782877122 ==')
try:
    cols = [x[1] for x in c.execute('pragma table_info(contact)')]
    for r in c.execute("select * from contact where username='hyf782877122'"):
        print(dict(zip(cols, r)))
except Exception as e:
    print('ERR', e)
print('\n== 查群 19944550391@chatroom ==')
try:
    for r in c.execute("select * from contact where username='19944550391@chatroom'"):
        print(dict(zip(cols, r)))
except Exception as e:
    print('ERR', e)
print('\n== 查 group/chatroom 名称表（若存在） ==')
for t in ['chatroom','group','contact_remark','stranger']:
    try:
        rows = c.execute(f"select * from {t} limit 3").fetchall()
        print(t, '->', rows)
    except Exception as e:
        print(t, 'ERR', e)
