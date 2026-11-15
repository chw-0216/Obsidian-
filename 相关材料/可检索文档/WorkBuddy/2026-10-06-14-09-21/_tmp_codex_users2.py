# -*- coding: utf-8 -*-
"""只抽"纯人话"用户指令，核对关键节点"""
import json, os, glob, re

ROOT = r"C:\Users\wardc\.codex\sessions\2026"
FILES = []
for m in ["09", "10"]:
    FILES += glob.glob(os.path.join(ROOT, m, "*", "*.jsonl"))
FILES.sort()

BAD = ("# AGENTS.md", "Automation:", ">>>", "Retained source order", "The following is",
       "<environment_context>", "tool exec", "Reviewed Codex session", "Assess the exact",
       "Planned action", "PARENT TURN", "APPROVAL REQUEST", "TRANSCRIPT", "Host: Retained",
       "{", "[", "Some conversation entries", "<external_codex", "Script completed",
       "深度思考", "Wall time", "Output:", "@'", "const ", "$")

def texts(p):
    out = []
    c = p.get("content")
    if isinstance(c, list):
        for it in c:
            if isinstance(it, dict):
                t = it.get("text") or it.get("input_text") or ""
                if t: out.append(t)
            elif isinstance(it, str): out.append(it)
    elif isinstance(c, str): out.append(c)
    return out

rows = []
for f in FILES:
    with open(f, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try: o = json.loads(line)
            except Exception: continue
            p = o.get("payload")
            if not isinstance(p, dict): continue
            if p.get("role") != "user": continue
            for t in texts(p):
                t = t.strip()
                if not t or len(t) > 600: continue
                if any(t.startswith(b) for b in BAD): continue
                if "environment_context" in t: continue
                rows.append((o.get("timestamp", ""), t))
rows.sort(key=lambda r: r[0])
print("纯指令条数:", len(rows))

print("\n" + "=" * 72)
print("【1】含『单色 / 双色 / 收敛 / 对版』的用户指令")
print("=" * 72)
for ts, t in rows:
    if any(k in t for k in ["单色", "双色", "收敛", "对版", "黑版", "只印黑"]):
        print("\n[%s] %s" % (ts[:19].replace("T", " "), t[:400]))

print("\n" + "=" * 72)
print("【2】含『飞鸟 / 绳子 / 翻 / 小鸟』的用户指令")
print("=" * 72)
for ts, t in rows:
    if any(k in t for k in ["飞鸟", "绳子", "小鸟", "翻动", "两帧"]):
        print("\n[%s] %s" % (ts[:19].replace("T", " "), t[:400]))

print("\n" + "=" * 72)
print("【3】10-03 至 10-06 全部纯指令")
print("=" * 72)
for ts, t in rows:
    if ts[:10] in ("2026-10-03", "2026-10-04", "2026-10-05", "2026-10-06"):
        print("\n[%s] %s" % (ts[:19].replace("T", " "), t[:400]))
