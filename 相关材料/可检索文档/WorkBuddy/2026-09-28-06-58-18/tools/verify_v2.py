# -*- coding: utf-8 -*-
"""
对照验收：旧 index.sqlite vs 新 index_v2.sqlite
只读两个库，输出：条数 / 严格去重后 / 会话数 / 覆盖率 / 重复来源 / 抽样比对
用法：python tools/verify_v2.py
"""
from __future__ import annotations

import datetime
import sqlite3

OLD = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
NEW = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index_v2.sqlite"

# 源库可映射总行数（gap_by_session.py 实测）
SRC_TOTAL = 947355
SRC_NONSPAM = 335681
SPAM = {"25410000808@chatroom", "18440588614@chatroom"}


def probe(path, label):
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    cur = c.cursor()
    out = {"label": label, "path": path}
    cur.execute("SELECT COUNT(*) FROM messages")
    out["n"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM sessions")
    out["sess"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM (SELECT DISTINCT session_key,ts,role,sender,type,content FROM messages)")
    out["strict"] = cur.fetchone()[0]
    cur.execute("SELECT MAX(ts) FROM messages")
    out["last"] = cur.fetchone()[0]
    cols = [r[1] for r in cur.execute("PRAGMA table_info(messages)")]
    out["cols"] = cols
    # 类型分布
    dist = {}
    for kind, sql in (
        ("私聊", "session_key NOT LIKE '%@chatroom%' AND session_key NOT LIKE 'gh\\_%' ESCAPE '\\' AND session_key NOT LIKE '%@openim%'"),
        ("群聊", "session_key LIKE '%@chatroom%'"),
        ("公众号", "session_key LIKE 'gh\\_%' ESCAPE '\\'"),
        ("企业微信", "session_key LIKE '%@openim%'"),
        ("filehelper", "session_key = 'filehelper'"),
    ):
        dist[kind] = cur.execute(f"SELECT COUNT(*) FROM messages WHERE {sql}").fetchone()[0]
    out["dist"] = dist
    # 我发的
    out["me"] = cur.execute("SELECT COUNT(*) FROM messages WHERE role='me'").fetchone()[0]
    # FTS 是否可查
    try:
        out["fts"] = cur.execute("SELECT COUNT(*) FROM messages_fts WHERE messages_fts MATCH '导师'").fetchone()[0]
    except Exception as e:
        out["fts"] = f"ERR {e}"
    c.close()
    return out


def main():
    old = probe(OLD, "index.sqlite（旧）")
    new = probe(NEW, "index_v2.sqlite（新）")

    print("=" * 74)
    print(f"{'指标':<22}{'旧 index':>16}{'新 index_v2':>18}")
    print("=" * 74)
    rows = [
        ("messages 总条数", "n", "{:,}"),
        ("严格去重后", "strict", "{:,}"),
        ("重复条数", None, "{:,}"),
        ("sessions 会话数", "sess", "{:,}"),
        ("我发出的（role=me）", "me", "{:,}"),
    ]
    for name, key, fmt in rows:
        if key is None:
            a, b = old["n"] - old["strict"], new["n"] - new["strict"]
        else:
            a, b = old[key], new[key]
        print(f"{name:<22}{fmt.format(a):>16}{fmt.format(b):>18}")
    print(f"{'最新一条时间':<22}{str(datetime.datetime.fromtimestamp(old['last'])):>16}{str(datetime.datetime.fromtimestamp(new['last'])):>18}")
    print(f"{'messages 列':<22}{','.join(old['cols'])[:15]+'…':>16}{','.join(new['cols'])[:17]+'…':>18}")
    print(f"{'FTS 命中「导师」':<22}{str(old['fts']):>16}{str(new['fts']):>18}")

    print()
    print("=" * 74)
    print("类型分布")
    print("=" * 74)
    print(f"{'类型':<12}{'旧 index':>14}{'新 index_v2':>16}")
    for k in old["dist"]:
        print(f"{k:<12}{old['dist'][k]:>14,}{new['dist'][k]:>16,}")

    print()
    print("=" * 74)
    print("覆盖率")
    print("=" * 74)
    print(f"  旧 index：{old['n']:,} / {SRC_TOTAL:,} = {100.0*old['n']/SRC_TOTAL:.1f}%  （对全部源库）")
    print(f"  新 index_v2：{new['n']:,} / {SRC_NONSPAM:,} = {100.0*new['n']/SRC_NONSPAM:.1f}%  （对剔除刷屏群后的源库）")
    print(f"  已排除刷屏群：{', '.join(sorted(SPAM))}")


if __name__ == "__main__":
    raise SystemExit(main())
