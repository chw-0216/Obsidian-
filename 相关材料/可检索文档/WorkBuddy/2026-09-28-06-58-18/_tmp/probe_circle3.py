# -*- coding: utf-8 -*-
import sqlite3, io, datetime, json, collections

DEC = 'C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted'.replace('\\', '/')
IDX = 'C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite'
OUT = io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_circle3.txt', 'w', encoding='utf-8')
def P(*a):
    OUT.write(' '.join(str(x) for x in a) + '\n')

cd = sqlite3.connect('file:%s/contact/contact.db?mode=ro' % DEC, uri=True)
ix = sqlite3.connect('file:%s?mode=ro' % IDX, uri=True)

P('=== chatroom_member schema ===')
for r in cd.execute("pragma table_info(chatroom_member)"):
    P(r)

P()
P('=== contact 表 schema ===')
for r in cd.execute("pragma table_info(contact)"):
    P(r)

P()
P('=== index: me 的 sender 分布 ===')
for r in ix.execute("select sender, count(*) from messages where role='me' group by sender order by 2 desc limit 6"):
    P(r)

P()
P('=== 找本人（contact 里 remark/nick 含 蔡浩文） ===')
for r in cd.execute("select username,alias,remark,nick_name from contact where remark like '%蔡浩文%' or nick_name like '%蔡浩文%' or alias like '%蔡浩文%'"):
    P(r)

P()
P('=== 城院圈 13 人 wxid 对照 ===')
NAMES = ['程颂孟秋', '尹诗琪', '李博文', '李莉丽', '肖宇', '李子轩', '闻一青', '王婧潭', '裴青青', '蔡静文', '李澳', '张学鹏', '陈飞']
for nm in NAMES:
    for r in cd.execute("select username,remark,nick_name,alias from contact where remark like ? or nick_name like ?", ('%' + nm + '%', '%' + nm + '%')):
        P('%-10s | %s | %s | %s | %s' % (nm, r[0], r[1], r[2], r[3]))

OUT.close()
print('done')
