# -*- coding: utf-8 -*-
"""
导（陈晔）· 秒级查看最新消息
直接读【解密后的原始微信库】，不走索引库 —— 更准（索引对导只有 5097 条，原始库有 7102 条）

用法:
  python 查最新消息.py              # 最新 20 条，秒级
  python 查最新消息.py 30           # 最新 30 条
  python 查最新消息.py -r           # 先增量刷新（约30秒）再查看
  python 查最新消息.py -r 15        # 刷新后看 15 条
  python 查最新消息.py -a           # 查看全部（分页打印最后 200 条）
  python 查最新消息.py -j           # 导出完整 JSON 到桌面
  python 查最新消息.py deerluna 10  # 指定会话（任意 wxid 均可，脚本通用）
"""
import sqlite3
import hashlib
import os
import sys
import glob
import json
import shutil
import subprocess
import datetime
from collections import defaultdict

# ============ 配置 ============
MY_ROOT   = "wxid_zn4ozsnn8esr21"          # 自己的 wxid（解密库里不带 _db45 后缀）
DEFAULT_TALKER = "deerluna"                 # 导（陈晔）
DEC_ROOT  = os.path.expandvars(
    r"%LOCALAPPDATA%\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted")
JSON_OUT  = r"C:\Users\wardc\Desktop\导_聊天记录.json"

TYPE_LABEL = {
    1: "text", 3: "image", 34: "voice", 42: "card", 43: "video",
    47: "sticker", 48: "location", 49: "link", 50: "voicecall",
    51: "videocall", 10000: "system",
}


def _dctx():
    try:
        import zstandard as zstd
        return zstd.ZstdDecompressor()
    except ImportError:
        return None


_D = _dctx()


def decode_content(blob):
    if blob is None:
        return ""
    if isinstance(blob, str):
        return blob
    raw = bytes(blob)
    if not raw:
        return ""
    if _D is not None:
        try:
            return _D.decompress(raw, max_output_size=1 << 24).decode("utf-8", "replace")
        except Exception:
            pass
    try:
        return raw.decode("utf-8")
    except Exception:
        return ""


import re


def clean_text(s):
    """把 XML/图片等压成可读一行"""
    if not s:
        return ""
    t = s.lstrip()
    if t.startswith("<msg") or t.startswith("<?xml"):
        def grab(tag):
            m = re.search(rf"<{tag}>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{tag}>", s, re.S)
            return m.group(1).strip() if m else ""
        parts = [grab(x) for x in ("title", "des", "content")]
        parts = [p for p in parts if p]
        if parts:
            s = " | ".join(parts)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]{0,200}>", " ", s)).strip()


def do_refresh():
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    print("刷新中（解密 + 索引）…")
    subprocess.run(["python", "-m", "chattrace.cli", "data", "decrypt",
                    "--account-dir", r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45"],
                   cwd=r"C:\Users\wardc\Desktop\_im_tmp\chattrace", env=env,
                   capture_output=True, timeout=300)
    subprocess.run(["python", "index-incremental.py"],
                   cwd=r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp", env=env,
                   capture_output=True, timeout=180)
    print("刷新完成")


def read_session(talker):
    """从所有解密库读取该会话，返回按时间升序的列表（已修正发送方）"""
    tab = "Msg_" + hashlib.md5(talker.encode()).hexdigest()
    rows = []
    for dbf in sorted(glob.glob(os.path.join(DEC_ROOT, "**", "*.db"), recursive=True)):
        try:
            con = sqlite3.connect(f"file:{dbf}?mode=ro", uri=True)
            if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                               (tab,)).fetchone():
                con.close()
                continue
            idmap = {r[0]: (r[1] or "") for r in con.execute("SELECT rowid, user_name FROM Name2Id")}
            for ts, rsid, lt, blob in con.execute(
                    f'SELECT create_time, real_sender_id, local_type, message_content FROM "{tab}"'):
                who = idmap.get(rsid, "") if rsid else ""
                is_send = 1 if who.startswith(MY_ROOT) else 0
                rows.append((int(ts), is_send, int(lt or 0), clean_text(decode_content(blob))))
            con.close()
        except Exception:
            pass
    rows.sort(key=lambda r: (r[0], r[1]))
    # 去重：同秒 + 同方向 + 同内容 + 同类型
    out, seen = [], set()
    for r in rows:
        k = (r[0], r[1], r[2], r[3][:80])
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def show(talker, limit):
    rows = read_session(talker)
    if not rows:
        print(f"未找到会话: {talker}")
        return
    tail = rows[-limit:]
    first, last = rows[0], rows[-1]
    print(f"=== {talker} | 共 {len(rows)} 条 | "
          f"{datetime.datetime.fromtimestamp(first[0]):%Y-%m-%d} → "
          f"{datetime.datetime.fromtimestamp(last[0]):%Y-%m-%d %H:%M} ===")
    print(f"    我 {sum(1 for r in rows if r[1]==1)} 条 / 对方 {sum(1 for r in rows if r[1]==0)} 条")
    print("-" * 70)
    for ts, is_send, lt, text in tail:
        who = "我" if is_send else "她"
        dt = datetime.datetime.fromtimestamp(ts).strftime("%m-%d %H:%M:%S")
        t = (text or "").replace("\n", " ")
        if len(t) > 110:
            t = t[:107] + "..."
        if not t:
            t = f"[{TYPE_LABEL.get(lt, 'type' + str(lt))}]"
        print(f"[{dt}] {who}: {t}")


def export_json(talker):
    rows = read_session(talker)
    data = [{"createTime": ts, "isSend": is_send, "localType": lt, "content": text}
            for ts, is_send, lt, text in rows]
    tmp = JSON_OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    with open(tmp, encoding="utf-8") as f:
        assert len(json.load(f)) == len(data)
    bak_dir = r"C:\Users\wardc\Desktop\10_个人资料与旧文件\工作日志"
    os.makedirs(bak_dir, exist_ok=True)
    if os.path.exists(JSON_OUT):
        shutil.copy2(JSON_OUT, os.path.join(bak_dir, "导_聊天记录_上一版备份.json"))
    shutil.copy2(tmp, JSON_OUT)
    os.remove(tmp)
    print(f"✅ 已导出 {len(data)} 条 → {JSON_OUT}")
    if data:
        print(f"   最新: {datetime.datetime.fromtimestamp(data[-1]['createTime']):%Y-%m-%d %H:%M}")


if __name__ == "__main__":
    args = list(sys.argv[1:])
    refresh = ("-r" in args) or ("--refresh" in args)
    dump_all = ("-a" in args) or ("--all" in args)
    to_json = ("-j" in args) or ("--json" in args)
    args = [a for a in args if not a.startswith("-")]

    talker, limit = DEFAULT_TALKER, 20
    for a in args:
        if a.isdigit():
            limit = int(a)
        else:
            talker = a
    if dump_all:
        limit = 200

    if refresh:
        do_refresh()
    if to_json:
        export_json(talker)
    else:
        show(talker, limit)
