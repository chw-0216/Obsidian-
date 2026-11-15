# -*- coding: utf-8 -*-
"""只读：核实是否存在其他 yifei 候选人"""
import sqlite3, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DB = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\contact\contact.db'
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
c = sqlite3.connect(f'file:{DB}?mode=ro', uri=True); c.execute('PRAGMA query_only=ON')
i = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True); i.execute('PRAGMA query_only=ON')

print('== contact：拼音/昵称/备注含 yifei/伊飞/一飞/弋斐/亦菲 ==')
q = """select username, nick_name, remark, quan_pin from contact
       where lower(quan_pin) like 'yifei%' or lower(nick_name) like '%yifei%'
          or nick_name like '%伊飞%' or nick_name like '%一飞%' or nick_name like '%弋斐%'
          or remark like '%伊飞%' or remark like '%一飞%' or remark like '%弋斐%'
       limit 60"""
for r in c.execute(q):
    print(r)
print('\n== 尚弋斐 / shenaijj520520 是否有私聊会话 ==')
for u in ['shenaijj520520']:
    print(u, i.execute('select talker, display_name, message_count from sessions where talker=?',(u,)).fetchall())
    r = c.execute('select username, nick_name, remark, quan_pin from contact where username=?',(u,)).fetchone()
    print('  contact:', r)
print('\n== 索引里所有 display_name 含 斐/菲/飞 且私聊 ==')
for r in i.execute("select talker, display_name, message_count from sessions where (display_name like '%斐%' or display_name like '%菲%') and session_type='私聊' order by message_count desc limit 20"):
    print(r)
