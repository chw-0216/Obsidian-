# -*- coding: utf-8 -*-
"""噪音群清理 · 步骤 1：备份导出（只读，不删任何东西）。

导出 index.sqlite 里这两个刷单群的全部行到 _tmp/noise_backup_<ts>/
  - messages.jsonl   逐行完整记录（含 content / server_id / local_id）
  - sessions.json    对应的 sessions 行
  - manifest.json    计数 / 时间范围 / 校验和
"""
import hashlib
import json
import sqlite3
import time
from pathlib import Path

INDEX = Path(r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite")
NOISE = ["25410000808@chatroom", "18440588614@chatroom"]   # 北京家教信息 / 2026泰语学习群（暗黑）
OUT = Path(r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp") / ("noise_backup_" + time.strftime("%Y%m%d_%H%M%S"))
OUT.mkdir(parents=True, exist_ok=True)

con = sqlite3.connect(f"file:{INDEX}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()

cols = [r[1] for r in cur.execute("PRAGMA table_info(messages)")]
q = ("SELECT rowid AS _rowid, " + ", ".join(cols) + " FROM messages WHERE session_key IN (?,?) ORDER BY session_key, ts")
rows = cur.execute(q, NOISE).fetchall()

h = hashlib.sha256()
with (OUT / "messages.jsonl").open("w", encoding="utf-8") as f:
    for r in rows:
        line = json.dumps(dict(r), ensure_ascii=False)
        h.update(line.encode("utf-8"))
        f.write(line + "\n")

sess_cols = [r[1] for r in cur.execute("PRAGMA table_info(sessions)")]
srows = cur.execute(
    "SELECT " + ", ".join(sess_cols) + " FROM sessions WHERE talker IN (?,?)", NOISE).fetchall()
(OUT / "sessions.json").write_text(
    json.dumps([dict(r) for r in srows], ensure_ascii=False, indent=1), encoding="utf-8")

# FTS 侧同量级：统计待删 FTS 行数（不导出正文，正文已在 messages.jsonl）
fts_n = cur.execute(
    "SELECT COUNT(*) FROM messages_fts WHERE session_key IN (?,?)", NOISE).fetchone()[0]

per = {}
for r in rows:
    per.setdefault(r["session_key"], {"n": 0, "lo": r["ts"], "hi": r["ts"]})
    d = per[r["session_key"]]
    d["n"] += 1
    d["lo"] = min(d["lo"], r["ts"])
    d["hi"] = max(d["hi"], r["ts"])

manifest = {
    "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "index": str(INDEX),
    "index_bytes": INDEX.stat().st_size,
    "noise_sessions": NOISE,
    "messages_exported": len(rows),
    "fts_rows_matching": fts_n,
    "sha256_of_jsonl": h.hexdigest(),
    "per_session": {
        k: {
            "count": v["n"],
            "from": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(v["lo"])),
            "to": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(v["hi"])),
        } for k, v in per.items()
    },
    "sessions_rows": len(srows),
    "db_before": {
        "messages": cur.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
        "sessions": cur.execute("SELECT COUNT(*) FROM sessions").fetchone()[0],
        "distinct_sessions_in_messages": cur.execute("SELECT COUNT(DISTINCT session_key) FROM messages").fetchone()[0],
    },
}
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
con.close()

print("备份目录:", OUT)
print("导出 messages 行数 =", len(rows), "| FTS 匹配行数 =", fts_n, "| sessions 行数 =", len(srows))
print("sha256 =", h.hexdigest()[:24], "…")
for k, v in manifest["per_session"].items():
    print("   %-24s %5d 条  %s ~ %s" % (k, v["count"], v["from"], v["to"]))
print("清理前:", manifest["db_before"])
