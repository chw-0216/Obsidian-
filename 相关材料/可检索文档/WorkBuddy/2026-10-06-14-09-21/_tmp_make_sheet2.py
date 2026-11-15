# -*- coding: utf-8 -*-
import os, glob
from PIL import Image, ImageDraw, ImageFont
SITE = r"C:/Users/wardc/Desktop/中期汇报_2026-09/07_照片素材/03_工作站现场_导师记录"
RECV = r"C:/Users/wardc/Desktop/中期汇报_2026-09/07_照片素材/01_工作站与领导接待"
def pick(folder, names):
    out=[]
    for n in names:
        hits = sorted(glob.glob(os.path.join(folder, n+"*")))
        if hits: out.append(hits[0])
    return out
groups = [
 ("G 07-25 空间", pick(SITE, ["20260725_工作站现场_%03d"%i for i in (100,101,102,104,106,107)])),
 ("H 07-29 接待", pick(SITE, ["20260729_工作站现场_%03d"%i for i in (91,92,93,94,95)])),
 ("I 07-31 组织部", pick(SITE, ["20260731_工作站现场_%03d"%i for i in (75,76,83,86)])),
 ("J 08-02 开街", pick(RECV, ["20260802_工作站与领导_%03d"%i for i in (17,18,20,22)])),
 ("K 08-20 梁区长", pick(SITE, ["20260820_工作站现场_%03d"%i for i in (34,35,36)])+pick(RECV, ["20260820_工作站与领导_%03d"%i for i in (11,12)])),
]
CELL_W, CELL_H, PAD, LBL = 340, 260, 8, 22
font=None
for fp in [r"C:/Windows/Fonts/msyh.ttc", r"C:/Windows/Fonts/simhei.ttf"]:
    if os.path.exists(fp): font=ImageFont.truetype(fp,14); break
maxcols = max(len(p) for _,p in groups)
Wt = PAD + maxcols*(CELL_W+PAD); Ht = PAD + sum(LBL+CELL_H+PAD+LBL for _ in groups)
sheet = Image.new("RGB",(Wt,Ht),(246,242,233)); dr=ImageDraw.Draw(sheet)
y=PAD
for title,paths in groups:
    dr.text((PAD,y+3), title, fill=(181,73,58), font=font); y+=LBL
    x=PAD
    for p in paths:
        try: im=Image.open(p).convert("RGB")
        except Exception: dr.rectangle([x,y,x+CELL_W,y+CELL_H],fill=(220,200,200)); x+=CELL_W+PAD; continue
        im.thumbnail((CELL_W,CELL_H))
        sheet.paste(im,(x+(CELL_W-im.width)//2, y+(CELL_H-im.height)//2))
        dr.rectangle([x,y,x+CELL_W,y+CELL_H],outline=(216,210,196))
        dr.text((x+2,y+CELL_H+3), os.path.basename(p)[:40], fill=(32,35,33), font=font)
        x+=CELL_W+PAD
    y+=CELL_H+PAD+LBL
out=r"_tmp_sheet_pick2.jpg"; sheet.save(out,quality=90); print("SAVED",out,sheet.size)
