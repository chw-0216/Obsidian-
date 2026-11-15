# -*- coding: utf-8 -*-
r"""dump_gayxue.py —— 拉「gay学现场」群 + 三人私聊"""
import os, sqlite3, datetime, re, io, sys

DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
con = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row

def fmt(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

# 群 id
GRP = None
for r in con.execute("select talker, display_name from sessions where display_name like '%gay学现场%'"):
    print("群：%s | %s" % (r["display_name"], r["talker"]))
    GRP = r["talker"]

# 全库会话名映射（含私聊，用来把群里的 wxid 翻译成人名）
names = {}
for r in con.execute("select talker, display_name from sessions"):
    names[r["talker"]] = r["display_name"]

IMG = re.compile(r'<img\b.*?(?:/>|</img>)', re.S)
def clean(ct):
    if ct is None:
        return ""
    if '<img' in ct or '<msg' in ct:
        head = ct.split('<')[0].strip()
        return (head[:70] + " 〔图片/附件〕") if head else "〔图片/附件〕"
    return ct.replace("\n", " ")[:160]

print()
print("=" * 78)
print("① 「gay学现场」群 · 2026-09-01 起全部消息")
print("=" * 78)
t0 = int(datetime.datetime(2026, 9, 1).timestamp())
for r in con.execute(
        "select ts, role, sender, content from messages "
        "where session_key=? and ts>=? order by ts", (GRP, t0)):
    who = "我" if r["role"] == "me" else (names.get(r["sender"]) or (r["sender"] or "?")[:16])
    print("[%s] %-8s %s" % (fmt(r["ts"]), who, clean(r["content"])))

print()
print("=" * 78)
print("② 王逸伦 私聊 · 全部（108 条）")
print("=" * 78)
for r in con.execute(
        "select ts, role, content from messages where session_key=? order by ts",
        ("wxid_4e4mad0ve4fn22",)):
    who = "我" if r["role"] == "me" else "王逸伦"
    print("[%s] %-6s %s" % (fmt(r["ts"]), who, clean(r["content"])))

print()
print("=" * 78)
print("③ 王若彤 私聊 · 最近 60 条")
print("=" * 78)
rows = con.execute(
    "select ts, role, content from messages where session_key=? order by ts desc limit 60",
    ("wxid_g6ewa78cg30722",)).fetchall()
for r in reversed(rows):
    who = "我" if r["role"] == "me" else "王若彤"
    print("[%s] %-6s %s" % (fmt(r["ts"]), who, clean(r["content"])))

print()
print("=" * 78)
print("④ 舒泽林 私聊 · 最近 60 条")
print("=" * 78)
rows = con.execute(
    "select ts, role, content from messages where session_key=? order by ts desc limit 60",
    ("wxid_0ejd54z34nmv32",)).fetchall()
for r in reversed(rows):
    who = "我" if r["role"] == "me" else "舒泽林"
    print("[%s] %-6s %s" % (fmt(r["ts"]), who, clean(r["content"])))
