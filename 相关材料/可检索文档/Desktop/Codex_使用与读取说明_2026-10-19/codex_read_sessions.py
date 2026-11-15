#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读取本机 Codex 的会话记录（只读）。

适用：Windows + OpenAI Codex 桌面端/CLI，数据目录 %USERPROFILE%\\.codex

用法：
  1) 列出最近的会话
     python codex_read_sessions.py list --limit 10

  2) 把某个会话导出为 Markdown（参数可以是完整 ID，也可以是标题关键词）
     python codex_read_sessions.py export --thread 01a1504f --out 会话.md
     python codex_read_sessions.py export --thread "博导" --diffs

  3) 解压原始 rollout 记录（*.jsonl.zst）为 .jsonl
     python codex_read_sessions.py rollout "C:\\Users\\wardc\\.codex\\sessions\\...\\rollout-xxx.jsonl.zst"

说明：
  - 只读打开 SQLite，不会写入 Codex 的数据文件；
  - 会话正文优先从 thread_history_1.sqlite 读取，标题等元数据从 state_5.sqlite 读取；
  - 解压 rollout 需要 zstandard（系统 Python 一般已安装：python -c "import zstandard"）。
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime

CODEX_HOME = os.environ.get("CODEX_HOME", os.path.join(os.path.expanduser("~"), ".codex"))
STATE_DB = os.path.join(CODEX_HOME, "state_5.sqlite")
HIST_DB = os.path.join(CODEX_HOME, "thread_history_1.sqlite")


def connect_ro(path):
    if not os.path.exists(path):
        sys.exit(f"找不到数据库：{path}")
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def fmt_ts(value, unit="s"):
    try:
        if unit == "ms":
            value = value / 1000.0
        return datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(value)


def resolve_thread(conn, key):
    """按完整 ID 或 ID 前缀 / 标题关键词定位会话，返回 (id, title, cwd, model, updated_at, tokens_used)"""
    cur = conn.cursor()
    row = cur.execute(
        "SELECT id,title,cwd,model,updated_at,tokens_used FROM threads WHERE id=?",
        (key,),
    ).fetchone()
    if row:
        return row
    row = cur.execute(
        "SELECT id,title,cwd,model,updated_at,tokens_used FROM threads WHERE id LIKE ? "
        "ORDER BY updated_at DESC LIMIT 1",
        (key + "%",),
    ).fetchone()
    if row:
        return row
    rows = cur.execute(
        "SELECT id,title,cwd,model,updated_at,tokens_used FROM threads WHERE title LIKE ? "
        "ORDER BY updated_at DESC LIMIT 5",
        (f"%{key}%",),
    ).fetchall()
    if not rows:
        sys.exit(f"没有找到匹配的会话：{key}")
    if len(rows) > 1:
        print("匹配到多个会话，请用更精确的标题或 ID：", file=sys.stderr)
        for r in rows:
            print(f"  {r[0]}  {r[1]}", file=sys.stderr)
        sys.exit(2)
    return rows[0]


def extract_text(content):
    """userMessage.content / 兼容多种 content 结构"""
    out = []
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for c in content:
            if isinstance(c, dict):
                if c.get("type") in ("text", "input_text", "output_text"):
                    out.append(c.get("text", ""))
                elif "text" in c:
                    out.append(str(c.get("text")))
            elif isinstance(c, str):
                out.append(c)
    return "\n".join(x for x in out if x)


def item_to_md(item_type, item, with_diffs=False):
    """把单条 item 转成 Markdown 片段（返回字符串或空）"""
    if item_type == "userMessage":
        text = extract_text(item.get("content", item.get("text", "")))
        return f"### 用户\n\n{text}\n" if text.strip() else ""

    if item_type == "agentMessage":
        text = item.get("text") or extract_text(item.get("content", ""))
        phase = item.get("phase") or ""
        tag = "（过程消息）" if phase == "commentary" else ""
        return f"### Codex{tag}\n\n{text}\n" if text.strip() else ""

    if item_type == "commandExecution":
        cmd = item.get("command", "")
        cwd = item.get("cwd", "")
        if not cmd:
            return ""
        s = f"### 执行命令\n\n```powershell\n{cmd}\n```\n"
        if cwd:
            s += f"\n工作目录：`{cwd}`\n"
        return s

    if item_type == "fileChange":
        lines = ["### 文件变更", ""]
        for ch in item.get("changes", []) or []:
            path = ch.get("path", "")
            kind = (ch.get("kind") or {}).get("type", "")
            lines.append(f"- `{path}`（{kind}）")
            if with_diffs and ch.get("diff"):
                diff = ch["diff"]
                if len(diff) > 4000:
                    diff = diff[:4000] + "\n…（diff 过长，已截断）"
                lines.append("\n```diff\n" + diff + "\n```")
        return "\n".join(lines) + "\n" if len(lines) > 2 else ""

    if item_type == "mcpToolCall":
        server = item.get("server", "")
        tool = item.get("tool", "")
        args = item.get("arguments", {})
        arg_text = json.dumps(args, ensure_ascii=False)
        if len(arg_text) > 800:
            arg_text = arg_text[:800] + "…"
        return f"### 工具调用（MCP）\n\n- 服务：`{server}`\n- 工具：`{tool}`\n- 参数：`{arg_text}`\n"

    if item_type == "webSearch":
        q = item.get("query") or item.get("q") or ""
        if isinstance(q, list):
            q = " / ".join(map(str, q))
        return f"### 联网搜索\n\n{q}\n" if q else "### 联网搜索\n"

    if item_type == "imageView":
        return f"### 查看图片\n\n`{item.get('path', '')}`\n"

    if item_type == "imageGeneration":
        return "### 生成图片\n\n" + json.dumps(item, ensure_ascii=False)[:500] + "\n"

    if item_type == "contextCompaction":
        return "### （上下文压缩）\n"

    if item_type == "subAgentActivity":
        return "### 子代理活动\n\n" + json.dumps(item, ensure_ascii=False)[:500] + "\n"

    if item_type == "collabAgentToolCall":
        return "### 协作代理调用\n\n" + json.dumps(item, ensure_ascii=False)[:500] + "\n"

    if item_type == "reasoning":
        summary = item.get("summary") or []
        if summary:
            return "### 推理摘要\n\n" + "\n".join(str(x) for x in summary) + "\n"
        return ""

    return ""


