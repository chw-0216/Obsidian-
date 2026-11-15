# -*- coding: utf-8 -*-
import json, os
from collections import Counter
rows=[json.loads(l) for l in open("_chenye_all.jsonl",encoding="utf-8")]
print("我:", sum(1 for r in rows if r["who"]=="我"), " 陈晔:", sum(1 for r in rows if r["who"]=="陈晔"))
for t in (42,48,50):
    s=[r for r in rows if r["type"]==t][:3]
    print("--- type", t, "n=", sum(1 for r in rows if r["type"]==t))
    for r in s: print("   ", r["dt"], r["body"][:100])
for lt in sorted({r["type"] for r in rows if r["type"]>0xFFFFFFFF}):
    sub=lt>>32
    if sub in (1,19,63):
        s=[r for r in rows if r["type"]==lt][:2]
        print("--- sub",sub,"n=",sum(1 for r in rows if r["type"]==lt))
        for r in s: print("   ", r["dt"], r["body"][:120])
