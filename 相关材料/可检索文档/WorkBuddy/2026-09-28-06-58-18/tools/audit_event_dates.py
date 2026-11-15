# -*- coding: utf-8 -*-
"""
audit_event_dates.py —— 事件库日期 × 索引库真实时间范围 全面审计（只读）

目的：事件库的日期来自多个源（含 LLM 抽取），存在年份解析错误。
     用**实时索引库**作为真相源，校验每条事件的日期是否落在该对话人的真实时间范围内。

输出：_tmp/event_date_audit.txt + _tmp/event_date_audit.csv
"""
import csv, io, os, sqlite3, datetime
from collections import Counter

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
EVT = r"C:\Users\wardc\.workbuddy-ai\skills\self-understanding-engine\references\事件库.csv"
OUT = os.path.join(WS, "_tmp")

# ---------- 索引库：每个会话的 [first, last] ----------
c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
span = {}
for dn, f, l in c.execute("select display_name, min(ts), max(ts) from messages m "
                          "join sessions s on s.talker=m.session_key group by 1"):
    if dn and f and l:
        span[dn] = (f, l)
# 也按 session_key 存一份（有的 display_name 为空）
c.close()
print("索引库会话时间范围载入:", len(span))

def to_d(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

def find_span(who):
    """三级匹配：精确 → 前缀 → 包含"""
    w = (who or "").strip()
    if not w:
        return None
    if w in span:
        return span[w]
    for k, v in span.items():
        if len(k) >= 3 and (k.startswith(w[:3]) or w.startswith(k[:3])):
            return v
    for k, v in span.items():
        if len(w) >= 3 and (w[:3] in k or k[:3] in w):
            return v
    return None

# ---------- 逐条审计 ----------
rows = list(csv.DictReader(io.open(EVT, encoding="utf-8-sig")))
bad, ok, noinfo = [], 0, 0
for r in rows:
    d = (r["日期"] or "").strip()
    who = r["对话人"] or ""
    if len(d) != 10:
        noinfo += 1
        continue
    sp = find_span(who)
    if not sp:
        noinfo += 1
        continue
    lo, hi = to_d(sp[0]), to_d(sp[1])
    if lo <= d <= hi:
        ok += 1
    else:
        bad.append((d, who, lo, hi, (r["事件"] or "")[:70], r))

L = []
W = L.append
W("事件库日期审计（真相源 = 实时索引库）")
W("=" * 78)
W("事件总数: %d" % len(rows))
W("  日期落在对话人真实范围内: %d" % ok)
W("  ⚠️ 越界（日期异常）: %d" % len(bad))
W("  无法核对（对话人未匹配/无日期）: %d" % noinfo)
W("")

W("=" * 78)
W("★ 越界明细（按年份差分类）")
W("=" * 78)
for d, who, lo, hi, ev, r in sorted(bad):
    dy = int(lo[:4]) - int(d[:4])
    W("\n[%s] 对话人=%s" % (d, who[:20]))
    W("   真实范围: %s → %s   （年份差 %+d）" % (lo, hi, dy))
    W("   事件: %s" % ev)

W("\n" + "=" * 78)
W("年份差分布")
W("=" * 78)
diff = Counter(int((find_span(r["对话人"]) and to_d(find_span(r["对话人"])[0]))[:4]) - int(r["日期"][:4])
               for d, who, lo, hi, ev, r in bad)
for k, v in sorted(diff.items()):
    W("  %+d 年: %d 条" % (k, v))

io.open(os.path.join(OUT, "event_date_audit.txt"), "w", encoding="utf-8").write("\n".join(L))
with io.open(os.path.join(OUT, "event_date_audit.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["事件日期", "对话人", "真实起", "真实止", "事件摘要"])
    for d, who, lo, hi, ev, r in sorted(bad):
        w.writerow([d, who, lo, hi, ev])

print("\n".join(L))
print("\n→ _tmp/event_date_audit.txt / .csv")
