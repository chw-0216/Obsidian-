# -*- coding: utf-8 -*-
"""海燕（中传·李老师）会话秒查 —— 0.2 秒看最新消息。

用法：
    python 查最新消息.py              # 默认会话（海燕 guo647789）最新 20 条
    python 查最新消息.py 50           # 看 50 条
    python 查最新消息.py -r 30        # 先增量刷新（解密+索引，约 30 秒）再看 30 条
    python 查最新消息.py 李老师        # 按显示名子串查（任意会话，不限海燕）
    python 查最新消息.py wxid_xxx 30  # 指定 wxid
    python 查最新消息.py --full       # 不截断正文（默认截 120 字）
    python 查最新消息.py --json       # 同时导出 Desktop\\海燕\\海燕_聊天记录.json

设计要点（踩过的坑）：
  · role 取值只有 me / them / system —— 库里没有 'her'、'self'
  · ts 是 Unix 秒，不是毫秒
  · 索引库一律 ?mode=ro 只读
  · 刷新用系统 Python 3.12（chattrace 是 editable 装在 3.12；托管 3.13 没有）
  · 本机 http_proxy 会劫持本地请求 → 清掉
"""
import sqlite3, sys, datetime, subprocess, os, json, shutil

sys.stdout.reconfigure(encoding="utf-8")

DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
ME = "wxid_zn4ozsnn8esr21"
DEFAULT_TALKER = "guo647789"          # 海燕（中传·李老师）
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(HERE, "海燕_聊天记录.json")

CHATTRACE_DIR = r"C:\Users\wardc\Desktop\_im_tmp\chattrace"
MCP_DIR = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp"
ACCOUNT = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45"
FALLBACK_PY = r"C:\Users\wardc\AppData\Local\Programs\Python\Python312\python.exe"


def pick_python():
    """挑一个能 import chattrace 的解释器（优先系统 3.12）。"""
    try:
        import importlib.util
        if importlib.util.find_spec("chattrace"):
            return sys.executable
    except Exception:
        pass
    return FALLBACK_PY if os.path.exists(FALLBACK_PY) else sys.executable


def do_refresh():
    """三层全走：解密 → 索引 → 出落点 JSON。

    ⚠️ 2026-10-09 补坑：原先只做前两层，导致 `weflow_live\\海燕.json` 停在旧版本，
    下游 `render_haiyan.py`（读 JSON）算出的条数会比索引库少。
    实测：索引 49 条 vs JSON 48 条 —— 差的正是 38 秒内新到的那条。
    """
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    for k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"):
        env.pop(k, None)
    py = pick_python()
    print("  [1/3] 解密（ChatTrace）…")
    subprocess.run([py, "-m", "chattrace.cli", "data", "decrypt", "--account-dir", ACCOUNT],
                   cwd=CHATTRACE_DIR, env=env, capture_output=True, timeout=300)
    print("  [2/3] 增量索引…")
    subprocess.run([py, "index-incremental.py"],
                   cwd=MCP_DIR, env=env, capture_output=True, timeout=300)
    print("  [3/3] 重出落点 JSON…")
    subprocess.run([py, "gen_live_json.py"],
                   cwd=MCP_DIR, env=env, capture_output=True, timeout=300)
    print("  刷新完成（三层）\n")


def resolve_talker(arg):
    """把 '李老师' 这类显示名子串解析成 wxid。"""
    if arg.startswith("wxid_") or "@" in arg or arg.isdigit():
        return arg
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = list(c.execute(
        "SELECT talker, display_name, message_count FROM sessions "
        "WHERE display_name LIKE ? ORDER BY message_count DESC", (f"%{arg}%",)))
    c.close()
    if not rows:
        return arg                      # 原样返回，后面按 LIKE 兜底
    if len(rows) > 1:
        print(f"⚠️ 「{arg}」匹配到 {len(rows)} 个会话，用消息量最大的那个：")
        for t, n, m in rows[:5]:
            print(f"    {t}  {n}  ({m} 条)")
    return rows[0][0]


def load(talker, limit, full=False):
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = list(c.execute(
        "SELECT id, role, ts, type, content FROM messages "
        "WHERE session_key LIKE ? ORDER BY ts DESC, id DESC LIMIT ?",
        (f"%{talker}%", limit * 4)))
    c.close()
    seen, out = set(), []
    for mid, role, ts, typ, content in rows:
        key = (ts, content)
        if key in seen:
            continue
        seen.add(key)
        out.append((mid, role, ts, typ, content))
        if len(out) >= limit:
            break
    return list(reversed(out))


def label(role):
    return {"me": "我", "system": "系统"}.get(role, "对方")


def show(talker, rows, full=False):
    print(f"=== {talker} 最新 {len(rows)} 条 ===")
    for mid, role, ts, typ, content in rows:
        try:
            dt = datetime.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")
        except Exception:
            dt = str(ts)
        text = (content or "").replace("\n", " ").strip()
        if not full and len(text) > 120:
            text = text[:117] + "…"
        print(f"[{dt}] {label(role)}: {text}")


def export(talker, rows):
    data = {
        "talker": talker,
        "exportedAt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(rows),
        "messages": [
            {"id": mid, "role": role, "sender": label(role),
             "timestamp": int(ts),
             "time": datetime.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S"),
             "type": typ, "content": content}
            for mid, role, ts, typ, content in rows],
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"\n📄 已导出 → {OUT_JSON}（{len(rows)} 条）")


if __name__ == "__main__":
    argv = sys.argv[1:]
    refresh = "-r" in argv or "--refresh" in argv
    full = "--full" in argv
    want_json = "--json" in argv
    argv = [a for a in argv if not a.startswith("-")]

    talker, limit = DEFAULT_TALKER, 20
    for a in argv:
        if a.isdigit():
            limit = int(a)
        else:
            talker = a
    talker = resolve_talker(talker)

    if refresh:
        do_refresh()

    rows = load(talker, limit, full)
    if not rows:
        print(f"❌ 没查到 {talker} 的消息（索引库可能没这个会话）")
        sys.exit(1)
    show(talker, rows, full)
    if want_json:
        export(talker, rows)
