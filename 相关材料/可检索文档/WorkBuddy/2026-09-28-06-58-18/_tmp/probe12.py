# -*- coding: utf-8 -*-
r"""probe12.py —— 极狐三线 26-08 之后 + 安鹏/王义 + 保险报案链"""
import sqlite3, datetime
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
def f(ts): return datetime.datetime.fromtimestamp(ts).strftime("%y-%m-%d %H:%M")
def cl(c):
    if not c: return ""
    if '<' in c:
        h = c.split('<')[0].strip()
        tag = "〔图〕" if '<img' in c else ("〔语音〕" if '<voicemsg' in c else ("〔视频〕" if '<videomsg' in c else ("〔表情〕" if '<emoji' in c else "〔卡片〕")))
        return (h[:250] + " " + tag) if h else tag
    return c.replace("\n", " ")[:300]

print("### 1. 极狐三条线 meta")
for w in ["wxid_vk33qtlz3yyn22", "45219356839@chatroom", "wxid_ptpc82ul5kw212"]:
    r = con.execute("select talker, display_name, session_type, message_count, first_ts, last_ts from sessions where talker=?", (w,)).fetchone()
    if r: print("  %-24s %-34s %5d 条  %s ~ %s" % (w, r["display_name"], r["message_count"], f(r["first_ts"]), f(r["last_ts"])))

print()
print("### 2. 金盏好修养极狐售后 · 26-08-01 之后全部")
for r in con.execute("select ts, role, content from messages where session_key='wxid_vk33qtlz3yyn22' and ts>=? order by ts", (int(datetime.datetime(2026, 8, 1).timestamp()),)):
    print("  [%s] %-4s %s" % (f(r["ts"]), "我" if r["role"] == "me" else ("他" if r["role"] == "them" else "sys"), cl(r["content"])))

print()
print("### 3. T5 服务群 · 26-08-01 之后全部")
for r in con.execute("select ts, role, sender, content from messages where session_key='45219356839@chatroom' and ts>=? order by ts", (int(datetime.datetime(2026, 8, 1).timestamp()),)):
    print("  [%s] %-4s s=%s %s" % (f(r["ts"]), "我" if r["role"] == "me" else ("他" if r["role"] == "them" else "sys"), (r["sender"] or "")[:26], cl(r["content"])[:250]))

print()
print("### 4. 极狐 小于儿 · 末 40 条")
rows = con.execute("select ts, role, content from messages where session_key='wxid_ptpc82ul5kw212' order by ts").fetchall()
print("  （共 %d 条，末 40）" % len(rows))
for r in rows[-40:]:
    print("  [%s] %-4s %s" % (f(r["ts"]), "我" if r["role"] == "me" else ("他" if r["role"] == "them" else "sys"), cl(r["content"])[:250]))

print()
print("### 5. 关键词：安鹏 / 王义 / 报案 / 定损 / 返款 / 无忧 / 维修")
for kw in ["安鹏", "王义", "报案", "定损", "返款", "无忧", "维修", "理赔", "太平洋"]:
    rows = con.execute("select session_key, ts, role, content from messages where content like ? order by ts desc limit 10", ("%" + kw + "%",)).fetchall()
    print("  【%s】%d 命中（末 10）" % (kw, len(rows)))
    for r in rows:
        print("     [%s] %-4s %-30s %s" % (f(r["ts"]), "我" if r["role"] == "me" else "他", r["session_key"][:30], cl(r["content"])[:170]))
    print()
