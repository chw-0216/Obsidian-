# -*- coding: utf-8 -*-
"""索引补录器 —— 修 index-incremental.py 的根因漏条。

根因：index-incremental.py 只抓 `create_time > 全库最大ts - 60`。
      → 任何「发送时间早于当时水位、后来才补到源库」的消息会被**永久跳过**。
      → 已实测造成：陈晔 2 行（语音通话邀请）+ 3 个新好友问候 + 两个大群整段历史。

本脚本：扫源库全量 → 与索引做 (session_key, server_id) / (session_key, ts, content[:80], sender) 双重比对
        → 把缺失行按与索引器完全相同的规则补进去。

用法：
  python backfill_index.py                 # 只补「小缺口」会话（缺 < 5000 行）—— 安全默认
  python backfill_index.py --sessions a,b  # 只补指定会话
  python backfill_index.py --include-groups  # 连大群一起补（会大幅增长索引）
  python backfill_index.py --dry-run       # 只报告不写入
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sqlite3
import sys
import time
from pathlib import Path

try:
    import zstandard as zstd
except ImportError:
    zstd = None

DEC_ROOT = Path(r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted")
INDEX = Path(r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite")
MY = "wxid_zn4ozsnn8esr21_db45"
MY_ROOT = "wxid_zn4ozsnn8esr21"
DBS = ["message_0.db", "message_1.db", "biz_message_0.db", "biz_message_1.db", "biz_message_2.db"]

LOCAL_TYPE_MAP = {
    1: ("text", None), 3: ("image", "[图片]"), 34: ("voice", "[语音]"),
    43: ("video", "[视频]"), 47: ("sticker", "[表情]"), 48: ("location", "[位置]"),
    42: ("card", "[名片]"), 49: ("link", None), 50: ("voicecall", None),
    10000: ("system", None),
}
SENDER_PREFIX = re.compile(r"^([A-Za-z0-9_\-]{4,64}):\s")
_dctx = zstd.ZstdDecompressor() if zstd else None


def map_type(lt):
    if lt in LOCAL_TYPE_MAP:
        return LOCAL_TYPE_MAP[lt]
    if lt > 0xFFFFFFFF:
        low = lt & 0xFFFFFFFF
        if low in LOCAL_TYPE_MAP:
            return LOCAL_TYPE_MAP[low]
    return (f"type{lt}", None)


def printable(s):
    if not s:
        return False
    bad = sum(1 for ch in s if ord(ch) < 9 or (13 < ord(ch) < 32) or ch == "\ufffd")
    return bad / max(len(s), 1) < 0.05


def decode_content(blob):
    if blob is None:
        return ""
    if isinstance(blob, str):
        return blob
    raw = bytes(blob)
    if not raw:
        return ""
    if _dctx is not None:
        try:
            return _dctx.decompress(raw, max_output_size=1 << 24).decode("utf-8", "replace")
        except Exception:
            pass
    try:
        return raw.decode("utf-8")
    except Exception:
        return ""


def clean_xml(s):
    if not s:
        return ""
    if s.lstrip().startswith("<msg") or s.lstrip().startswith("<?xml"):
        def grab(tag):
            m = re.search(rf"<{tag}>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{tag}>", s, re.S)
            return (m.group(1).strip() if m else "")
        parts = [grab(t) for t in ("title", "des", "content")]
        parts = [p for p in parts if p]
        if parts:
            s = " | ".join(parts)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]{0,200}>", " ", s)).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", default="", help="逗号分隔，只补这些会话")
    ap.add_argument("--include-groups", action="store_true")
    ap.add_argument("--threshold", type=int, default=5000, help="默认只补缺行数 < 该值的会话")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    only = set(x for x in a.sessions.split(",") if x)

    idx = sqlite3.connect(INDEX)
    idx.execute("PRAGMA journal_mode=WAL")
    has_srv = any(r[1] == "server_id" for r in idx.execute("PRAGMA table_info(messages)"))
    # 去重键（与 index-incremental.py 完全同形）
    seen = set()
    for sk, ts, ct, sd in idx.execute(
            "SELECT session_key, ts, substr(content,1,80), COALESCE(sender,'') FROM messages"):
        seen.add((sk, ts, ct, sd))
    idx_cnt = dict(idx.execute("select session_key, count(*) from messages group by 1").fetchall())
    print("索引现状: %d 条 / %d 会话" % (sum(idx_cnt.values()), len(idx_cnt)))

    ins_msg = ("INSERT OR IGNORE INTO messages "
               "(session_key, ts, time_text, role, sender, type, content, server_id, local_id) "
               "VALUES (?,?,?,?,?,?,?,?,?)")
    ins_fts = "INSERT INTO messages_fts (content, sender, session_key) VALUES (?,?,?)"

    # ---- Pass 1: 只数行数（轻），决定补哪些会话 ----
    t0 = time.time()
    handles = {}          # dbf -> (con, idmap, md5map)
    tab_index = []        # (sid, table, dbf, is_group, src_n)
    for dbf in DBS:
        hits = list(DEC_ROOT.rglob(dbf))
        if not hits:
            continue
        con = sqlite3.connect(f"file:{hits[0]}?mode=ro", uri=True)
        idmap = {r[0]: r[1] for r in con.execute("SELECT rowid, user_name FROM Name2Id")}
        md5map = {hashlib.md5(n.encode()).hexdigest(): n for n in idmap.values()}
        handles[dbf] = (con, idmap, md5map)
        tabs = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Msg\\_%' ESCAPE '\\'")]
        for t in tabs:
            sid = md5map.get(t[4:])
            if not sid:
                continue
            n = con.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0]
            tab_index.append((sid, t, dbf, sid.endswith("@chatroom"), n))

    # 按会话汇总源库行数
    src_cnt = {}
    for sid, t, dbf, isg, n in tab_index:
        src_cnt[sid] = src_cnt.get(sid, 0) + n

    plan = []
    for sid, t, dbf, isg, n in tab_index:
        if only and sid not in only:
            continue
        miss_n = src_cnt.get(sid, 0) - idx_cnt.get(sid, 0)
        if miss_n <= 0:
            continue
        if not only and not a.include_groups and miss_n >= a.threshold:
            if sid not in [p[0] for p in plan]:
                print("  [跳过·大缺口] %-34s 缺约 %d 行（加 --include-groups 或 --sessions 处理）" % (sid, miss_n))
            continue
        plan.append((sid, t, dbf, isg))
    print("扫描耗时 %.1f 秒，待处理表 %d 个 / 会话 %d 个" % (time.time() - t0, len(plan), len({p[0] for p in plan})))

    # ---- Pass 2: 只读待处理表 ----
    total_ins = 0
    sess_delta = {}
    for sid, t, dbf, is_group in plan:
        con, idmap, md5map = handles[dbf]
        rows = con.execute(
            'SELECT create_time, real_sender_id, local_type, message_content, local_id, server_id '
            f'FROM "{t}"').fetchall()
        batch = []
        for ct, rsid, ltype, blob, lid, srv in rows:
            lt = int(ltype or 0)
            wf_type, placeholder = map_type(lt)
            text = clean_xml(decode_content(blob))
            if not printable(text):
                text = ""
            if not text:
                text = placeholder or f"[type{lt}]"
            sender = ""
            if is_group:
                m = SENDER_PREFIX.match(text)
                if m:
                    sender = m.group(1)
                    text = text[m.end():].strip() or text
                elif rsid and (idmap.get(rsid) or "").startswith(MY_ROOT):
                    sender = "我"
            else:
                who = (idmap.get(rsid) or "") if rsid else ""
                if who.startswith(MY_ROOT) or who == MY:
                    sender = "我"
                elif who and not who.endswith("@chatroom"):
                    sender = who
                else:
                    sender = sid
            role = "me" if sender == "我" else ("system" if lt == 10000 else "them")
            key = (sid, ct, text[:80], sender)
            if key in seen:
                continue
            seen.add(key)
            batch.append((sid, ct, "", role, sender, wf_type, text, int(srv or 0), int(lid or 0)))
        if batch:
            if not a.dry_run:
                cur = idx.cursor()
                cur.executemany(ins_msg, batch)
                cur.executemany(ins_fts, [(b[6], b[4], b[0]) for b in batch])
                idx.commit()
            total_ins += len(batch)
            sess_delta[sid] = sess_delta.get(sid, 0) + len(batch)
            print("  ✓ %-34s 补入 %d 行" % (sid, len(batch)))

    print("\n合计补入 %d 行 / %d 会话" % (total_ins, len(sess_delta)))
    if not a.dry_run and total_ins:
        # 重算受影响会话的 message_count
        cur = idx.cursor()
        for sid in sess_delta:
            cur.execute("UPDATE sessions SET message_count=(SELECT COUNT(*) FROM messages WHERE session_key=?) WHERE talker=?", (sid, sid))
        idx.commit()
    after = idx.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    print("索引现状: %d 条" % after)
    idx.close()
    for con, _, _ in handles.values():
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
