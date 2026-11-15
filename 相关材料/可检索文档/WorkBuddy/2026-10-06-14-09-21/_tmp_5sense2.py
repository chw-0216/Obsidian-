# -*- coding: utf-8 -*-
import sqlite3, datetime, re, os, glob, json

KW = ["五感","五种感官","感官","通感","嗅觉","气味","香味","栗香","味觉","触觉","听觉","具身","在地性"]

print("="*72)
print("A. 微信库 index.sqlite")
print("="*72)
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cur = con.cursor()
seen = set()
for kw in KW:
    cur.execute("""SELECT m.ts, s.display_name, m.role, m.content FROM messages m
                   LEFT JOIN sessions s ON m.session_key = s.talker
                   WHERE m.content LIKE ? ORDER BY m.ts""", ('%'+kw+'%',))
    for ts, dn, role, c in cur.fetchall():
        key = (ts, str(c)[:60])
        if key in seen: continue
        seen.add(key)
        t = datetime.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")
        c = str(c).split('<')[0][:200]
        print(f"[{kw}] [{t}] {dn} {'我' if role=='me' else '对方'}: {c}")

print()
print("="*72)
print("B. Codex sessions")
print("="*72)
cnt = 0
for f in glob.glob(r"C:/Users/wardc/.codex/sessions/2026/*/*/*.jsonl"):
    try:
        fh = open(f, encoding="utf-8", errors="ignore")
    except Exception:
        continue
    with fh:
        for line in fh:
            if not any(k in line for k in KW):
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            p = o.get("payload") or {}
            if not isinstance(p, dict) or p.get("role") not in ("user","assistant"):
                continue
            c = p.get("content")
            ts = [i.get("text") for i in c if isinstance(i, dict)] if isinstance(c, list) else ([c] if isinstance(c, str) else [])
            for t in ts:
                if not t or "<environment_context>" in t:
                    continue
                for kw in KW:
                    if kw in t:
                        print(f"[{kw}] [{o.get('timestamp','')[:16]}] {p['role']}: {t[:260]}")
                        cnt += 1
                        break
                if cnt > 60: break
            if cnt > 60: break
    if cnt > 60: break
print(f"(Codex 命中 {cnt} 条，上限 60)")
