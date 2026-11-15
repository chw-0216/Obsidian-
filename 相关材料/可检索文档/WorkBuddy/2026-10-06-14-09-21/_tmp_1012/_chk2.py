# -*- coding: utf-8 -*-
import json
from collections import Counter
rows=[json.loads(l) for l in open("_chenye_jinglin.jsonl",encoding="utf-8")]
print("命中:", len(rows), "| 类型分布:", Counter(r["type"] for r in rows).most_common(8))
print()
print("--- 非文字类型的命中样本（看是否为真实内容）---")
n=0
for r in rows:
    if r["type"]!=1:
        print("%s type=%d | %s" % (r["dt"], r["type"], r["body"][:110]))
        n+=1
        if n>=18: break
print()
print("--- 我/陈晔 总条数 ---")
allr=[json.loads(l) for l in open("_chenye_all.jsonl",encoding="utf-8")]
print(Counter(r["who"] for r in allr))
