# -*- coding: utf-8 -*-
"""对照实验：对「非补2」的既有文件做同样的尺寸校验。
若它们也大面积不通过 → 说明 cdnthumbwidth/height 不是本地缩略图的尺寸，校验方法无效。
"""
import json, os, re, struct, datetime
OUT = r"C:/Users/wardc/Desktop/中期汇报_2026-09/17_陈晔会话图片全量定位_2026-10-12/02_图片"
JSON_P = r"C:/Users/wardc/Desktop/导_聊天记录.json"

def jpeg_size(b):
    i=2; n=len(b)
    while i < n-9:
        if b[i]!=0xFF: i+=1; continue
        m=b[i+1]
        if m in (0xD8,0xD9) or 0xD0<=m<=0xD7: i+=2; continue
        seg=struct.unpack_from(">H",b,i+2)[0]
        if m in (0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF):
            h,w=struct.unpack_from(">HH",b,i+5); return w,h
        i+=2+seg
    return None
def png_size(b):
    return struct.unpack_from(">II",b,16) if len(b)>=24 else None
def dims_of(p):
    b=open(p,"rb").read()
    if b[:3]==b"\xff\xd8\xff": return jpeg_size(b)
    if b[:8]==b"\x89PNG\r\n\x1a\n": return png_size(b)
    return None

msgs=json.load(open(JSON_P,encoding="utf-8"))
idx={}
for m in msgs:
    if str(m.get("localType"))!="3": continue
    ct=m.get("content") or ""
    gi=lambda k:(re.search(rf'\b{k}="(\d+)"',ct) or [None,None])[1]
    idx[int(m["createTime"])]={"tw":gi("cdnthumbwidth"),"th":gi("cdnthumbheight"),
        "thumb":gi("cdnthumblength"),"hd":gi("hdlength"),"mid":gi("length")}

ok=bad=0; samples=[]
for ym in sorted(os.listdir(OUT)):
    d=os.path.join(OUT,ym)
    if not os.path.isdir(d): continue
    for f in sorted(os.listdir(d)):
        if "_补2." in f: continue
        mm=re.match(r"(\d{8})_(\d{6})_([^_]+)_",f)
        if not mm: continue
        ts=int(datetime.datetime.strptime(mm.group(1)+mm.group(2),"%Y%m%d%H%M%S").timestamp())
        info=idx.get(ts)
        if not info or not info["tw"]: continue
        p=os.path.join(d,f); sz=os.path.getsize(p); d0=dims_of(p)
        want=(int(info["tw"]),int(info["th"]))
        if d0==want: ok+=1
        else:
            bad+=1
            if len(samples)<15: samples.append((f,d0,want,sz,info["thumb"],info["mid"],info["hd"]))
print("非补2 文件尺寸校验：  ✓ %d   ✗ %d" % (ok,bad))
print()
for s in samples:
    print("%-44s 实际=%s 期望=%s 文件=%dB thumb=%s mid=%s hd=%s" % s)
