# -*- coding: utf-8 -*-
"""
索引重建（去重正解版）—— 只读源库，写一个**新**索引文件，不碰现有 index.sqlite。

为什么重建而不是打补丁：
  1) 现有 index.sqlite **没有 server_id 列**，无法做精确去重，只能靠内容字符串猜
  2) 现有索引只覆盖源库 **34%**（群聊仅 15.4%），因为 index-incremental.py 只读
     `create_time > before_max - 60`，**从不回填历史**
  3) 源库有稳定主键 server_id（实测 100% 有值、全局唯一）→ 用它去重是**精确的**，无启发式

用法：
  python tools/rebuild_index.py --dry     # 只统计，不解码，秒级
  python tools/rebuild_index.py --apply   # 真正重建（写 index_v2.sqlite）
  python tools/rebuild_index.py --apply --exclude=25410000808@chatroom,18440588614@chatroom
                                          # 排除刷屏群（占全部缺口的 96%，且他 0 发言）
"""
from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import sys
import time

DEC = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted"
CONTACT_DB = os.path.join(DEC, "contact", "contact.db")
OUT = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index_v2.sqlite"
PAT = "name LIKE 'Msg\\_%' ESCAPE '\\'"
DBS = ["message_0.db", "message_1.db", "biz_message_0.db", "biz_message_1.db", "biz_message_2.db"]
MY_ROOT = "wxid_zn4ozsnn8esr21"
SENDER_PREFIX = re.compile(r"^([A-Za-z0-9_\-]{4,64}):\s")

try:
    import zstandard as zstd
    _dctx = zstd.ZstdDecompressor()
except ImportError:
    _dctx = None

LOCAL_TYPE_MAP = {
    1: ("text", None), 3: ("image", "[图片]"), 34: ("voice", "[语音]"),
    43: ("video", "[视频]"), 47: ("sticker", "[表情]"), 48: ("location", "[位置]"),
    42: ("card", "[名片]"), 49: ("link", None), 50: ("voicecall", None), 10000: ("system", None),
}


def map_type(lt):
    if lt in LOCAL_TYPE_MAP:
        return LOCAL_TYPE_MAP[lt]
    if lt > 0xFFFFFFFF:
        low = lt & 0xFFFFFFFF
        if low in LOCAL_TYPE_MAP:
            return LOCAL_TYPE_MAP[low]
    return (f"type{lt}", None)


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
            return m.group(1).strip() if m else ""
        parts = [p for p in (grab(t) for t in ("title", "des", "content")) if p]
        if parts:
            s = " | ".join(parts)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]{0,200}>", " ", s)).strip()


def printable(s):
    if not s:
        return False
    bad = sum(1 for ch in s if ord(ch) < 9 or (13 < ord(ch) < 32) or ch == "\ufffd")
    return bad / max(len(s), 1) < 0.05


def load_names():
    """通讯录 → {username: 显示名}。★ 必须做，否则 sessions.display_name 会退化成 wxid，
    下游导出的文件名 / accountName 全变成机器 id（2026-10-04 踩过）。"""
    m = {}
    if not os.path.exists(CONTACT_DB):
        return m
    c = sqlite3.connect(f"file:{CONTACT_DB}?mode=ro", uri=True)
    try:
        for u, remark, nick in c.execute("SELECT username, remark, nick_name FROM contact"):
            if not u:
                continue
            nm = (remark or "").strip() or (nick or "").strip()
            if nm:
                m[u] = nm
    except Exception:
        pass
    c.close()
    return m


