# -*- coding: utf-8 -*-
"""陈晔会话 · 井邻（乡村美育工作站）梳理所需的全部聚合。
输入: _chenye_all.jsonl
输出: _chenye_final.txt（人读）+ 控制台
"""
import json, os, re, datetime
from collections import Counter, defaultdict

OUT = r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21\_tmp_1012"
rows = [json.loads(l) for l in open(os.path.join(OUT, "_chenye_all.jsonl"), encoding="utf-8")]

def ok(b):
    cjk = len(re.findall(r"[\u4e00-\u9fff]", b))
    return cjk >= 4 and cjk / max(len(b), 1) > 0.35

buf = []
def p(s=""):
    buf.append(s)
    print(s)

# ---------- 1. 核心词 ----------
CORE = ["井邻", "洞台", "渤海镇", "驻村", "工作站", "植墨", "偏移四型", "四型",
        "MBTI", "八版", "飞鸟", "栗蓬", "栗子", "栗壳", "怀柔", "动漫谷", "开街",
        "乡村美育", "丝网", "版画", "工作坊", "低碳", "王总", "关总", "马慧楠", "小廖", "王子辰"]
p("=" * 72)
p("【一】核心词首次/末次出现与次数")
p("=" * 72)
p("%-10s %6s  %-19s  %-19s" % ("词", "次数", "首次", "末次"))
for k in CORE:
    h = [r for r in rows if k in r["body"]]
    if not h:
        p("%-10s %6d  -" % (k, 0)); continue
    p("%-10s %6d  %-19s  %-19s" % (k, len(h), h[0]["dt"], h[-1]["dt"]))

# ---------- 2. 连续段 ----------
p(); p("=" * 72)
p("【二】井邻相关「连续段」（相邻活跃日 ≤3 天视为同段）")
p("=" * 72)
day_hit = sorted({r["day"] for r in rows if any(k in r["body"] for k in CORE)})
segs, cur = [], [day_hit[0]] if day_hit else []
for d in day_hit[1:]:
    a = datetime.date.fromisoformat(cur[-1]); b = datetime.date.fromisoformat(d)
    if (b - a).days <= 3:
        cur.append(d)
    else:
        segs.append(cur); cur = [d]
if cur: segs.append(cur)

day_all = Counter(r["day"] for r in rows)
day_me = Counter(r["day"] for r in rows if r["who"] == "我")
day_cy = Counter(r["day"] for r in rows if r["who"] == "陈晔")
p("%-3s %-24s %5s %6s %6s %6s" % ("#", "区间", "天", "总条", "我", "陈晔"))
for i, s in enumerate(segs, 1):
    tot = sum(day_all[d] for d in s); me = sum(day_me[d] for d in s); cy = sum(day_cy[d] for d in s)
    p("%-3d %-24s %5d %6d %6d %6d" % (i, "%s → %s" % (s[0], s[-1]), len(s), tot, me, cy))

# ---------- 3. 「井邻」全部出现 ----------
p(); p("=" * 72)
p("【三】「井邻」全部出现（共 %d 次）" % len([r for r in rows if "井邻" in r["body"]]))
p("=" * 72)
for r in rows:
    if "井邻" in r["body"]:
        p("%s [%s] %s" % (r["dt"], r["who"], r["body"][:180]))

# ---------- 4. 导师口径（否定/要求） ----------
p(); p("=" * 72)
p("【四】陈晔的「口径类」发言（不要/别/不能/必须/你要/你得）")
p("=" * 72)
NEG = re.compile(r"(不要|别|不能|不许|不应该|必须|你要|你得|你还是|先.{0,4}再|记住|注意)")
for r in rows:
    if r["who"] == "陈晔" and r["type"] == 1 and NEG.search(r["body"]) and len(r["body"]) < 120:
        p("%s  %s" % (r["dt"], r["body"]))

# ---------- 5. 领导 / 来访 ----------
p(); p("=" * 72)
p("【五】领导 / 来访 / 官方口径")
p("=" * 72)
VIS = re.compile(r"(政协|区委|组织部|宣传部|文旅|科学城|区长|书记|部长|主席|领导|记者|日报|镇长|镇里|渤海镇|政府|采购|开街|到访|参观|来访|视察)")
for r in rows:
    if VIS.search(r["body"]) and len(r["body"]) < 150:
        p("%s [%s] %s" % (r["dt"], r["who"], r["body"]))

# ---------- 6. 关键人物 ----------
p(); p("=" * 72)
p("【六】关键人物提及次数与首次/末次")
p("=" * 72)
for k in ["王总", "关总", "马慧楠", "小廖", "王子辰", "刘老师", "杨老师", "小马", "王华青", "关", "小蔡"]:
    h = [r for r in rows if k in r["body"]]
    if h:
        p("%-8s %4d 次  %s → %s" % (k, len(h), h[0]["dt"], h[-1]["dt"]))

# ---------- 7. 月度分布 ----------
p(); p("=" * 72)
p("【七】陈晔会话月度消息量")
p("=" * 72)
m = Counter(r["day"][:7] for r in rows)
mm = Counter(r["day"][:7] for r in rows if r["who"] == "我")
mc = Counter(r["day"][:7] for r in rows if r["who"] == "陈晔")
p("%-9s %6s %6s %6s" % ("月份", "总", "我", "陈晔"))
for k in sorted(m):
    p("%-9s %6d %6d %6d" % (k, m[k], mm[k], mc[k]))

open(os.path.join(OUT, "_chenye_final.txt"), "w", encoding="utf-8").write("\n".join(buf))
print("\n>> 写入 _chenye_final.txt")
