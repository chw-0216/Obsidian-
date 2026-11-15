# -*- coding: utf-8 -*-
r"""probe10.py —— 舒泽林会话 / 何一沙 / 本人关键词（建模·数字人·Tripo·积分）"""
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
        return (h[:200] + " " + tag) if h else tag
    return c.replace("\n", " ")[:260]

print("#" * 90)
print("A. 找「舒泽林」会话 talker")
print("#" * 90)
for r in con.execute("select talker, display_name, session_type, message_count, first_ts, last_ts from sessions where display_name like '%舒%' or display_name like '%舒哥%'"):
    print("  talker=%s | dn=%s | %s | %d 条 | %s ~ %s" % (r["talker"], r["display_name"], r["session_type"], r["message_count"], f(r["first_ts"]) if r["first_ts"] else "-", f(r["last_ts"]) if r["last_ts"] else "-"))

print()
print("#" * 90)
print("B. 何一沙 / Yisharlot")
print("#" * 90)
for r in con.execute("select talker, display_name, session_type, message_count, first_ts, last_ts from sessions where display_name like '%何一沙%' or display_name like '%Yisharlot%' or display_name like '%一莎%'"):
    print("  talker=%s | dn=%s | %s | %d 条 | %s ~ %s" % (r["talker"], r["display_name"], r["session_type"], r["message_count"], f(r["first_ts"]) if r["first_ts"] else "-", f(r["last_ts"]) if r["last_ts"] else "-"))

print()
print("#" * 90)
print("C. 本人(role=me)关键词命中")
print("#" * 90)
for kw in ["建模", "数字人", "Tripo", "积分", "何一沙", "何一莎"]:
    rows = con.execute("select session_key, ts, content from messages where role='me' and content like ? order by ts desc limit 15", ("%" + kw + "%",)).fetchall()
    print("  【%s】本人发出 %d 条（末 15）" % (kw, len(rows)))
    for r in rows:
        print("     [%s] %-34s %s" % (f(r["ts"]), r["session_key"][:34], cl(r["content"])[:180]))
    print()

print("#" * 90)
print("D. 柯益盈 会话 meta + 首末")
print("#" * 90)
for r in con.execute("select talker, display_name, session_type, message_count, first_ts, last_ts from sessions where talker like '%5049180491911%'"):
    print("  talker=%s | dn=%s | %s | %d 条 | %s ~ %s" % (r["talker"], r["display_name"], r["session_type"], r["message_count"], f(r["first_ts"]), f(r["last_ts"])))
