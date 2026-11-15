# -*- coding: utf-8 -*-
"""
全量打通：index.sqlite（1,829 会话 / 324,588 条）→ 下游可分析语料

产出：
  <OUT>/_index.csv          会话总索引（类型/显示名/wxid/消息数/首末时间/去重数）
  <OUT>/_summary.json       分层统计摘要
  <OUT>/private/*.json      私聊（weflow_live 同构）
  <OUT>/group/*.json        群聊
  <OUT>/channel/*.json      公众号 / 服务号
  <OUT>/other/*.json        企业微信 / filehelper / 未知
  <READABLE>/*.txt          可读纯文本（按天分组，只给私聊+群聊且 >= MIN_READABLE 条）

要点：
  - **去重键 (ts, content)** —— 索引混了「07 导出」与「解密库直读」两个来源，实测 2,506 条重复(0.77%)
  - 文件名安全化 + 重名加后缀；display_name 为空则用 talker
  - 只读 index.sqlite，不写它
"""
from __future__ import annotations

import csv
import datetime as dt
import io
import json
import os
import re
import sqlite3
import sys
from collections import defaultdict

INDEX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
OUT = r"C:\Users\wardc\Desktop\07_聊天记录分析\all_sessions"
READABLE = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\readable_full"
ME = "wxid_zn4ozsnn8esr21"
MIN_READABLE = 20

# index 里的 type 字符串 -> weflow_live 的 int 枚举（与 gen_live_json.py 对齐）
TYPE_INT = {
    "text": 0, "image": 1, "voice": 2, "video": 3, "sticker": 5, "location": 8,
    "card": 27, "link": 21, "voicecall": 23, "videocall": 23, "system": 80,
    "file": 21, "redpacket": 21, "transfer": 21, "quote": 0, "merged": 21,
}
BAD = re.compile(r'[\\/:*?"<>|\r\n\t]+')


def classify(k: str) -> str:
    if k.endswith("@chatroom"):
        return "group"
    if k.startswith("gh_"):
        return "channel"
    if k.endswith("@openim"):
        return "other"
    if k == "filehelper":
        return "other"
    return "private"


def safe_name(name: str, fallback: str) -> str:
    n = BAD.sub("_", (name or "").strip())
    n = n.strip(" .")
    if not n:
        n = fallback
    n = BAD.sub("_", n)
    return n[:80] if len(n) > 80 else n


