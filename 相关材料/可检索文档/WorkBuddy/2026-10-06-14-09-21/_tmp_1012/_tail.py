# -*- coding: utf-8 -*-
import json, os, re
OUT = r"C:/Users/wardc/WorkBuddy AI/2026-10-06-14-09-21/_tmp_1012"
rows=[json.loads(l) for l in open(os.path.join(OUT,"_chenye_all.jsonl"),encoding="utf-8")]
print("=== 2026-10-03 → 2026-10-12 ===")
for r in rows:
    if r["day"]>="2026-10-03" and r["type"]==1 and len(re.findall(r"[\u4e00-\u9fff]",r["body"]))>=3:
        print("%s [%s] %s" % (r["dt"],r["who"],r["body"][:160]))
print()
print("=== 2025-10-15 → 2025-10-23 关键（含井邻/怀柔/王总/勤工/低碳）===")
KEY=re.compile(r"(井邻|怀柔|王总|勤工|低碳|栗|百千|丝网|承诺|消费|洞台|驻村|第一批|名单|打卡)")
for r in rows:
    if "2025-10-15"<=r["day"]<="2025-10-24" and r["type"]==1 and KEY.search(r["body"]) and len(re.findall(r"[\u4e00-\u9fff]",r["body"]))>=3:
        print("%s [%s] %s" % (r["dt"],r["who"],r["body"][:160]))
