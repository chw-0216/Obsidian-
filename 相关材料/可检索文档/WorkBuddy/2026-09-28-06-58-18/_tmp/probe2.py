# -*- coding: utf-8 -*-
r"""probe2.py —— 群成员 + 转账核对 + 群历史"""
import os, sqlite3, datetime, re, glob

DEC = r"C:\Users\wardc\AppData\Local\Cache\..\..\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted"
DEC = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted"
IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"

def fmt(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

# ---------- ① 群成员 ----------
idx = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
idx.row_factory = sqlite3.Row
names = {r["talker"]: r["display_name"] for r in idx.execute("select talker, display_name from sessions")}

print("=" * 78)
print("① 「gay学现场」群成员（contact.db chatroom_member）")
print("=" * 78)
c = sqlite3.connect("file:" + os.path.join(DEC, "contact", "contact.db").replace("\\", "/") + "?mode=ro", uri=True)
c.row_factory = sqlite3.Row
try:
    for r in c.execute("select room_id, member_id from chatroom_member where room_id like '%6795601010%'"):
        mid = r[1]
        nm = names.get(mid) if 'names' in dir() else None
        try:
            q = c.execute("select remark, nick_name from contact where username=?", (mid,)).fetchone()
        except Exception:
            q = None
        print("  %-28s 会话名=%s | 备注=%s | 昵称=%s" % (mid, nm, q[0] if q else None, q[1] if q else None))
except Exception as e:
    print("!!", e)
    # 模糊找
    for t in [r[0] for r in c.execute("select name from sqlite_master where type='table'")]:
        if "member" in t.lower() or "chatroom" in t.lower():
            print(" 表:", t)

# 群成员名字（从 contact 表）
print()
print("--- 群内出现过的 sender 翻译 ---")
GRP = "6795601010@chatroom"
senders = [r[0] for r in idx.execute(
    "select distinct sender from messages where session_key=? and sender is not null", (GRP,))]
for s in senders:
    nm = names.get(s)
    extra = ""
    if not nm:
        for r in c.execute("select remark, nick_name from contact where username=?", (s,)):
            extra = " (备注=%s / 昵称=%s)" % (r[0], r[1])
    print("  %-28s → %s%s" % (s, nm or "?", extra))

# ---------- ② 转账核对 ----------
print()
print("=" * 78)
print("② 转账核对：王逸伦 / 舒泽林 / 王若彤")
print("=" * 78)
for f in sorted(glob.glob(os.path.join(DEC, "general", "*.db"))):
    print("库:", os.path.basename(f))
    g = sqlite3.connect("file:" + f.replace("\\", "/") + "?mode=ro", uri=True)
    g.row_factory = sqlite3.Row
    tabs = [r[0] for r in g.execute("select name from sqlite_master where type='table'")]
    for t in tabs:
        if "transfer" in t.lower() or "redenv" in t.lower():
            cols = [r[1] for r in g.execute("pragma table_info(%s)" % t)]
            print("  [%s] 列: %s" % (t, cols))
            n = g.execute("select count(*) from %s" % t).fetchone()[0]
            print("     行数:", n)
            for r in g.execute("select rowid, * from %s order by rowid" % t):
                d = dict(r)
                print("     ", {k: (str(v)[:70] if v is not None else None)
                                for k, v in d.items() if k != "rowid"})
    g.close()

# ---------- ③ 群里搜「借 / 还 / 钱 / 400 / 500」 ----------
print()
print("=" * 78)
print("③ 三人会话里搜 借/还/欠/400/500/借条")
print("=" * 78)
for sk, label in [("wxid_4e4mad0ve4fn22", "王逸伦"), ("wxid_0ejd54z34nmv32", "舒泽林"),
                  ("wxid_g6ewa78cg30722", "王若彤"), (GRP, "gay学现场群")]:
    print("--- %s ---" % label)
    for r in idx.execute(
            "select ts, role, content from messages where session_key=? and ("
            "content like '%借%' or content like '%还%' or content like '%欠%' "
            "or content like '%400%' or content like '%500%' or content like '%转账%') order by ts",
            (sk,)):
        ct = (r["content"] or "").replace("\n", " ")[:110]
        who = "我" if r["role"] == "me" else ("他" if r["role"] == "them" else "sys")
        print("  [%s] %-4s %s" % (fmt(r["ts"]), who, ct))
    print()
