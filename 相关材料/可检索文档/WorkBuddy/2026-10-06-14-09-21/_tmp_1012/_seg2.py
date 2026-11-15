# -*- coding: utf-8 -*-
import json, os, datetime, re
from collections import Counter
OUT = r"C:/Users/wardc/WorkBuddy AI/2026-10-06-14-09-21/_tmp_1012"
rows = [json.loads(l) for l in open(os.path.join(OUT,"_chenye_all.jsonl"),encoding="utf-8")]

ANCHOR = ["井邻","洞台","渤海镇","工作站","怀柔","乡村美育","开街","低碳","王总","关总","王华青"]
h = [r for r in rows if any(k in r["body"] for k in ANCHOR)]
day = sorted({r["day"] for r in h})
segs, cur = [], [day[0]]
for d in day[1:]:
    if (datetime.date.fromisoformat(d)-datetime.date.fromisoformat(cur[-1])).days <= 3:
        cur.append(d)
    else:
        segs.append(cur); cur=[d]
segs.append(cur)
da=Counter(r["day"] for r in rows); dm=Counter(r["day"] for r in rows if r["who"]=="我"); dc=Counter(r["day"] for r in rows if r["who"]=="陈晔")
print("=== 项目锚定连续段 (%d 段, 命中 %d 条 / %d 天) ===" % (len(segs), len(h), len(day)))
for i,s in enumerate(segs,1):
    print("%-3d %s → %s  (%d天, 总%d, 我%d, 陈%d)" % (i,s[0],s[-1],len(s),sum(da[d] for d in s),sum(dm[d] for d in s),sum(dc[d] for d in s)))

print()
print("=== 2026-08-13 → 2026-08-23 全部（首单/招募）===")
for r in rows:
    if "2026-08-13" <= r["day"] <= "2026-08-23" and r["type"]==1 and len(re.findall(r"[\u4e00-\u9fff]",r["body"]))>=3:
        print("%s [%s] %s" % (r["dt"], r["who"], r["body"][:150]))

print()
print("=== 2026-09-08 → 2026-10-12 全部（收尾）===")
for r in rows:
    if "2026-09-08" <= r["day"] <= "2026-10-12" and r["type"]==1 and len(re.findall(r"[\u4e00-\u9fff]",r["body"]))>=3:
        print("%s [%s] %s" % (r["dt"], r["who"], r["body"][:150]))
