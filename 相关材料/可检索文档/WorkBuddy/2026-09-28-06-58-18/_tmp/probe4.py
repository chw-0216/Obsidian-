# -*- coding: utf-8 -*-
import os, sqlite3, datetime, re
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
GRP = "6795601010@chatroom"
idx = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
idx.row_factory = sqlite3.Row
names = {r["talker"]: r["display_name"] for r in idx.execute("select talker, display_name from sessions")}
def fmt(ts): return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
def clean(ct):
    if ct is None: return ""
    if '<img' in ct or '<msg' in ct or '<emoji' in ct or '<voicemsg' in ct or '<videomsg' in ct:
        head = ct.split('<')[0].strip()
        tag = "〔图片〕" if '<img' in ct else ("〔语音〕" if '<voicemsg' in ct else ("〔视频〕" if '<videomsg' in ct else ("〔表情〕" if '<emoji' in ct else "〔卡片〕")))
        return (head[:90] + " " + tag) if head else tag
    return ct.replace("\n", " ")[:220]
print("=== 群 2025-10 全部消息 ===")
t0 = int(datetime.datetime(2025,10,1).timestamp()); t1 = int(datetime.datetime(2025,11,1).timestamp())
for r in idx.execute("select ts, role, sender, content from messages where session_key=? and ts>=? and ts<? order by ts", (GRP, t0, t1)):
    who = "我" if r["role"]=="me" else (names.get(r["sender"]) or (r["sender"] or "?")[:14])
    print("[%s] %-8s %s" % (fmt(r["ts"]), who, clean(r["content"])))

print()
print("=== 王逸伦 私聊：全部消息的 sender/role 分布 ===")
for r in idx.execute("select role, count(*) n, min(ts) a, max(ts) b from messages where session_key='wxid_4e4mad0ve4fn22' group by role"):
    print("  %s: %d 条  %s → %s" % (r["role"], r["n"], fmt(r["a"])[:10], fmt(r["b"])[:10]))

print()
print("=== 三人私聊：我发占比 & 最近活跃 ===")
for sk, nm in [("wxid_4e4mad0ve4fn22","王逸伦"),("wxid_0ejd54z34nmv32","舒泽林"),("wxid_g6ewa78cg30722","王若彤")]:
    tot = idx.execute("select count(*) from messages where session_key=?",(sk,)).fetchone()[0]
    me  = idx.execute("select count(*) from messages where session_key=? and role='me'",(sk,)).fetchone()[0]
    mx  = idx.execute("select max(ts) from messages where session_key=?",(sk,)).fetchone()[0]
    days = (datetime.datetime(2026,10,6) - datetime.datetime.fromtimestamp(mx)).days
    print("  %-5s 总 %4d | 我发 %4d (%.0f%%) | 末条 %s | 距今 %d 天" % (nm, tot, me, 100.0*me/max(tot,1), fmt(mx)[:10], days))
