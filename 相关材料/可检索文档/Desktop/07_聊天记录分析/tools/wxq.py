#!/usr/bin/env python
"""wxq — 微信实时查询工具（ChatTrace 版，不依赖 WeFlow）

数据源：
  - 解密库  %LOCALAPPDATA%\\ChatTrace\\accounts\\<acct>\\decrypted\\   (message_*.db / sns.db)
  - 索引库  _im_tmp\\wechat-mcp\\index.sqlite                          (sessions/messages/FTS)

子命令：
  refresh                     三层刷新：解密 -> 索引 -> JSON（约 35 秒）
  sessions [-n 30]            最近活跃会话
  new [-m 120] [--all]        最近 N 分钟的新消息（跨所有会话）
  dump <名字|wxid> [-n 40]    导出某个会话的消息
  moments [名字|wxid] [-n 20] 导出某人的朋友圈（含赞与评论）
  search <关键词> [-n 20]     全文检索（FTS5）
  resolve <名字片段>          名字 -> wxid
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

DESKTOP = Path(r"C:\Users\wardc\Desktop")
MCP = DESKTOP / "_im_tmp" / "wechat-mcp"
CHATTRACE = DESKTOP / "_im_tmp" / "chattrace"
ACCT = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45"
ACCT_KEY = "wxid_zn4ozsnn8esr21_db45"
DEC_ROOT = Path(r"C:\Users\wardc\AppData\Local\ChatTrace\accounts") / ACCT_KEY / "decrypted"
INDEX = MCP / "index.sqlite"
SNS = DEC_ROOT / "sns" / "sns.db"
STATE = MCP / "_wxq_state.json"
ME_WXID = "wxid_zn4ozsnn8esr21"


# ---------- 基础 ----------
def ts_text(value, fmt: str = "%m-%d %H:%M") -> str:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return str(value)
    if number > 10_000_000_000:
        number //= 1000
    try:
        return datetime.fromtimestamp(number).strftime(fmt)
    except (OSError, ValueError):
        return str(value)


def connect(path: Path, readonly: bool = True) -> sqlite3.Connection:
    if readonly:
        return sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    return sqlite3.connect(path)


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------- 子命令 ----------
def cmd_refresh(args) -> int:
    started = time.time()
    steps = [
        ("[1/3] 解密微信库", CHATTRACE, [sys.executable, "-m", "chattrace.cli", "data", "decrypt", "--account-dir", ACCT]),
        ("[2/3] 更新检索索引", MCP, [sys.executable, "index-incremental.py"]),
        ("[3/3] 生成分析 JSON", MCP, [sys.executable, "gen_live_json.py"]),
    ]
    for label, cwd, command in steps:
        mark = time.time()
        print(f"{label} ...", flush=True)
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        tail = [line for line in (result.stdout or "").splitlines() if line.strip()][-4:]
        for line in tail:
            print("   ", line)
        print(f"    用时 {time.time() - mark:.1f}s  exit={result.returncode}")
        if result.returncode != 0:
            print((result.stderr or "")[-500:], file=sys.stderr)
            return result.returncode
    print(f"\n刷新完成，总用时 {time.time() - started:.1f}s")
    return 0


def cmd_sessions(args) -> int:
    con = connect(INDEX)
    sql = "SELECT talker, display_name, session_type, message_count, last_ts FROM sessions"
    params: list = []
    if args.type != "all":
        sql += " WHERE session_type = ?"
        params.append(args.type)
    sql += " ORDER BY last_ts DESC LIMIT ?"
    params.append(args.limit)
    rows = con.execute(sql, params).fetchall()
    print(f"{'最后活跃':<14} {'类型':<8} {'名称':<28} {'条数':>7}  talker")
    for talker, name, kind, count, last in rows:
        print(f"{ts_text(last, '%Y-%m-%d %H:%M'):<14} {kind:<8} {(name or '')[:26]:<28} {count:>7}  {talker}")
    print(f"\n共 {con.execute('SELECT COUNT(*) FROM sessions').fetchone()[0]} 个会话 / "
          f"{con.execute('SELECT COUNT(*) FROM messages').fetchone()[0]} 条消息")
    con.close()
    return 0


def cmd_new(args) -> int:
    con = connect(INDEX)
    state = load_state()
    if args.all:
        since = 0
    else:
        since = int(time.time()) - args.minutes * 60
    rows = con.execute(
        "SELECT m.session_key, s.display_name, m.ts, m.role, m.content "
        "FROM messages m LEFT JOIN sessions s ON s.talker = m.session_key "
        "WHERE m.ts >= ? ORDER BY m.ts",
        (since,),
    ).fetchall()
    if not rows:
        print(f"最近 {args.minutes} 分钟没有新消息")
    else:
        print(f"最近 {args.minutes} 分钟新增 {len(rows)} 条，涉及 {len({r[0] for r in rows})} 个会话：\n")
        current = None
        for key, name, when, role, content in rows:
            if key != current:
                current = key
                print(f"── {name or key} ──")
            who = "我" if role == "me" else (name or "对方")[:8]
            body = str(content).replace("\n", " / ")
            print(f"  [{ts_text(when)}][{who}] {body[:120]}")
    state["last_new_check"] = int(time.time())
    save_state(state)
    con.close()
    return 0


def resolve_talker(needle: str) -> str:
    con = connect(INDEX)
    row = con.execute(
        "SELECT talker FROM sessions WHERE talker = ? OR display_name = ? "
        "OR display_name LIKE ? ORDER BY last_ts DESC LIMIT 1",
        (needle, needle, f"%{needle}%"),
    ).fetchone()
    con.close()
    return row[0] if row else needle


def cmd_dump(args) -> int:
    talker = resolve_talker(args.who)
    con = connect(INDEX)
    meta = con.execute(
        "SELECT display_name, message_count, first_ts, last_ts FROM sessions WHERE talker = ?",
        (talker,),
    ).fetchone()
    if meta:
        print(f"# {meta[0]} ({talker}) 共 {meta[1]} 条  "
              f"{ts_text(meta[2], '%Y-%m-%d')} ~ {ts_text(meta[3], '%Y-%m-%d')}\n")
    rows = con.execute(
        "SELECT ts, role, sender, content FROM messages WHERE session_key = ? "
        "ORDER BY ts DESC LIMIT ?",
        (talker, args.limit),
    ).fetchall()
    for when, role, sender, content in reversed(rows):
        who = "我" if role == "me" else "对方"
        print(f"[{ts_text(when)}][{who}] {str(content).replace(chr(10), ' / ')[:200]}")
    con.close()
    return 0


def cmd_moments(args) -> int:
    if not SNS.exists():
        print("找不到 sns.db，先跑 refresh", file=sys.stderr)
        return 1
    con = connect(SNS)
    rows = con.execute("SELECT user_name, content FROM SnsTimeLine").fetchall()
    items = []
    for user, xml in rows:
        if not xml:
            continue
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            continue
        if args.who and args.who not in xml:
            continue
        obj, extra = root.find("TimelineObject"), root.find("LocalExtraInfo")
        if obj is None:
            continue
        media = obj.find("ContentObject/mediaList")
        likes, comments = [], []
        if extra is not None:
            likes = [n.findtext("nickname") or n.findtext("username")
                     for n in extra.findall("like_user_list/user_comment")]
            comments = [(ts_text(n.findtext("create_time"), "%Y-%m-%d %H:%M"),
                         n.findtext("nickname") or n.findtext("username") or "",
                         n.findtext("content") or "")
                        for n in extra.findall("comment_user_list/user_comment")]
        items.append({
            "user": user,
            "ts": int(obj.findtext("createTime") or 0),
            "desc": obj.findtext("contentDesc") or "",
            "title": obj.findtext("title") or "",
            "desc2": obj.findtext("description") or "",
            "source": obj.findtext("sourceNickName") or "",
            "media": len(list(media)) if media is not None else 0,
            "likes": [x for x in likes if x],
            "comments": comments,
        })
    items.sort(key=lambda item: item["ts"])
    items = items[-args.limit:]
    print(f"共 {len(items)} 条朋友圈\n")
    for item in items:
        head = item["desc"] or item["title"] or "(无文字)"
        print(f"--- [{ts_text(item['ts'], '%Y-%m-%d %H:%M')}] {head}")
        if item["desc2"]:
            print(f"    分享: {item['title']}")
            print(f"          {item['desc2']}")
        if item["source"]:
            print(f"    来源: {item['source']}")
        print(f"    媒体 {item['media']} 个 | 赞: {', '.join(item['likes']) or '无'}")
        for when, who, content in item["comments"]:
            tag = " ←我" if "蔡浩文" in who else ""
            print(f"    评 [{when}] {who}{tag}: {content}")
        print()
    con.close()
    return 0


def cmd_search(args) -> int:
    con = connect(INDEX)
    rows = con.execute(
        "SELECT m.session_key, s.display_name, m.ts, m.role, m.content "
        "FROM messages_fts f JOIN messages m ON m.id = f.rowid "
        "LEFT JOIN sessions s ON s.talker = m.session_key "
        "WHERE messages_fts MATCH ? ORDER BY m.ts DESC LIMIT ?",
        (args.keyword, args.limit),
    ).fetchall()
    print(f"聊天命中 {len(rows)} 条：\n")
    for key, name, when, role, content in rows:
        who = "我" if role == "me" else (name or "对方")[:8]
        print(f"[{ts_text(when)}][{who}] {str(content).replace(chr(10), ' / ')[:160]}")
    con.close()

    if args.moments and SNS.exists():
        hits = []
        con = connect(SNS)
        for user, xml in con.execute("SELECT user_name, content FROM SnsTimeLine"):
            if xml and args.keyword in xml:
                try:
                    root = ET.fromstring(xml)
                except ET.ParseError:
                    continue
                obj, extra = root.find("TimelineObject"), root.find("LocalExtraInfo")
                if obj is None:
                    continue
                comments = []
                if extra is not None:
                    comments = [(ts_text(n.findtext("create_time"), "%Y-%m-%d %H:%M"),
                                 n.findtext("nickname") or "",
                                 n.findtext("content") or "")
                                for n in extra.findall("comment_user_list/user_comment")]
                hits.append({
                    "user": user,
                    "ts": int(obj.findtext("createTime") or 0),
                    "desc": obj.findtext("contentDesc") or obj.findtext("title") or "",
                    "comments": comments,
                })
        con.close()
        hits.sort(key=lambda item: item["ts"])
        print(f"\n朋友圈命中 {len(hits)} 条：\n")
        for hit in hits:
            print(f"--- [{ts_text(hit['ts'], '%Y-%m-%d %H:%M')}] {hit['user']}")
            print(f"    正文: {hit['desc']}")
            for when, who, content in hit["comments"]:
                tag = " ←我" if "蔡浩文" in who else ""
                print(f"    评 [{when}] {who}{tag}: {content}")
    return 0


def cmd_resolve(args) -> int:
    con = connect(INDEX)
    rows = con.execute(
        "SELECT talker, display_name, session_type, message_count FROM sessions "
        "WHERE display_name LIKE ? OR talker LIKE ? ORDER BY last_ts DESC LIMIT 10",
        (f"%{args.who}%", f"%{args.who}%"),
    ).fetchall()
    for talker, name, kind, count in rows:
        print(f"{name}  [{kind}]  {count} 条  {talker}")
    if not rows:
        print("没有匹配的会话", file=sys.stderr)
        return 1
    con.close()
    return 0


def cmd_export(args) -> int:
    talker = resolve_talker(args.who)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d")
    con = connect(INDEX)
    meta = con.execute(
        "SELECT display_name, session_type, message_count, first_ts, last_ts FROM sessions WHERE talker = ?",
        (talker,),
    ).fetchone()
    name = (meta[0] if meta else talker) or talker
    rows = con.execute(
        "SELECT ts, role, sender, type, content FROM messages WHERE session_key = ? ORDER BY ts",
        (talker,),
    ).fetchall()
    messages = [
        {
            "ts": int(ts),
            "time": ts_text(ts, "%Y-%m-%d %H:%M:%S"),
            "role": role,
            "sender": sender,
            "type": mtype,
            "content": content,
        }
        for ts, role, sender, mtype, content in rows
    ]
    con.close()

    moments: list[dict] = []
    if args.with_moments and SNS.exists():
        con = connect(SNS)
        for user, xml in con.execute("SELECT user_name, content FROM SnsTimeLine"):
            if not xml or talker not in xml:
                continue
            try:
                root = ET.fromstring(xml)
            except ET.ParseError:
                continue
            obj, extra = root.find("TimelineObject"), root.find("LocalExtraInfo")
            if obj is None:
                continue
            media = obj.find("ContentObject/mediaList")
            likes = [n.findtext("nickname") or n.findtext("username")
                     for n in (extra.findall("like_user_list/user_comment") if extra is not None else [])]
            comments = [
                {"time": ts_text(n.findtext("create_time"), "%Y-%m-%d %H:%M"),
                 "who": n.findtext("nickname") or "",
                 "content": n.findtext("content") or ""}
                for n in (extra.findall("comment_user_list/user_comment") if extra is not None else [])
            ]
            moments.append({
                "ts": int(obj.findtext("createTime") or 0),
                "time": ts_text(int(obj.findtext("createTime") or 0), "%Y-%m-%d %H:%M:%S"),
                "text": obj.findtext("contentDesc") or "",
                "shared_title": obj.findtext("title") or "",
                "media_count": len(list(media)) if media is not None else 0,
                "likes": [x for x in likes if x],
                "comments": comments,
            })
        con.close()
        moments.sort(key=lambda item: item["ts"])

    payload = {
        "exportedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": "ChatTrace decrypted DBs + wechat-mcp/index.sqlite",
        "session": {
            "talker": talker,
            "displayName": name,
            "type": meta[1] if meta else "",
            "declaredMessageCount": meta[2] if meta else len(messages),
            "first": ts_text(meta[3], "%Y-%m-%d %H:%M:%S") if meta else "",
            "last": ts_text(meta[4], "%Y-%m-%d %H:%M:%S") if meta else "",
        },
        "messages": messages,
        "moments": moments,
    }
    safe_name = "".join(ch for ch in name if ch not in r'\/:*?"<>|')
    json_path = out / f"{safe_name}_导出_{stamp}.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"JSON -> {json_path}  ({len(messages)} 条消息 / {len(moments)} 条朋友圈)")

    md_path = out / f"{safe_name}_导出_{stamp}.md"
    lines = [f"# {name}（{talker}）导出", "", f"> {payload['exportedAt']} · {len(messages)} 条消息 · {len(moments)} 条朋友圈", ""]
    lines.append("## 聊天记录")
    lines.append("")
    for item in messages:
        who = "我" if item["role"] == "me" else "对方"
        body = str(item["content"]).replace("\n", " / ")
        lines.append(f"- `{item['time']}` **{who}**：{body}")
    if moments:
        lines.append("")
        lines.append("## 朋友圈")
        lines.append("")
        for item in moments:
            head = item["text"] or item["shared_title"] or "(无文字)"
            lines.append(f"### `{item['time']}` {head}")
            lines.append(f"- 媒体 {item['media_count']} · 赞 {', '.join(item['likes']) or '无'}")
            for comment in item["comments"]:
                lines.append(f"- 评 `{comment['time']}` {comment['who']}：{comment['content']}")
            lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"MD   -> {md_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="wxq", description="微信实时查询（ChatTrace 版）")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("refresh", help="三层刷新").set_defaults(func=cmd_refresh)

    p = sub.add_parser("sessions", help="最近活跃会话")
    p.add_argument("-n", "--limit", type=int, default=30)
    p.add_argument("--type", choices=["all", "private", "group"], default="all")
    p.set_defaults(func=cmd_sessions)

    p = sub.add_parser("new", help="最近的新消息")
    p.add_argument("-m", "--minutes", type=int, default=120)
    p.add_argument("--all", action="store_true", help="全部历史（慎用）")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("dump", help="导出会话消息")
    p.add_argument("who")
    p.add_argument("-n", "--limit", type=int, default=40)
    p.set_defaults(func=cmd_dump)

    p = sub.add_parser("moments", help="导出朋友圈")
    p.add_argument("who", nargs="?", default=None, help="wxid 或名称片段")
    p.add_argument("-n", "--limit", type=int, default=20)
    p.set_defaults(func=cmd_moments)

    p = sub.add_parser("search", help="全文检索")
    p.add_argument("keyword")
    p.add_argument("-n", "--limit", type=int, default=20)
    p.add_argument("--moments", action="store_true", help="同时搜朋友圈")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("resolve", help="名字 -> wxid")
    p.add_argument("who")
    p.set_defaults(func=cmd_resolve)

    p = sub.add_parser("export", help="导出会话+朋友圈为 JSON/Markdown")
    p.add_argument("who")
    p.add_argument("--out", required=True, help="输出目录")
    p.add_argument("--with-moments", action="store_true", help="同时导出朋友圈")
    p.set_defaults(func=cmd_export)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
