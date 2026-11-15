# -*- coding: utf-8 -*-
"""定向抽取：飞鸟/绳子/单色双色/收敛 等关键节点"""
import json, os, glob

ROOT = r"C:\Users\wardc\.codex\sessions\2026"
FILES = []
for m in ["09", "10"]:
    FILES += glob.glob(os.path.join(ROOT, m, "*", "*.jsonl"))
FILES.sort()

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
    for k in ("text", "message"):
        if isinstance(p.get(k), str): out.append(p[k])
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
                if not t or "<environment_context>" in t: continue
                # 只留"人话"（短、无工具痕迹）
                if t.startswith("[") or t.startswith("{") or "tool exec" in t: continue
                rows.append((o.get("timestamp", ""), t))
rows.sort(key=lambda r: r[0])

print("纯用户指令条数:", len(rows))
print("\n" + "=" * 72)
print("【A】10-01 至 10-05 用户原话全录（井邻视觉相关）")
print("=" * 72)
for ts, t in rows:
    if ts[:10] in ("2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05"):
        if len(t) > 900: t = t[:900] + " …"
        print("\n--- %s ---\n%s" % (ts[:19].replace("T", " "), t))
