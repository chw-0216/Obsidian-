# -*- coding: utf-8 -*-
r"""probe3.py —— 群成员 + 群活跃度 + 全员逐月"""
import os, sqlite3, datetime, re

IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
DEC = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted"
GRP = "6795601010@chatroom"

def fmt(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

idx = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
idx.row_factory = sqlite3.Row
names = {r["talker"]: r["display_name"] for r in idx.execute("select talker, display_name from sessions")}

print("=" * 78)
print("① 群成员表（contact.db chatroom_member）")
print("=" * 78)
c = sqlite3.connect("file:" + os.path.join(DEC, "contact", "contact.db").replace("\\", "/") + "?mode=ro", uri=True)
c.row_factory = sqlite3.Row
print("chatroom_member 列：", [r[1] for r in c.execute("pragma table_info(chatroom_member)")])
rows = c.execute("select room_id, member_id from chatroom_member "
                 "where room_id like '%6795601010%' or room_id like '%679560101%'").fetchall()
print("成员数：", len(rows))
for r in rows:
    q = c.execute("select remark, nick_name from contact where username=?", (r["member_id"],)).fetchone()
    print("  %-28s 备注=%s 昵称=%s" % (r["member_id"], q[0] if q else None, q[1] if q else None))

print()
print("=" * 78)
print("② 群内各人发言量（2024-11 起）")
print("=" * 78)
for r in idx.execute(
        "select sender, role, count(*) n, min(ts) a, max(ts) b from messages "
        "where session_key=? group by sender, role order by n desc", (GRP,)):
    s = r["sender"] or "(空)"
    nm = names.get(s) or ("我自己" if r["role"] == "me" else s)
    print("  %-34s %-8s %5d  %s → %s" % (s, nm, r["n"], fmt(r["a"])[:10], fmt(r["b"])[:10]))

print()
print("=" * 78)
print("③ 群逐月消息量（全部历史）")
print("=" * 78)
bym = {}
for r in idx.execute("select ts, role, sender from messages where session_key=?", (GRP,)):
    m = datetime.datetime.fromtimestamp(r["ts"]).strftime("%Y-%m")
    d = bym.setdefault(m, {"n": 0, "me": 0})
    d["n"] += 1
    if r["role"] == "me":
        d["me"] += 1
for m in sorted(bym):
    print("  %s  共 %4d 条  我 %3d 条  %s" % (m, bym[m]["n"], bym[m]["me"], "█" * min(60, bym[m]["n"] // 2)))

print()
print("=" * 78)
print("④ 群 2026 年全部消息（含纯文本）")
print("=" * 78)
IMG = re.compile(r'<img\b.*?(?:/>|</img>)', re.S)
def clean(ct):
    if ct is None:
        return ""
    if '<img' in ct or '<msg' in ct or '<emoji' in ct or '<voicemsg' in ct or '<videomsg' in ct:
        head = ct.split('<')[0].strip()
        tag = "〔图片〕" if '<img' in ct else ("〔语音〕" if '<voicemsg' in ct else
              ("〔视频〕" if '<videomsg' in ct else ("〔表情〕" if '<emoji' in ct else "〔卡片〕")))
        return (head[:80] + " " + tag) if head else tag
    return ct.replace("\n", " ")[:200]

t0 = int(datetime.datetime(2026, 1, 1).timestamp())
for r in idx.execute("select ts, role, sender, content from messages "
                     "where session_key=? and ts>=? order by ts", (GRP, t0)):
    who = "我" if r["role"] == "me" else (names.get(r["sender"]) or (r["sender"] or "?")[:14])
    print("[%s] %-8s %s" % (fmt(r["ts"]), who, clean(r["content"])))
