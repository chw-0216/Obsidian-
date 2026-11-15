# -*- coding: utf-8 -*-
r"""probe7.py —— 10-06 12:00 → 10-07 现在，全部关键会话"""
import sqlite3, datetime
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
names = {r["talker"]: r["display_name"] for r in con.execute("select talker, display_name from sessions")}
def f(ts): return datetime.datetime.fromtimestamp(ts).strftime("%m-%d %H:%M")
def cl(c):
    if not c: return ""
    if '<' in c:
        h=c.split('<')[0].strip()
        tag = "〔图〕" if '<img' in c else ("〔语音〕" if '<voicemsg' in c else ("〔视频〕" if '<videomsg' in c else ("〔表情〕" if '<emoji' in c else "〔卡片〕")))
        return (h[:110]+" "+tag) if h else tag
    return c.replace("\n"," ")[:170]

T0 = int(datetime.datetime(2026,10,6,12,0).timestamp())
T1 = int(datetime.datetime(2026,10,8,0,0).timestamp())

TARGETS = [
    ("6795601010@chatroom", "gay学现场群（高中同学）"),
    ("wxid_0ejd54z34nmv32", "舒泽林"),
    ("wxid_4e4mad0ve4fn22", "王逸伦"),
    ("wxid_g6ewa78cg30722", "王若彤"),
    ("wxid_5049180491911", "柯益盈"),
    ("wxid_vk33qtlz3yyn22", "金盏好修养极狐售后"),
    ("45219356839@chatroom", "T5-刘丽萍极狐专属服务群"),
    ("wxid_ptpc82ul5kw212", "极狐 小于儿"),
]
for sk, lab in TARGETS:
    rows = con.execute("select ts, role, content from messages where session_key=? and ts>=? and ts<? order by ts",
                       (sk, T0, T1)).fetchall()
    print("=" * 78)
    print("【%s】%d 条" % (lab, len(rows)))
    print("=" * 78)
    for r in rows:
        print("  [%s] %-4s %s" % (f(r["ts"]), "我" if r["role"]=="me" else ("他" if r["role"]=="them" else "sys"), cl(r["content"])))
    print()

# 全库：10-06 12:00 后「我」发过消息的私聊/小群
print("=" * 78)
print("★ 10-06 12:00 后，我在哪些会话发过言（非公众号）")
print("=" * 78)
for r in con.execute("""
  select session_key, count(*) n, min(ts) a, max(ts) b from messages
   where role='me' and ts>=? and ts<?
   group by session_key order by n desc""", (T0, T1)):
    nm = names.get(r["session_key"]) or r["session_key"]
    print("  %-34s 我 %3d 条  %s → %s" % (nm[:32], r["n"], f(r["a"]), f(r["b"])))
