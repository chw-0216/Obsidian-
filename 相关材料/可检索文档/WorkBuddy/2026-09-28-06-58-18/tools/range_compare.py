# -*- coding: utf-8 -*-
"""新旧库分类型时间范围对照 + FTS 可用性验证"""
import datetime
import sqlite3

OLD = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
NEW = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index_v2.sqlite"

KINDS = {
    "私聊": "session_key NOT LIKE '%@chatroom%' AND session_key NOT LIKE 'gh\\_%' ESCAPE '\\' AND session_key NOT LIKE '%@openim%' AND session_key <> 'filehelper'",
    "群聊": "session_key LIKE '%@chatroom%'",
    "公众号": "session_key LIKE 'gh\\_%' ESCAPE '\\'",
    "企业微信": "session_key LIKE '%@openim%'",
    "filehelper": "session_key = 'filehelper'",
}


def fmt(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "-"


for label, path in (("旧 index", OLD), ("新 index_v2", NEW)):
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    cur = c.cursor()
    print(f"\n===== {label} =====")
    for k, cond in KINDS.items():
        cur.execute(f"SELECT COUNT(*), MIN(ts), MAX(ts) FROM messages WHERE {cond}")
        n, a, b = cur.fetchone()
        print(f"  {k:<10} {n:>7,}   {fmt(a)} → {fmt(b)}")
    c.close()

print("\n===== FTS 可用性（trigram 需 ≥3 字）=====")
for label, path in (("旧 index", OLD), ("新 index_v2", NEW)):
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    cur = c.cursor()
    for q in ("导师", "陈晔", "美术馆", "格拉斯哥"):
        try:
            n = cur.execute("SELECT COUNT(*) FROM messages_fts WHERE messages_fts MATCH ?", (q,)).fetchone()[0]
        except Exception as e:
            n = f"ERR {e}"
        print(f"  {label:<12} MATCH '{q}' → {n}")
    c.close()
