# -*- coding: utf-8 -*-
"""
公众号历史回灌 —— 把 WeFlow 导出 JSON 里的公众号消息补进 index.sqlite。

背景：
  解密库 biz_message_*.db 只保留到 2026-08-04，2025-08-01 ~ 2026-07-24 的公众号历史
  只存在于 WeFlow 导出 JSON 里（658 个目录 / 公众号_*.json）。
  两段时间**不重叠** → 纯追加，无需内容比对去重（靠 ux_msg(session_key, server_id) 兜底）。

用法：
  python tools/import_channels.py --dry      # 只统计，不写库
  python tools/import_channels.py --apply    # 真正写入 index.sqlite
"""
from __future__ import annotations

import io
import json
import os
import re
import sqlite3
import sys
import time

SRC = r"C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出"
IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"

LOCAL_TYPE_MAP = {
    1: ("text", None), 3: ("image", "[图片]"), 34: ("voice", "[语音]"),
    43: ("video", "[视频]"), 47: ("sticker", "[表情]"), 48: ("location", "[位置]"),
    42: ("card", "[名片]"), 49: ("link", None), 50: ("voicecall", None), 10000: ("system", None),
}
URL = re.compile(r"https?://\S+")


def map_type(lt: int):
    if lt in LOCAL_TYPE_MAP:
        return LOCAL_TYPE_MAP[lt]
    if lt > 0xFFFFFFFF and (lt & 0xFFFFFFFF) in LOCAL_TYPE_MAP:
        return LOCAL_TYPE_MAP[lt & 0xFFFFFFFF]
    return (f"type{lt}", None)


def clean(s: str) -> str:
    """压空白 + 去掉裸 URL（对齐索引里公众号内容的风格）"""
    if not s:
        return ""
    s = URL.sub("", s)
    return re.sub(r"\s+", " ", s).strip()


def main():
    dry = "--dry" in sys.argv
    if not dry and "--apply" not in sys.argv:
        print("需要 --dry 或 --apply", file=sys.stderr)
        return 1

    dirs = [d for d in os.listdir(SRC) if d.startswith("公众号_")]
    print(f"公众号目录 {len(dirs)} 个")

    con = sqlite3.connect(IDX)
    con.execute("PRAGMA journal_mode=WAL")
    cur = con.cursor()

    before_n = cur.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    before_max_id = cur.execute("SELECT COALESCE(MAX(id),0) FROM messages").fetchone()[0]
    print(f"写入前: {before_n:,} 条（max id = {before_max_id}，回滚用）")

    ins_msg = ("INSERT OR IGNORE INTO messages "
               "(session_key, ts, time_text, role, sender, type, content, server_id, local_id) "
               "VALUES (?,?,?,?,?,?,?,?,?)")
    ins_fts = "INSERT INTO messages_fts (content, sender, session_key) VALUES (?,?,?)"

    tot = added = skipped = bad = 0
    sess = {}
    t0 = time.time()

    for d in dirs:
        p = os.path.join(SRC, d)
        js = [f for f in os.listdir(p) if f.endswith(".json")]
        if not js:
            continue
        try:
            with io.open(os.path.join(p, js[0]), "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            bad += 1
            continue
        sid = (data.get("session") or {}).get("wxid") or ""
        if not sid.startswith("gh_"):
            bad += 1
            continue

        batch, batchf = [], []
        for m in data.get("messages") or []:
            tot += 1
            ts = int(m.get("createTime") or 0)
            if not ts:
                continue
            lt = int(m.get("localType") or 0)
            wf_type, ph = map_type(lt)
            text = clean(m.get("content") or "") or (ph or f"[type{lt}]")
            is_send = int(m.get("isSend") or 0)
            role = "me" if is_send else ("system" if lt == 10000 else "them")
            try:
                srv = int(m.get("platformMessageId") or 0)
            except Exception:
                srv = 0
            lid = int(m.get("localId") or 0)
            batch.append((sid, ts, "", role, sid, wf_type, text, srv, lid))
            batchf.append((text, sid, sid))

        if batch:
            if dry:
                added += len(batch)
            else:
                cur.executemany(ins_msg, batch)
                added += cur.rowcount
            s = sess.setdefault(sid, [0, 0, 0])
            s[0] += len(batch)
            s[1] = min(s[1] or ts, ts)
            s[2] = max(s[2], ts)

    print(f"\n扫描消息 {tot:,} 条 · 新增 {added:,} · 目录异常 {bad}")
    print(f"涉及公众号 {len(sess)} 个 · 耗时 {time.time()-t0:.1f} 秒")

    if not dry:
        con.commit()
        # 重建 FTS：把本次新增行（id > before_max_id）补进 messages_fts
        rows = cur.execute(
            "SELECT content, sender, session_key FROM messages WHERE id > ?", (before_max_id,)
        ).fetchall()
        cur.executemany(ins_fts, rows)
        # 同步 sessions
        for sid, (n, f, l) in sess.items():
            cnt, mn, mx = cur.execute(
                "SELECT COUNT(*), MIN(ts), MAX(ts) FROM messages WHERE session_key=?", (sid,)
            ).fetchone()
            cur.execute(
                "INSERT OR REPLACE INTO sessions"
                "(talker,display_name,session_type,is_channel,message_count,first_ts,last_ts,source_file)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (sid, sid, "公众号", 1, cnt, mn, mx, "weflow_channel_backfill"),
            )
        con.commit()
        after_n = cur.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        fts_n = cur.execute("SELECT COUNT(*) FROM messages_fts").fetchone()[0]
        print(f"\n写入后: {after_n:,} 条 (+{after_n-before_n:,}) · messages_fts {fts_n:,}")
        print(f"本次新增行区间: id > {before_max_id}（如需回滚可删此区间）")
    else:
        print("（--dry 模式，未写库）")

    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