def fmt(ts):
    try:
        return dt.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def main() -> int:
    dry = "--dry" in sys.argv
    only = None
    for i, a in enumerate(sys.argv):
        if a == "--only" and i + 1 < len(sys.argv):
            only = sys.argv[i + 1]

    con = sqlite3.connect(f"file:{INDEX}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    HAS_SRV = any(r[1] == "server_id" for r in con.execute("PRAGMA table_info(messages)"))
    sessions = con.execute(
        "SELECT talker, display_name, session_type, message_count, first_ts, last_ts FROM sessions"
    ).fetchall()

    for sub in ("private", "group", "channel", "other"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    os.makedirs(READABLE, exist_ok=True)

    used = defaultdict(set)
    rows_out = []
    stat = defaultdict(lambda: {"sessions": 0, "msgs": 0, "dups": 0})

    cur = con.cursor()
    n_done = 0
    for s in sessions:
        talker = s["talker"]
        cat = classify(talker)
        if only and cat != only:
            continue
        disp = (s["display_name"] or "").strip() or talker

        cur.execute(
            "SELECT ts, role, sender, type, content, id"
            + (", server_id" if HAS_SRV else "") +
            " FROM messages WHERE session_key=? ORDER BY ts, id", (talker,))
        seen = set()
        msgs = []
        dup = 0
        for row in cur:
            ts, role, sender, typ, content, mid = row[:6]
            srv = row[6] if HAS_SRV else 0
            # ★ 2026-10-04：索引重建后 `server_id` 已是精确唯一键（ux_msg），
            #   所以**按 server_id 去重**即可，不再用内容键。
            #   旧的内容键 (ts, role, sender, typ, content) 会误杀「多人同秒进群」这类
            #   真实系统消息 —— 实测误杀 225 条。仅在 server_id 缺失(=0)时回退到 id。
            key = ("srv", srv) if srv else ("id", mid)
            if key in seen:
                dup += 1
                continue
            seen.add(key)
            role = role or "them"
            if role == "me":
                snd = ME
            else:
                snd = (sender or "").strip() or talker
            msgs.append({
                "sender": snd,
                "accountName": disp,
                "timestamp": int(ts),
                "type": TYPE_INT.get((typ or "").lower(), 99),
                "typeLabel": typ or "",
                "isSend": 1 if role == "me" else 0,
                "content": content or "",
                "platformMessageId": str(mid),
            })

        st = stat[cat]
        st["sessions"] += 1
        st["msgs"] += len(msgs)
        st["dups"] += dup

        rows_out.append({
            "类型": {"private": "私聊", "group": "群聊", "channel": "公众号", "other": "其他"}[cat],
            "显示名": disp,
            "wxid": talker,
            "消息数": len(msgs),
            "去重条数": dup,
            "首条": fmt(msgs[0]["timestamp"]) if msgs else "",
            "末条": fmt(msgs[-1]["timestamp"]) if msgs else "",
        })

        if dry:
            n_done += 1
            continue

        # 落 JSON
        base = safe_name(disp, talker)
        fn = base
        # ★ 冲突检测必须**大小写不敏感** —— Windows 文件名不区分大小写，
        #   两个会话名只差大小写时会写进同一个文件，**后写的覆盖先写的（丢数据）**。
        #   实测 private 里 933 个会话只落成 932 个文件，就是这个原因。
        if fn.lower() in used[cat]:
            # 用 talker 兜底（全局唯一）
            fn = f"{base}_{talker}"
        used[cat].add(fn.lower())
        payload = {
            "displayName": disp,
            "username": talker,
            "syncAt": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "totalCount": len(msgs),
            "sessionType": cat,
            "messages": msgs,
        }
        with io.open(os.path.join(OUT, cat, fn + ".json"), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)

        # 可读文本（只给私聊/群聊且够量）
        if cat in ("private", "group") and len(msgs) >= MIN_READABLE:
            lines = []
            d0 = msgs[0]["timestamp"]; d1 = msgs[-1]["timestamp"]
            lines.append("# %s   共 %d 条   %s ~ %s\n" % (
                disp, len(msgs), fmt(d0)[:10], fmt(d1)[:10]))
            day = None
            for m in msgs:
                dd = fmt(m["timestamp"])[:10]
                if dd != day:
                    day = dd
                    lines.append("\n═══ %s ═══" % dd)
                who = "我" if m["isSend"] == 1 else "TA"
                t = fmt(m["timestamp"])[11:16]
                txt = (m["content"] or "").replace("\n", " ")
                if len(txt) > 300:
                    txt = txt[:297] + "..."
                lines.append("[%s] %s: %s" % (t, who, txt))
            with io.open(os.path.join(READABLE, fn + ".txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

        n_done += 1
        if n_done % 200 == 0:
            print("  ...已处理 %d 会话" % n_done, flush=True)

    if not dry:
        with io.open(os.path.join(OUT, "_index.csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["类型", "显示名", "wxid", "消息数", "去重条数", "首条", "末条"])
            w.writeheader()
            for r in sorted(rows_out, key=lambda x: -x["消息数"]):
                w.writerow(r)
        with io.open(os.path.join(OUT, "_summary.json"), "w", encoding="utf-8") as f:
            json.dump({
                "generatedAt": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": INDEX,
                "byCategory": {k: dict(v) for k, v in stat.items()},
                "totalSessions": sum(v["sessions"] for v in stat.values()),
                "totalMessages": sum(v["msgs"] for v in stat.values()),
                "totalDuplicatesRemoved": sum(v["dups"] for v in stat.values()),
            }, f, ensure_ascii=False, indent=1)

    # ★ --clean / --clean-dry：找出本次没有重新生成的 .json（换库/改显示名后，旧文件名会变成孤儿）
    if not dry and ("--clean" in sys.argv or "--clean-dry" in sys.argv):
        orphans = []
        total_seen = 0
        for cat in ("private", "group", "channel", "other"):
            d = os.path.join(OUT, cat)
            if not os.path.isdir(d):
                continue
            for f in os.listdir(d):
                if not f.endswith(".json"):
                    continue
                total_seen += 1
                # ⚠️ used 里存的是**小写**键（Windows 大小写不敏感），比较必须同样小写化，
                #    否则所有含大写字母的正常文件都会被误判成孤儿（2026-10-04 踩过）。
                if f[:-5].lower() not in used[cat]:
                    orphans.append(os.path.join(d, f))
        manifest = os.path.join(OUT, "_orphans.txt")
        with io.open(manifest, "w", encoding="utf-8") as f:
            f.write("\n".join(orphans))
        total_mb = sum(os.path.getsize(p) for p in orphans) / 1048576.0
        print(f"\n孤儿文件 {len(orphans)} 个 · {total_mb:.1f} MB · 清单写入 {manifest}")

        # ★ 安全阀：孤儿占比过高说明判定逻辑有问题，一律只列不删
        ratio = len(orphans) / max(total_seen, 1)
        if ratio > 0.2:
            print(f"  ⚠️ 孤儿占比 {ratio:.0%} 异常（>20%），已跳过删除，请人工核对清单")
        elif "--clean" in sys.argv:
            n = 0
            for p in orphans:
                try:
                    os.remove(p)
                    n += 1
                except Exception as e:
                    print("  删除失败:", p, e)
            print(f"  已删除 {n} 个")
        else:
            print("  （--clean-dry 只列清单，未删除）")

    print("\n===== 分层统计 =====")
    for k in ("private", "group", "channel", "other"):
        v = stat.get(k)
        if not v:
            continue
        print("  %-8s 会话 %5d  消息 %7d  去重 %5d" % (k, v["sessions"], v["msgs"], v["dups"]))
    print("  合计     会话 %5d  消息 %7d  去重 %5d" % (
        sum(v["sessions"] for v in stat.values()),
        sum(v["msgs"] for v in stat.values()),
        sum(v["dups"] for v in stat.values())))
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
