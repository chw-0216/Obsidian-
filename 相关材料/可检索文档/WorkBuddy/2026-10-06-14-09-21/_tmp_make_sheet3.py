# -*- coding: utf-8 -*-
import os, glob
from PIL import Image, ImageDraw, ImageFont
RECV = r"C:/Users/wardc/Desktop/中期汇报_2026-09/07_照片素材/01_工作站与领导接待"
SITE = r"C:/Users/wardc/Desktop/中期汇报_2026-09/07_照片素材/03_工作站现场_导师记录"
S22  = r"C:/Users/wardc/Desktop/中期汇报_2026-09/07_照片素材/06_区委书记到访_导师聊天_2026-08-22"
files = [
 os.path.join(RECV,"20260820_工作站与领导_001.jpg"),
 os.path.join(RECV,"20260820_工作站与领导_012.jpg"),
 os.path.join(SITE,"20260820_工作站现场_036.jpg"),
 os.path.join(SITE,"20260820_工作站现场_034.jpg"),
 os.path.join(S22,"20260822_区委书记到访_印制台全景.png"),
 os.path.join(S22,"20260822_区委书记到访_站内听取介绍.png"),
 os.path.join(S22,"20260822_区委书记到访_与老师交流.png"),
 os.path.join(S22,"20260822_区委书记到访_村口步行街.png"),
]
CELL_W,CELL_H,PAD,LBL=420,320,8,22
font=ImageFont.truetype(r"C:/Windows/Fonts/msyh.ttc",14)
cols=4
rows=(len(files)+cols-1)//cols
Wt=PAD+cols*(CELL_W+PAD); Ht=PAD+rows*(CELL_H+LBL+PAD)
sheet=Image.new("RGB",(Wt,Ht),(246,242,233)); dr=ImageDraw.Draw(sheet)
for i,p in enumerate(files):
    r,c=divmod(i,cols); x=PAD+c*(CELL_W+PAD); y=PAD+r*(CELL_H+LBL+PAD)
    try:
        im=Image.open(p).convert("RGB"); im.thumbnail((CELL_W,CELL_H))
        sheet.paste(im,(x+(CELL_W-im.width)//2, y+(CELL_H-im.height)//2))
    except Exception as e:
        dr.rectangle([x,y,x+CELL_W,y+CELL_H],fill=(220,200,200))
    dr.rectangle([x,y,x+CELL_W,y+CELL_H],outline=(216,210,196))
    dr.text((x+2,y+CELL_H+3), os.path.basename(p)[:46], fill=(32,35,33), font=font)
out=r"_tmp_sheet_pick3.jpg"; sheet.save(out,quality=92); print("SAVED",out,sheet.size)
