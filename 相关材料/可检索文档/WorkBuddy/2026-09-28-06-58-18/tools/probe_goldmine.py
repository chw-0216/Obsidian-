# -*- coding: utf-8 -*-
"""探查 5 个高价值未开发表：好友申请 / 转账 / 红包 / 朋友圈 / 群成员"""
import sqlite3, os, io, datetime

DEC = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
out = io.StringIO()


def t2s(ts, ms=False):
    try:
        v = int(ts)
        if ms or v > 10_000_000_000:
            v = v / 1000
        return datetime.datetime.fromtimestamp(v).strftime('%Y-%m-%d %H:%M')
    except Exception:
        return str(ts)


def dump(rel, sql, label, args=(), conv=None):
    p = os.path.join(DEC, rel.replace('/', os.sep))
    out.write(f'\n{"="*78}\n### {label}   {rel}\n{"="*78}\n')
    try:
        con = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
        for i, row in enumerate(con.execute(sql, args)):
            if conv:
                row = conv(row)
            out.write('  ' + ' | '.join(str(x)[:70] for x in row) + '\n')
            if i > 60:
                out.write('  ...(截断)\n')
                break
        con.close()
    except Exception as e:
        out.write(f'  !! {e}\n')


# 1. 好友申请 —— 终于能回答「谁加他」
dump('general/general.db',
     'select user_name_, type_, timestamp_, content_, is_sender_, scene_, remark_ from FMessageTable order by timestamp_ desc',
     '★ 好友申请 FMessageTable（is_sender_=1 表示他发出）')

# 2. 转账
dump('general/general.db',
     'select transfer_id, session_name, pay_payer, pay_receiver, begin_transfer_time, invalid_time, last_update_time from transferTable order by begin_transfer_time desc',
     '★ 转账 transferTable')

# 3. 红包
dump('general/general.db',
     'select message_server_id, session_name, sender_user_name, hb_status, hb_type, receive_status from redEnvelopeTable',
     '红包 redEnvelopeTable')

# 4. 搜索记录
dump('general/general.db', 'select keyword, create_time from websearch_record',
     '微信内搜索 websearch_record')

# 5. 朋友圈条目
dump('sns/sns.db',
     'select tid, username, substr(summary,1,40), create_time from SnsTopItem_1 order by create_time desc limit 40',
     '★ 朋友圈 SnsTopItem_1（倒序前 40）')

# 6. 群成员样本
dump('contact/contact.db',
     'select room_id, count(*) c from chatroom_member group by room_id order by c desc limit 25',
     '★ 群成员数 TOP25')

# 7. 群公告
dump('contact/contact.db',
     'select username_, substr(announcement_,1,60), announcement_publish_time_ from chat_room_info_detail where announcement_ is not null and length(announcement_)>10 order by announcement_publish_time_ desc limit 25',
     '★ 群公告（有内容的）')

# 8. 标签定义
dump('contact/contact.db', 'select label_id_, label_name_, sort_order_ from contact_label order by sort_order_',
     '通讯录标签定义 contact_label')

open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\goldmine.txt', 'w', encoding='utf-8').write(out.getvalue())
print('ok', len(out.getvalue()))
