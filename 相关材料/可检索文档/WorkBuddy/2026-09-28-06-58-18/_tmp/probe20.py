# -*- coding: utf-8 -*-
r"""probe20.py —— gay学现场群 10-05~10-07 全文 + 舒泽林私聊图片本地文件定位"""
import sqlite3, datetime, os, glob
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
def f(ts): return datetime.datetime.fromtimestamp(ts).strftime("%y-%m-%d %H:%M:%S")

print("#"*96); print("① 找 gay学现场 群 talker"); print("#"*96)
for r in con.execute("select talker, display_name, message_count, last_ts from sessions where display_name like '%gay%' or display_name like '%学现场%'"):
    print("   ", dict(r))

print(); print("#"*96); print("② gay学现场 10-05 → 现在 全文"); print("#"*96)
t0 = int(datetime.datetime(2026,10,5,0,0).timestamp())
rows = con.execute("select session_key, ts, role, type, sender, content from messages where session_key in (select talker from sessions where display_name like '%gay%') and ts>=? order by ts", (t0,)).fetchall()
for r in rows:
    c = (r["content"] or "")
    print("  [%s] %-6s %-8s %s" % (f(r["ts"]), r["role"], r["type"], c.replace("\n"," ")[:200]))

print(); print("#"*96); print("③ 舒泽林 10-06→10-07 图片/视频消息 XML 详情"); print("#"*96)
rows2 = con.execute("select ts, role, type, content from messages where session_key='wxid_0ejd54z34nmv32' and ts>=? and (type in ('image','video') or content like '%img%' or content like '%videomsg%') order by ts",
                    (int(datetime.datetime(2026,10,6,0,0).timestamp()),)).fetchall()
for r in rows2:
    print("-"*88)
    print("[%s] %s %s" % (f(r["ts"]), r["role"], r["type"]))
    print((r["content"] or "")[:2000])

print(); print("#"*96); print("④ index.sqlite 目录结构 + 找 media/attach 目录"); print("#"*96)
base = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp"
for p in sorted(glob.glob(base + "/*")):
    print("   %s%s" % (p, "/" if os.path.isdir(p) else ""))
