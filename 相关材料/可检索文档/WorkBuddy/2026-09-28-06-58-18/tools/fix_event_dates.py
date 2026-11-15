# -*- coding: utf-8 -*-
"""
fix_event_dates.py —— 用实时索引库校正事件库日期（年份错误）

原理：
  事件库日期来自多源（含 LLM 抽取），存在**年份解析错误**（月日对、年份错）。
  真相源 = 索引库中该对话人的真实消息时间范围 [first_ts, last_ts]。

规则（只做高置信度修正）：
  若事件日期的「月-日」能落在该对话人真实跨度的某一年的同一「月-日」上
  → 判定为年份错误 → 改写为那个合法年份。
  其余一律不动（保留原值，另标「日期待核」）。

副作用：原文件备份为 events_merged.csv.bak-20261004
新增列：日期_原始 / 日期修正
"""
import csv, io, os, sqlite3, datetime, shutil
from collections import Counter

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
SRC = os.path.join(WS, "events_merged.csv")
BAK = os.path.join(WS, "events_merged.csv.bak-20261004")
DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"

# ---------- 载入真实跨度 ----------
c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
span = {}
for dn, f, l in c.execute("select display_name,min(ts),max(ts) from messages m "
                          "join sessions s on s.talker=m.session_key group by 1"):
    if dn and f and l:
        span[dn] = (f, l)
c.close()

def D(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

def find_span(who):
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

def fix_year(ds, lo, hi):
    """月日落在跨度内 → 找合法年份；否则 None"""
    mmdd = ds[5:]
    try:
        mm, dd = int(mmdd[:2]), int(mmdd[3:])
    except Exception:
        return None
    for y in range(int(lo[:4]), int(hi[:4]) + 1):
        try:
            datetime.date(y, mm, dd)
        except Exception:
            continue
        cand = "%04d-%02d-%02d" % (y, mm, dd)
        if lo <= cand <= hi:
            return cand
    return None

# ---------- 处理 ----------
rows = list(csv.DictReader(io.open(SRC, encoding="utf-8-sig")))
fields = list(rows[0].keys())
for extra in ("日期_原始", "日期修正"):
    if extra not in fields:
        fields.append(extra)

stat = Counter()
for r in rows:
    ds = (r["日期"] or "").strip()
    r["日期_原始"] = ds
    r["日期修正"] = ""
    if len(ds) != 10:
        stat["无日期"] += 1
        continue
    sp = find_span(r["对话人"])
    if not sp:
        stat["对话人未匹配"] += 1
        continue
    lo, hi = D(sp[0]), D(sp[1])
    if lo <= ds <= hi:
        stat["范围内·不动"] += 1
        continue
    f = fix_year(ds, lo, hi)
    if f:
        r["日期"] = f
        r["日期修正"] = "年份修正"
        stat["★年份已修正"] += 1
    else:
        r["日期修正"] = "日期待核"
        stat["越界·待核"] += 1

if not os.path.exists(BAK):
    shutil.copy2(SRC, BAK)

with io.open(SRC, "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

print("事件库日期校正完成")
print("=" * 50)
for k, v in stat.most_common():
    print("  %-16s %5d" % (k, v))
print("\n备份: %s" % BAK)
print("已写: %s（新增列 日期_原始 / 日期修正）" % SRC)
