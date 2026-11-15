# -*- coding: utf-8 -*-
r"""probe9.py —— ① Tripo 积分归属 ② 10-06 全天「反驳舒泽林」定位 ③ 何一沙 / 两个模式"""
import sqlite3, datetime
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
def f(ts): return datetime.datetime.fromtimestamp(ts).strftime("%y-%m-%d %H:%M:%S")
def cl(c):
    if not c: return ""
    if '<' in c:
        h = c.split('<')[0].strip()
        tag = "〔图〕" if '<img' in c else ("〔语音〕" if '<voicemsg' in c else ("〔视频〕" if '<videomsg' in c else ("〔表情〕" if '<emoji' in c else "〔卡片〕")))
        return (h[:150] + " " + tag) if h else tag
    return c.replace("\n", " ")[:220]

# ---------- ① Tripo 积分归属 ----------
print("#" * 90)
print("① Tripo 积分问题 · 谁发的？")
print("#" * 90)
for r in con.execute("select session_key, ts, role, sender, content from messages where content like '%积分问题附参赛邮箱%' or content like '%积分问题%' order by ts"):
    print("  sk=%s | %s | role=%s | sender=%s" % (r["session_key"], f(r["ts"]), r["role"], r["sender"]))
    print("     >>", cl(r["content"])[:300])

print()
print("--- Tripothon 群里本人(role=me)全部发言 ---")
for r in con.execute("select ts, content from messages where session_key like '%49893126997%' and role='me' order by ts"):
    print("  [%s] %s" % (f(r["ts"]), cl(r["content"])[:220]))

print()
print("--- Tripothon 群 10-01 之后全部 ---")
for r in con.execute("select ts, role, sender, content from messages where session_key like '%49893126997%' and ts>=? order by ts", (int(datetime.datetime(2026, 10, 1).timestamp()),)):
    print("  [%s] %-4s s=%s %s" % (f(r["ts"]), r["role"], (r["sender"] or "")[:28], cl(r["content"])[:200]))

# ---------- ② 10-06 全天 舒泽林 + gay学现场 ----------
print()
print("#" * 90)
print("② 10-06 00:00 → 10-08 全天 · 舒泽林 + gay学现场 + 王若彤 + 王逸伦")
print("#" * 90)
t0 = int(datetime.datetime(2026, 10, 6).timestamp())
t1 = int(datetime.datetime(2026, 10, 9).timestamp())
keys = {
    "6795601010@chatroom": "gay学现场群",
    "wxid_4e4mad0ve4fn22": "王逸伦",
}
for sk, lab in keys.items():
    print("-" * 78); print("【%s】%s" % (lab, sk))
    n = 0
    for r in con.execute("select ts, role, sender, content from messages where session_key=? and ts>=? and ts<? order by ts", (sk, t0, t1)):
        n += 1
        print("  [%s] %-4s s=%s %s" % (f(r["ts"]), r["role"], (r["sender"] or "")[:28], cl(r["content"])[:230]))
    print("  → %d 条" % n)

print()
print("--- 10-06 起 舒泽林相关会话（按 session 名含 舒 或已知 wxid）---")
for r in con.execute("select session_key, display_name, talker from sessions where display_name like '%舒%' or talker like '%舒%'"):
    print("  sk=%s | dn=%s | talker=%s" % (r["session_key"], r["display_name"], r["talker"]))

# ---------- ③ 何一沙 ----------
print()
print("#" * 90)
print("③ 何一沙 / 两个模式 / 建模")
print("#" * 90)
for r in con.execute("select session_key, display_name, talker, message_count from sessions where display_name like '%何一沙%' or display_name like '%Yisharlot%' or talker like '%Yisharlot%'"):
    print("  sk=%s | dn=%s | talker=%s | %s 条" % (r["session_key"], r["display_name"], r["talker"], r["message_count"]))

print()
print("--- 何一沙会话 全部（末 60 条）---")
for r in con.execute("select session_key from sessions where display_name like '%Yisharlot%' or display_name like '%何一沙%' limit 1"):
    sk = r["session_key"]
    rows = con.execute("select ts, role, content from messages where session_key=? order by ts", (sk,)).fetchall()
    print("  sk=%s 共 %d 条" % (sk, len(rows)))
    for x in rows[-60:]:
        print("  [%s] %-4s %s" % (f(x["ts"]), x["role"], cl(x["content"])[:200]))

print()
print("--- 关键词：建模 / 数字人 / Tripo / 积分 ---")
for kw in ["Tripo", "tripo", "积分", "何一莎", "何一沙", "数字人", "建模"]:
    rows = con.execute("select session_key, ts, role, content from messages where content like ? order by ts desc limit 8", ("%" + kw + "%",)).fetchall()
    print("  【%s】%d 命中（末 8）" % (kw, len(rows)))
    for r in rows:
        print("     [%s] %-4s %s | %s" % (f(r["ts"]), r["role"], r["session_key"][:30], cl(r["content"])[:150]))
