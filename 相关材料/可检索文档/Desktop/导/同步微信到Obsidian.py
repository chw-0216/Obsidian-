# -*- coding: utf-8 -*-
"""
把微信会话同步成 Obsidian 人物笔记
用法: python _sync_wx_to_obsidian.py [wxid或留空=王沂]
"""
import sqlite3, hashlib, os, sys, io, glob, re
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MY_ROOT = "wxid_zn4ozsnn8esr21"
DEC = os.path.expandvars(r"%LOCALAPPDATA%\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted")
VAULT = r"C:\Users\wardc\Documents\Obsidian Vault"
ARCHIVE = os.path.join(VAULT, "03_微信聊天分析", "01_人物档案")

# ---- 配置 ----
PROFILES = {
    "wxid_0nhh6xnsh2h221": dict(
        name="王沂",
        role="木版转丝网合作方（陈晔老师引荐）",
        alias_note="Wang🌿 · 名片由陈晔老师 2026-10-20 17:10 发送",
    ),
}

import zstandard as zstd
_D = zstd.ZstdDecompressor()

def dec(b):
    if b is None: return ""
    if isinstance(b, str): return b
    try: return _D.decompress(bytes(b), max_output_size=1 << 24).decode("utf-8", "replace")
    except Exception:
        try: return bytes(b).decode("utf-8")
        except Exception: return ""

def render(lt, raw):
    """把消息渲染成可读一行"""
    t = (raw or "").strip()
    if lt == 3 or t.startswith("<img") or (t.startswith("<?xml") and "<img" in t[:400]):
        return "【图片】"
    if lt == 34: return "【语音】"
    if lt == 42: return "【名片】"
    if lt == 43: return "【视频】"
    if lt == 47: return "【表情】"
    if lt == 48: return "【位置】"
    if lt == 50: return "【语音通话】"
    if lt == 10000: return f"〔系统〕{re.sub(chr(60)+'[^>]{0,200}'+chr(62),' ',t)[:80]}"
    if lt == 49 or "<appmsg" in t:
        m = re.search(r"<title>(.*?)</title>", t, re.S)
        title = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        fname = re.search(r"<title>(.*?\.(?:pdf|docx?|xlsx?|zip|pptx?))</title>", t, re.I)
        return f"【文件】{fname.group(1)}" if fname else f"【链接】{title[:80]}"
    s = re.sub(r"<[^>]{0,400}>", " ", t)
    s = re.sub(r"\s+", " ", s).strip()
    return s or f"【type{lt}】"

def load(talker):
    tab = "Msg_" + hashlib.md5(talker.encode()).hexdigest()
    rows = []
    for dbf in sorted(glob.glob(os.path.join(DEC, "**", "*.db"), recursive=True)):
        try:
            con = sqlite3.connect(f"file:{dbf}?mode=ro", uri=True)
            if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (tab,)).fetchone():
                con.close(); continue
            idmap = {r[0]: (r[1] or "") for r in con.execute("SELECT rowid,user_name FROM Name2Id")}
            for lid, ts, rsid, lt, blob in con.execute(
                    f'SELECT local_id,create_time,real_sender_id,local_type,message_content FROM "{tab}"'):
                who = idmap.get(rsid, "") if rsid else ""
                rows.append((int(ts), int(lid), 1 if who.startswith(MY_ROOT) else 0, int(lt or 0), dec(blob)))
            con.close()
        except Exception:
            pass
    rows.sort(key=lambda r: (r[0], r[1]))
    seen, out = set(), []
    for r in rows:
        k = (r[0], r[1])
        if k in seen: continue
        seen.add(k); out.append(r)
    return out

def build(talker, prof):
    msgs = load(talker)
    if not msgs:
        print(f"  ❌ {talker} 没有消息"); return None
    t0, t1 = msgs[0][0], msgs[-1][0]
    d0 = datetime.fromtimestamp(t0).strftime("%Y-%m-%d")
    d1 = datetime.fromtimestamp(t1).strftime("%Y-%m-%d")
    me = sum(1 for m in msgs if m[2] == 1)
    them = len(msgs) - me
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    L = []
    L.append("---")
    L.append(f"tags: [人物档案, 微信, 聊天记录]")
    L.append(f"messages: {len(msgs)}")
    L.append(f"wxid: {talker}")
    L.append(f"role: {prof['role']}")
    L.append(f"first: {d0}")
    L.append(f"last: {d1}")
    L.append(f"synced: {now}")
    L.append("---")
    L.append("")
    L.append(f"# {prof['name']}")
    L.append("")
    L.append(f"> {len(msgs)} 条 · {d0} ~ {d1} · 我 {me} / 对方 {them}")
    L.append("")
    L.append(f"> [!info] 身份")
    L.append(f"> {prof['alias_note']}")
    L.append(f"> 角色：{prof['role']}")
    L.append("")
    L.append("[[00_微信聊天分析总览|← 返回总览]] ｜ [[人物案例库]]")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 完整聊天记录")
    L.append("")
    cur = None
    for ts, lid, is_send, lt, raw in msgs:
        dt = datetime.fromtimestamp(ts)
        day = dt.strftime("%Y-%m-%d")
        if day != cur:
            cur = day
            L.append("")
            L.append(f"### {day}")
            L.append("")
        hm = dt.strftime("%H:%M")
        who = "**我**" if is_send else f"**{prof['name']}**"
        L.append(f"- `{hm}` {who}　{render(lt, raw)}")
    L.append("")
    L.append("---")
    L.append("")
    L.append(f"*由 `_sync_wx_to_obsidian.py` 自动同步 · {now}*")
    L.append("")
    return "\n".join(L), msgs, d0, d1

def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(PROFILES.keys())
    os.makedirs(ARCHIVE, exist_ok=True)
    for talker in targets:
        prof = PROFILES.get(talker) or dict(name=talker, role="（未配置）", alias_note=talker)
        print(f"\n{'='*56}\n  {prof['name']}  ({talker})\n{'='*56}")
        res = build(talker, prof)
        if not res:
            continue
        md, msgs, d0, d1 = res
        out = os.path.join(ARCHIVE, f"{prof['name']}.md")
        # 先写 .tmp 再替换（避免写一半）
        tmp = out + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(md)
        os.replace(tmp, out)
        print(f"  ✅ {out}")
        print(f"     {len(msgs)} 条 · {d0} ~ {d1} · {os.path.getsize(out)//1024} KB")

if __name__ == "__main__":
    main()
