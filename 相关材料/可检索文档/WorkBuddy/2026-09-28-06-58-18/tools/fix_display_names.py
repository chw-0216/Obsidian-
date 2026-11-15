# -*- coding: utf-8 -*-
"""
修复 sessions.display_name —— 重建索引时被我误写成 wxid/gh_id，导致下游导出的
文件名和 accountName 全是机器 id。

名称来源（优先级）：
  1) contact.remark        （他设的备注 —— 识别标签）
  2) contact.nick_name     （微信昵称）
  3) chat_room 表（群名）
  4) 兜底：talker 本身

用法：
  python tools/fix_display_names.py --dry     # 只看覆盖率
  python tools/fix_display_names.py --apply   # 写入 index.sqlite
"""
from __future__ import annotations

import os
import sqlite3
import sys

IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
DEC = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted"


def load_names():
    """返回 {username: 显示名}"""
    m = {}
    p = os.path.join(DEC, "contact", "contact.db")
    c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    for u, remark, nick in c.execute("SELECT username, remark, nick_name FROM contact"):
        if not u:
            continue
        name = (remark or "").strip() or (nick or "").strip()
        if name:
            m[u] = name
    c.close()

    # 群名（部分群名只在 chat_room / chat_room_info_detail 里）
    for db, tbl, cols in (
        ("contact.db", "chat_room", ("username", "nick_name", "remark")),
        ("contact.db", "chat_room_info_detail", None),
    ):
        p = os.path.join(DEC, "contact", db)
        if not os.path.exists(p):
            continue
        c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        try:
            have = [r[1] for r in c.execute(f"PRAGMA table_info({tbl})")]
        except Exception:
            c.close()
            continue
        if not have:
            c.close()
            continue
        uc = next((x for x in ("username", "chatroom", "chat_room") if x in have), None)
        nc = next((x for x in ("nick_name", "nickname", "name", "display_name") if x in have), None)
        rc = "remark" if "remark" in have else None
        if uc and nc:
            for row in c.execute(f"SELECT {uc}, {nc}" + (f", {rc}" if rc else "") + f" FROM {tbl}"):
                u = row[0]
                nm = ((row[2] if rc else "") or "").strip() or (row[1] or "").strip()
                if u and nm and u not in m:
                    m[u] = nm
        c.close()
    return m


def main():
    dry = "--dry" in sys.argv
    if not dry and "--apply" not in sys.argv:
        print("需要 --dry 或 --apply", file=sys.stderr)
        return 1

    names = load_names()
    print(f"通讯录/群名表载入 {len(names):,} 条")

    con = sqlite3.connect(IDX)
    cur = con.cursor()
    rows = cur.execute("SELECT talker, display_name, session_type FROM sessions").fetchall()

    hit = miss = already = 0
    miss_by_kind = {}
    upd = []
    for talker, disp, kind in rows:
        if disp and disp != talker:
            already += 1
            continue
        nm = names.get(talker)
        if nm and nm != talker:
            upd.append((nm, talker))
            hit += 1
        else:
            miss += 1
            miss_by_kind[kind] = miss_by_kind.get(kind, 0) + 1

    print(f"\n会话总数 {len(rows):,}")
    print(f"  已有真名       {already:,}")
    print(f"  本次可补真名   {hit:,}")
    print(f"  仍无名（兜底用 id）{miss:,}")
    if miss_by_kind:
        print("  仍无名按类型:", dict(sorted(miss_by_kind.items(), key=lambda x: -x[1])))

    if dry:
        print("\n（--dry 模式，未写库）")
        for nm, tk in upd[:8]:
            print(f"    {tk} → {nm}")
        con.close()
        return 0

    cur.executemany("UPDATE sessions SET display_name=? WHERE talker=?", upd)
    con.commit()
    left = cur.execute(
        "SELECT COUNT(*) FROM sessions WHERE display_name IS NULL OR display_name=talker OR display_name=''"
    ).fetchone()[0]
    print(f"\n写入 {cur.rowcount if cur.rowcount>0 else hit:,} 条；仍无名的会话 {left:,}")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
