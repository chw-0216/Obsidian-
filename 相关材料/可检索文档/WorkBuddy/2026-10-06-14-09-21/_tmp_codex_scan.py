# -*- coding: utf-8 -*-
"""从 Codex rollout jsonl 中抽取 user 消息原文（含时间戳）"""
import json, os, glob

ROOT = r"C:\Users\wardc\.codex\sessions\2026"
FILES = []
for m in ["09", "10"]:
    FILES += glob.glob(os.path.join(ROOT, m, "*", "*.jsonl"))
FILES.sort()

def texts(payload):
    out = []
    c = payload.get("content")
    if isinstance(c, list):
        for it in c:
            if isinstance(it, dict):
                t = it.get("text") or it.get("input_text") or ""
                if t: out.append(t)
            elif isinstance(it, str):
                out.append(it)
    elif isinstance(c, str):
        out.append(c)
    for k in ("text", "message"):
        if isinstance(payload.get(k), str):
            out.append(payload[k])
    return out

rows = []
for f in FILES:
    with open(f, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            p = o.get("payload")
            if not isinstance(p, dict):
                continue
            role = p.get("role")
            if role not in ("user", "assistant"):
                continue
            for t in texts(p):
                if not t.strip():
                    continue
                if t.lstrip().startswith("<environment_context>"):
                    continue
                if "<environment_context>" in t and len(t) > 2000:
                    continue
                rows.append((o.get("timestamp", ""), role, t, os.path.basename(f)))

rows.sort(key=lambda r: r[0])
print("user/assistant 消息总数:", len(rows))
OUT = r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21\_tmp_jinglin\codex_对话全量.txt"
with open(OUT, "w", encoding="utf-8") as w:
    for ts, role, t, fn in rows:
        w.write("=== %s | %s | %s\n%s\n\n" % (ts, role, fn, t[:3000]))
print("已落盘 codex_对话全量.txt")

KWS = ["悲鸿", "主导", "不是海报", "艺术品", "当地特色", "香料", "对版", "单色", "双色", "飞鸟", "翻动", "硫酸纸", "制版", "网版", "曝光"]
print("=" * 70)
for kw in KWS:
    hits = [r for r in rows if kw in r[2]]
    print("\n### [%s] 命中 %d" % (kw, len(hits)))
    for ts, role, t, fn in hits[:6]:
        d = ts[:16].replace("T", " ")
        one = " / ".join(x.strip() for x in t.splitlines() if x.strip())[:230]
        print("   %s | %s | %s" % (d, role, one))
