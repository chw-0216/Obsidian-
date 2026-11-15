# -*- coding: utf-8 -*-
r"""probe13.py —— 王义/gh_4fe8de031b84 · 10-06~10-07 全部会话 · 笑一/母亲近期"""
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
        return (h[:200] + " " + tag) if h else tag
    return c.replace("\n", " ")[:250]

print("### 1. gh_4fe8de031b84（王义/安鹏）会话")
r = con.execute("select talker, display_name, message_count, first_ts, last_ts from sessions where talker='gh_4fe8de031b84'").fetchone()
print("  ", dict(r) if r else "无")
for x in con.execute("select ts, role, content from messages where session_key='gh_4fe8de031b84' order by ts"):
    print("  [%s] %-4s %s" % (f(x["ts"]), "我" if x["role"] == "me" else ("他" if x["role"] == "them" else "sys"), cl(x["content"])))

print()
print("### 2. 10-06 00:00 → 10-07 12:00 全部会话逐条（本人相关）")
t0 = int(datetime.datetime(2026, 10, 6).timestamp())
t1 = int(datetime.datetime(2026, 10, 7, 12).timestamp())
rows = con.execute("""select m.session_key, s.display_name, m.ts, m.role, m.content
                      from messages m left join sessions s on s.talker=m.session_key
                      where m.ts>=? and m.ts<? order by m.ts""", (t0, t1)).fetchall()
from collections import Counter
c = Counter()
for r in rows: c[(r["session_key"], r["display_name"])] += 1
print("  活跃会话 %d 个，共 %d 条" % (len(c), len(rows)))
for (sk, dn), n in c.most_common(40):
    print("   %-32s %-24s %4d" % (sk[:32], (dn or "")[:24], n))

print()
print("### 3. 10-06 全天 · 笑一")
for r in con.execute("select ts, role, content from messages where session_key='wxid_wdnk6ue9kiyn22' and ts>=? and ts<? order by ts", (t0, t1)):
    print("  [%s] %-4s %s" % (f(r["ts"]), "我" if r["role"] == "me" else "他", cl(r["content"])[:200]))

print()
print("### 4. 10-06/10-07 · 文件传输助手（本人自言自语 = 决策输入）")
for r in con.execute("select ts, role, content from messages where session_key='filehelper' and ts>=? order by ts", (int(datetime.datetime(2026, 10, 5).timestamp()),)):
    print("  [%s] %-4s %s" % (f(r["ts"]), "我" if r["role"] == "me" else "他", cl(r["content"])[:400]))