def cmd_list(args):
    conn = connect_ro(STATE_DB)
    cur = conn.cursor()
    rows = cur.execute(
        """SELECT id, title, cwd, model, updated_at, tokens_used, archived
           FROM threads ORDER BY updated_at DESC LIMIT ?""",
        (args.limit,),
    ).fetchall()
    print(f"最近 {len(rows)} 个会话（数据源：{STATE_DB}）\n")
    for tid, title, cwd, model, ts, tokens, archived in rows:
        title = (title or "").replace("\n", " ")[:60]
        print(f"{fmt_ts(ts)}  {'[归档]' if archived else '      '}  {tid}")
        print(f"  标题：{title}")
        print(f"  模型：{model}    tokens：{tokens}")
        print(f"  目录：{cwd}\n")


def cmd_export(args):
    conn = connect_ro(STATE_DB)
    tid, title, cwd, model, ts, tokens = resolve_thread(conn, args.thread)
    conn.close()

    hist = connect_ro(HIST_DB)
    cur = hist.cursor()
    rows = cur.execute(
        """SELECT item_type, item_json, created_at_ms
           FROM thread_items WHERE thread_id=? ORDER BY rollout_ordinal""",
        (tid,),
    ).fetchall()
    hist.close()

    out = [f"# {title or '（无标题会话）'}", ""]
    out.append(f"- 会话 ID：`{tid}`")
    out.append(f"- 工作目录：`{cwd}`")
    out.append(f"- 模型：`{model}`")
    out.append(f"- 更新时间：{fmt_ts(ts)}")
    out.append(f"- Tokens：{tokens}")
    out.append("")

    prev_type = None
    for item_type, item_json, created_ms in rows:
        try:
            item = json.loads(item_json)
        except Exception:
            continue
        md = item_to_md(item_type, item, with_diffs=args.diffs)
        if not md:
            continue
        if not (prev_type == "agentMessage" and item_type == "agentMessage"):
            out.append(f"_（{fmt_ts(created_ms, 'ms')}）_\n")
        out.append(md.rstrip() + "\n")
        prev_type = item_type

    text = "\n".join(out)
    path = args.out or f"codex_会话_{tid[:8]}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"已导出：{os.path.abspath(path)}（{len(text)} 字符，{len(rows)} 条 item）")


def cmd_rollout(args):
    try:
        import zstandard
    except ImportError:
        sys.exit("需要 zstandard 模块：python -m pip install zstandard")
    src = args.file
    if not os.path.exists(src):
        sys.exit(f"找不到文件：{src}")
    dctx = zstandard.ZstdDecompressor()
    with open(src, "rb") as f:
        raw = dctx.decompress(f.read())
    out = args.out or (src[:-4] if src.endswith(".zst") else src + ".jsonl")
    with open(out, "wb") as f:
        f.write(raw)
    lines = raw.count(b"\n") + 1
    print(f"已解压：{os.path.abspath(out)}（{len(raw)} 字节，约 {lines} 行 JSONL）")


def main():
    parser = argparse.ArgumentParser(description="只读读取本机 Codex 会话记录")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="列出最近会话")
    p_list.add_argument("--limit", type=int, default=10)
    p_list.set_defaults(func=cmd_list)

    p_exp = sub.add_parser("export", help="导出会话为 Markdown")
    p_exp.add_argument("--thread", required=True, help="会话 ID（完整或前缀）或标题关键词")
    p_exp.add_argument("--out", help="输出文件路径")
    p_exp.add_argument("--diffs", action="store_true", help="在导出中附带文件 diff")
    p_exp.set_defaults(func=cmd_export)

    p_rol = sub.add_parser("rollout", help="解压 rollout 原始记录")
    p_rol.add_argument("file", help="*.jsonl.zst 文件路径")
    p_rol.add_argument("--out", help="输出的 .jsonl 路径")
    p_rol.set_defaults(func=cmd_rollout)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
