# -*- coding: utf-8 -*-
"""只读探查：社交拓扑映射 + 朋友圈互动全量 + 联系人表差异
   目标：把「谁和谁同群」「谁在关注他」两条线做实，为多轮交叉分析提供硬数据。
"""
import sqlite3, io, os

BASE = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted"
OUT = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\topo_sns.txt"
buf = io.StringIO()
def p(*a):
    buf.write(" ".join(str(x) for x in a) + "\n")

def ro(path):
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.text_factory = lambda b: b.decode('utf-8', 'ignore')
    return con

# ============ 一、chatroom_member 结构 + 桥映射 ============
con = ro(os.path.join(BASE, "contact", "contact.db"))
cur = con.cursor()
p("=" * 84)
p("一、★ chatroom_member 结构")
p("=" * 84)
for r in cur.execute("select sql from sqlite_master where name in ('chatroom_member','chat_room','chat_room_info_detail','contact')"):
    p(r[0]); p("-" * 40)

# 成员 id 能否对上 contact
p("")
p("★ contact 表列：")
cols = [d[1] for d in cur.execute("pragma table_info(contact)")]
p(cols)
p("★ contact 总数：", cur.execute("select count(*) from contact").fetchone()[0])

# 3641 是谁
p("")
p("★ chatroom_member 中 3641 / 343 / 586 是否对应 contact.rowid：")
for mid in (3641, 343, 586, 2362, 358):
    try:
        r = cur.execute("select rowid, username, local_type, remark, nick_name from contact where rowid=?", (mid,)).fetchone()
        p(f"  rowid={mid} -> {r}")
    except Exception as e:
        p(f"  rowid={mid} ERR {e}")

# 拿 SELF 的 rowid
p("")
for r in cur.execute("select rowid, username, remark, nick_name from contact where username='wxid_zn4ozsnn8esr21'"):
    p("★ SELF:", r)

# 群数量与成员数量
p("")
p("chatroom_member 行数：", cur.execute("select count(*) from chatroom_member").fetchone()[0])
p("chat_room 行数：", cur.execute("select count(*) from chat_room").fetchone()[0])

# 他所在的群 = 哪些群包含他的 rowid
self_rowid = None
r = cur.execute("select rowid from contact where username='wxid_zn4ozsnn8esr21'").fetchone()
if r:
    self_rowid = r[0]
    p("★ SELF rowid =", self_rowid)

# chatroom_member 列名
p("")
p("chatroom_member 列：", [d[1] for d in cur.execute("pragma table_info(chatroom_member)")])
p("")
p("样例 10 行：")
for r in list(cur.execute("select * from chatroom_member limit 10")):
    p("   ", r)

# ============ 二、朋友圈互动全量（SnsMessage_tmp3） ============
con2 = ro(os.path.join(BASE, "sns", "sns.db"))
cur2 = con2.cursor()
p("")
p("=" * 84)
p("二、★ 朋友圈互动 SnsMessage_tmp3 全量")
p("=" * 84)
for r in cur2.execute("select sql from sqlite_master where name like 'SnsMessage%' or name like 'SnsTimeLine%' or name like 'SnsTopItem%'"):
    p(r[0]); p("-" * 40)

p("")
p("★ SnsTimeLine 列：", [d[1] for d in cur2.execute("pragma table_info(SnsTimeLine)")])
p("★ SnsMessage_tmp3 列：", [d[1] for d in cur2.execute("pragma table_info(SnsMessage_tmp3)")])
p("★ SnsTopItem_1 列：", [d[1] for d in cur2.execute("pragma table_info(SnsTopItem_1)")])

con.close(); con2.close()

with open(OUT, "w", encoding="utf-8") as f:
    f.write(buf.getvalue())
print("ok", len(buf.getvalue()))
