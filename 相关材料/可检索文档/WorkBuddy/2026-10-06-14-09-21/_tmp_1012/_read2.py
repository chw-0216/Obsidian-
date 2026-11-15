# -*- coding: utf-8 -*-
import json, re
from collections import Counter
rows=[json.loads(l) for l in open("_chenye_all.jsonl",encoding="utf-8")]
ANCHOR=["井邻","洞台","渤海镇","工作站","怀柔","乡村美育","开街","低碳","王总","关总","王华青"]
def lbl(lt):
    m=lt&0xFFFFFFFF; s=lt>>32
    return {1:"文字",3:"图片",34:"语音",43:"视频",47:"表情",10000:"系统",42:"名片",48:"位置",50:"通话"}.get(m) or ("引用" if s==57 else "文件" if s==6 else "链接" if s==5 else "视频号" if s==51 else "小程序" if s in(33,36) else "其他")
def ok(b):
    cjk=len(re.findall(r"[\u4e00-\u9fff]",b))
    return cjk>=4 and cjk/max(len(b),1)>0.35
hit=[r for r in rows if any(k in r["body"] for k in ANCHOR)]
clean=[r for r in hit if r["type"]!=1 or ok(r["body"])]
buf=[]; cur=None
for r in clean:
    if r["day"]!=cur:
        cur=r["day"]; buf.append("\n■ %s"%cur)
    t=lbl(r["type"]); tag="" if r["type"]==1 else "〈%s〉"%t
    buf.append("  %s [%s]%s %s"%(r["dt"][11:16],"陈晔" if r["who"]=="陈晔" else "我",tag,r["body"].replace("\n"," ⏎ ").strip()[:220]))
open("_chenye_read2.txt","w",encoding="utf-8").write("\n".join(buf))
print("锚定命中:",len(hit),"| 干净:",len(clean),"| 天:",len({r["day"] for r in clean}))
print("谁:",Counter(r["who"] for r in clean))
print("年:",Counter(r["day"][:4] for r in clean))
print("类型:",Counter(lbl(r["type"]) for r in clean))
print("行数:",len(buf))
