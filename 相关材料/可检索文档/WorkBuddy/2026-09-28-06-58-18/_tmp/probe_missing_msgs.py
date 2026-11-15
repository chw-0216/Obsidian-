# -*- coding: utf-8 -*-
"""捞出「源库有、索引无」的那 5 条消息的内容。"""
import hashlib
import sqlite3
import time
from pathlib import Path

DEC_ROOT = Path(r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted")
INDEX = Path(r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite")
DBS = ["message_0.db", "message_1.db", "biz_message_0.db", "biz_message_1.db", "biz_message_2.db"]
TARGETS = {
    "deerluna": 7281,
    "wxid_8368913688512": 7,
    "wxid_1jx5zehp4f9u22": 1,
    "a26347050": 9,
}

try:
    import zstandard as zstd
    _d = zstd.ZstdDecompressor()
except Exception:
    _d = None


def dec(blob):
    if blob is None:
        return ""
    if isinstance(blob, str):
        return blob
    raw = bytes(blob)
    if not raw:
        return ""
    if _d:
        try:
            return _d.decompress(raw, max_output_size=1 << 24).decode("utf-8", "replace")
        except Exception:
            pass
    try:
        return raw.decode("utf-8")
    except Exception:
        return ""


idx = sqlite3.connect(f"file:{INDEX}?mode=ro", uri=True)
idx_ts = {}
for sid, ts in idx.execute("select session_key, ts from messages"):
    idx_ts.setdefault(sid, set()).add(ts)

for dbf in DBS:
    hits = list(DEC_ROOT.rglob(dbf))
    if not hits:
        continue
    con = sqlite3.connect(f"file:{hits[0]}?mode=ro", uri=True)
    idmap = {r[0]: r[1] for r in con.execute("SELECT rowid, user_name FROM Name2Id")}
    md5map = {hashlib.md5(n.encode()).hexdigest(): n for n in idmap.values()}
    for t in [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Msg\\_%' ESCAPE '\\'")]:
        sid = md5map.get(t[4:])
        if sid not in TARGETS:
            continue
        have = idx_ts.get(sid, set())
        rows = con.execute(
            'SELECT create_time, local_type, real_sender_id, message_content FROM "%s" ORDER BY create_time' % t
        ).fetchall()
        miss = [r for r in rows if r[0] not in have]
        print("=" * 70)
        print("%s  (%s)  源 %d 行 / 索引 %d 行 / 缺 %d 行" % (sid, dbf, len(rows), len(have), len(miss)))
        for ct, lt, rsid, blob in miss:
            who = idmap.get(rsid, "?")
            txt = dec(blob)
            txt = txt.replace("\n", " ")[:200]
            print("   [%s] local_type=%s sender=%s" % (
                time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ct)), lt, who))
            print("      %s" % txt)
    con.close()
