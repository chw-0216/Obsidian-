# -*- coding: utf-8 -*-
import os, glob
from PIL import Image, ImageDraw, ImageFont

SITE = r"C:/Users/wardc/Desktop/中期汇报_2026-09/07_照片素材/03_工作站现场_导师记录"
PPT  = r"C:/Users/wardc/Desktop/中期汇报_2026-09/09_PPT用图"
KEY  = r"C:/Users/wardc/Desktop/05_井邻项目_视觉与丝网印刷/12秒丝网版画_9个关键帧_20260721"

def pick(folder, names):
    out=[]
    for n in names:
        hits = sorted(glob.glob(os.path.join(folder, n+"*")))
        if hits: out.append(hits[0])
    return out

groups = [
 ("A 建设初期 07-07", pick(SITE, ["20260707_工作站现场_%03d"%i for i in (146,148,153,154,155,159,161,169,170,171,172,173)])),
 ("B 完工成型 07-24", pick(SITE, ["20260724_工作站现场_%03d"%i for i in (110,111,112,113,114,115,116,117,118)])),
 ("C 现场作业 07-25", pick(SITE, ["20260725_工作站现场_%03d"%i for i in (100,101,102,103,104,105,106,107,108)])),
 ("D 领导接待 PPT",  pick(PPT, ["01_封面_与领导共同印制","02_接待_领导观摩丝网","03_书记到访_印制台全景","04_书记到访_听取介绍","05_书记到访_村口","06_书记到访_交流"])),
 ("E 开街 PPT",      pick(PPT, ["40_开街_活动1","41_开街_活动2","42_开街_活动3"])),
 ("F 关键帧",        pick(KEY, ["01_0s_空白纸面","04_4s_三瓶滴墨","05_5s_刮板推印","06_6.2s_指纹绽放","07_7.5s_弧线变田垄","08_8.8s_乡村全景"])),
]

CELL_W, CELL_H, PAD, LBL = 300, 240, 8, 22
font = None
for fp in [r"C:/Windows/Fonts/msyh.ttc", r"C:/Windows/Fonts/simhei.ttf"]:
    if os.path.exists(fp):
        font = ImageFont.truetype(fp, 13); break

rows=[]
for title, paths in groups:
    rows.append((title, paths))

maxcols = max(len(p) for _,p in rows)
Wt = PAD + maxcols*(CELL_W+PAD)
Ht = PAD
for title, paths in rows:
    Ht += LBL + CELL_H + PAD + LBL
sheet = Image.new("RGB", (Wt, Ht), (246,242,233))
dr = ImageDraw.Draw(sheet)

y = PAD
for title, paths in rows:
    dr.text((PAD, y+2), title, fill=(181,73,58), font=font)
    y += LBL
    x = PAD
    for p in paths:
        try:
            im = Image.open(p).convert("RGB")
        except Exception as e:
            dr.rectangle([x,y,x+CELL_W,y+CELL_H], fill=(220,200,200)); x += CELL_W+PAD; continue
        im.thumbnail((CELL_W, CELL_H))
        ox = x + (CELL_W-im.width)//2
        oy = y + (CELL_H-im.height)//2
        sheet.paste(im, (ox, oy))
        dr.rectangle([x,y,x+CELL_W,y+CELL_H], outline=(216,210,196))
        dr.text((x+2, y+CELL_H+3), os.path.basename(p)[:34], fill=(32,35,33), font=font)
        x += CELL_W+PAD
    y += CELL_H + PAD + LBL

out = r"C:/Users/wardc/WorkBuddy AI/2026-10-06-14-09-21/_tmp_sheet_pick.jpg"
sheet.save(out, quality=88)
print("SAVED", out, sheet.size)
