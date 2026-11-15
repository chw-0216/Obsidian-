# -*- coding: utf-8 -*-
"""只读探查 2：桥名单 + 我的群清单 + 朋友圈互动全量 + 联系人分层 + 语音分布
"""
import sqlite3, io, os
from collections import Counter, defaultdict

BASE = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted"
OUT = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\topo_sns2.txt"
SELF_ID = 3641
buf = io.StringIO()
def p(*a):
    buf.write(" ".join(str(x) for x in a) + "\n")

def ro(path):
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.text_factory = lambda b: b.decode('utf-8', 'ignore')
    return con

cc = ro(os.path.join(BASE, "contact", "contact.db"))
c1 = cc.cursor()

# ---------- 1. 联系人分层 ----------
p("=" * 84)
p("一、★ contact 表 42,708 人 分层（local_type）")
p("=" * 84)
lt = Counter(r[0] for r in c1.execute("select local_type from contact"))
p("local_type 分布：", dict(lt))
p("")
p("★ 各类型样例：")
for t in sorted(lt):
    rs = list(c1.execute("select username, remark, nick_name from contact where local_type=? limit 4", (t,)))
    p(f"  type={t} (n={lt[t]}):")
    for r in rs:
        p("      ", r)

# 有备注的人数
p("")
nb = c1.execute("select count(*) from contact where remark is not null and remark<>''").fetchone()[0]
p("★ 有 remark 的人数：", nb)

# ---------- 2. 桥名单（横跨多群，排除 SELF） ----------
p("")
p("=" * 84)
p("二、★ 社交拓扑「桥」TOP40（横跨群数，排除本人）")
p("=" * 84)
rows = list(c1.execute("""
    select m.member_id, count(distinct m.room_id) c
    from chatroom_member m
    where m.member_id <> ?
    group by m.member_id order by c desc limit 40
""", (SELF_ID,)))
for mid, c in rows:
    r = c1.execute("select username, local_type, remark, nick_name from contact where id=?", (mid,)).fetchone()
    if r:
        p(f"  {c:4d} 群  id={mid:6d}  remark={r[2]!r:20s} nick={r[3]!r:24s} u={r[0]}")
    else:
        p(f"  {c:4d} 群  id={mid:6d}  <contact 缺失>")

# ---------- 3. 我的群清单（含人数） ----------
p("")
p("=" * 84)
p("三、★ 他所在的群（702 个）按成员数 TOP40")
p("=" * 84)
gcnt = list(c1.execute("select room_id, count(*) c from chatroom_member group by room_id order by c desc limit 40"))
for rid, c in gcnt:
    r = c1.execute("select username from chat_room where id=?", (rid,)).fetchone()
    p(f"  {c:5d} 人  room={r[0] if r else rid}")

# ---------- 4. 朋友圈互动全量 ----------
cs = ro(os.path.join(BASE, "sns", "sns.db"))
c2 = cs.cursor()
p("")
p("=" * 84)
p("四、★ 朋友圈互动 SnsMessage_tmp3 —— 谁在给他点赞/评论")
p("=" * 84)
msgs = list(c2.execute("""
    select create_time, type, from_username, from_nickname, content, is_relative_me
    from SnsMessage_tmp3 order by create_time
"""))
p("总数：", len(msgs))
p("type 分布：", dict(Counter(m[1] for m in msgs)))
p("is_relative_me 分布：", dict(Counter(m[5] for m in msgs)))
p("")
cnt = Counter(m[3] or m[2] for m in msgs)
p("★ 互动次数 TOP30：")
for n, c in cnt.most_common(30):
    p(f"  {c:3d}  {n}")
p("")
p("★ 全部带 content 的互动（有实际留言）：")
for m in msgs:
    if m[4] and m[4].strip():
        import datetime
        t = datetime.datetime.fromtimestamp(m[0]).strftime('%Y-%m-%d %H:%M')
        p(f"  [{t}] {m[3]} : {m[4][:80]}")

# ---------- 5. SnsTopItem_1 ----------
p("")
p("=" * 84)
p("五、★ SnsTopItem_1 7436 条 —— 结构验证")
p("=" * 84)
rs = list(c2.execute("select tid, username, summary, create_time, is_read from SnsTopItem_1 order by create_time desc limit 5"))
for r in rs:
    p("  ", r)
p("")
p("★ username 是否 wxid 形态（前 10 个）：")
for r in list(c2.execute("select distinct username from SnsTopItem_1 limit 10")):
    p("  ", r[0])
cc.close(); cs.close()

with open(OUT, "w", encoding="utf-8") as f:
    f.write(buf.getvalue())
print("ok", len(buf.getvalue()))
