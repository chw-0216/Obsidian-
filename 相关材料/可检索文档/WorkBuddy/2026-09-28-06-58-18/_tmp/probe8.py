# -*- coding: utf-8 -*-
r"""probe8.py —— 柯益盈 / 极狐安鹏 / 何一沙 / 文件传输助手 底账"""
import sqlite3, datetime
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
def f(ts): return datetime.datetime.fromtimestamp(ts).strftime("%y-%m-%d %H:%M")
def cl(c):
    if not c: return ""
    if '<' in c:
        h=c.split('<')[0].strip()
        tag = "〔图〕" if '<img' in c else ("〔语音〕" if '<voicemsg' in c else ("〔视频〕" if '<videomsg' in c else ("〔表情〕" if '<emoji' in c else "〔卡片〕")))
        return (h[:120]+" "+tag) if h else tag
    return c.replace("\n"," ")[:180]

def dump(sk, lab, limit=None, desc=False):
    q = "select ts, role, content from messages where session_key=? order by ts" + (" desc" if desc else "")
    rows = con.execute(q, (sk,)).fetchall()
    if desc: rows = list(reversed(rows))
    if limit: rows = rows[-limit:]
    print("=" * 78); print("【%s】共 %d 条%s" % (lab, len(rows), "（末 %d）" % limit if limit else "")); print("=" * 78)
    for r in rows:
        print("  [%s] %-4s %s" % (f(r["ts"]), "我" if r["role"]=="me" else ("他" if r["role"]=="them" else "sys"), cl(r["content"])))
    print()

dump("wxid_5049180491911", "柯益盈（高中三班）")
dump("wxid_vk33qtlz3yyn22", "金盏好修养极狐售后")
dump("45219356839@chatroom", "T5-刘丽萍极狐专属服务群")