def main():
    dry = "--dry" in sys.argv
    if not dry and "--apply" not in sys.argv:
        print("需要 --dry 或 --apply", file=sys.stderr)
        return 1

    # --exclude=a,b  排除指定会话（刷屏群）
    EXCLUDE = set()
    for a in sys.argv:
        if a.startswith("--exclude="):
            EXCLUDE = {x.strip() for x in a.split("=", 1)[1].split(",") if x.strip()}
    if EXCLUDE:
        print(f"排除会话 {len(EXCLUDE)} 个：{', '.join(sorted(EXCLUDE))}")

    if not dry:
        if os.path.exists(OUT):
            os.remove(OUT)
        db = sqlite3.connect(OUT)
        db.execute("PRAGMA journal_mode=OFF")
        db.execute("PRAGMA synchronous=OFF")
        db.executescript("""
            CREATE TABLE messages(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              session_key TEXT, ts INTEGER, time_text TEXT,
              role TEXT, sender TEXT, type TEXT, content TEXT,
              server_id INTEGER, local_id INTEGER);
            -- ★ 精确去重：server_id 实测 100% 有值且全局唯一（local_id 会在分片间重启，不能当键）
            CREATE UNIQUE INDEX ux_msg ON messages(session_key, server_id);
            CREATE INDEX idx_msg_session ON messages(session_key, ts);
            CREATE INDEX idx_msg_dedupe ON messages(session_key, ts, sender);
            CREATE VIRTUAL TABLE messages_fts USING fts5(
              content, sender, session_key UNINDEXED, tokenize='trigram', detail='full');
            -- ★ 与现有 index.sqlite 的 sessions 表**逐列同形**，
            --   否则 index-incremental.py 的 ON CONFLICT upsert 会因缺列而失败
            CREATE TABLE sessions(
              talker TEXT PRIMARY KEY, display_name TEXT, session_type TEXT,
              is_channel INTEGER DEFAULT 0, message_count INTEGER DEFAULT 0,
              first_ts INTEGER, last_ts INTEGER, source_file TEXT);
        """)
        db.commit()
    else:
        db = None

    tot = dup = 0
    excluded_n = 0
    per_sess = {}
    t0 = time.time()
    ins = None
    if db:
        ins = "INSERT OR IGNORE INTO messages(session_key,ts,time_text,role,sender,type,content,server_id,local_id) VALUES (?,?,?,?,?,?,?,?,?)"
        insf = "INSERT INTO messages_fts(content,sender,session_key) VALUES (?,?,?)"

    for dbf in DBS:
        p = os.path.join(DEC, "message", dbf)
        if not os.path.exists(p):
            print(f"  {dbf}: 跳过")
            continue
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        idmap = {r[0]: r[1] for r in con.execute("SELECT rowid, user_name FROM Name2Id")}
        md5map = {hashlib.md5(n.encode()).hexdigest(): n for n in idmap.values() if n}
        tabs = [r[0] for r in con.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND {PAT}")]
        dbf_new = 0
        for t in tabs:
            sid = md5map.get(t[4:])
            if not sid:
                continue
            if sid in EXCLUDE:
                try:
                    excluded_n += con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                except Exception:
                    pass
                continue
            is_group = sid.endswith("@chatroom")
            try:
                rows = con.execute(
                    f'SELECT create_time, real_sender_id, local_type, local_id, server_id, message_content FROM "{t}"'
                ).fetchall()
            except Exception:
                continue
            batch, batchf = [], []
            for ts, rsid, ltype, lid, srv, blob in rows:
                tot += 1
                lt = int(ltype or 0)
                wf_type, placeholder = map_type(lt)
                if dry:
                    text, sender = "", ""
                else:
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
                        if who.startswith(MY_ROOT):
                            sender = "我"
                        elif who and not who.endswith("@chatroom"):
                            sender = who
                        else:
                            sender = sid
                    role = "me" if sender == "我" else ("system" if lt == 10000 else "them")
                    batch.append((sid, int(ts), "", role, sender, wf_type, text, int(srv or 0), int(lid or 0)))
                    batchf.append((text, sender, sid))
                s = per_sess.setdefault(sid, [0, int(ts), int(ts)])
                s[0] += 1
                if ts < s[1]:
                    s[1] = int(ts)
                if ts > s[2]:
                    s[2] = int(ts)
            if db and batch:
                db.executemany(ins, batch)
                db.executemany(insf, batchf)
                db.commit()
                dbf_new += len(batch)
            del rows
        con.close()
        if db:
            print(f"  {dbf}: 写入 {dbf_new} 条  ({time.time()-t0:.0f}s)")

    if db:
        names = load_names()
        named = 0
        for sid, (n, f, l) in per_sess.items():
            kind = "群聊" if sid.endswith("@chatroom") else ("公众号" if sid.startswith("gh_") else "私聊")
            disp = names.get(sid) or sid
            if disp != sid:
                named += 1
            db.execute(
                "INSERT OR REPLACE INTO sessions"
                "(talker,display_name,session_type,is_channel,message_count,first_ts,last_ts,source_file)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (sid, disp, kind, 1 if kind == "公众号" else 0, n, f, l, "rebuild_index_v2"),
            )
        db.commit()
        print(f"  显示名：{named}/{len(per_sess)} 个会话从通讯录补到真名")
        real = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        db.close()
    else:
        real = tot

    print("\n" + "=" * 60)
    print(f"源库读入        {tot} 行")
    if excluded_n:
        print(f"排除刷屏群      {excluded_n} 行")
    print(f"唯一键去重后    {real} 行   (server_id 精确去重，丢弃 {tot-real})")
    print(f"会话数          {len(per_sess)}")
    print(f"耗时            {time.time()-t0:.1f} 秒")
    if not dry:
        print(f"输出            {OUT}")
    else:
        print("（--dry 模式，未解码内容，未写文件）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
