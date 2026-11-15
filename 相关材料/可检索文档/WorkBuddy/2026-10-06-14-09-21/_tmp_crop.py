# -*- coding: utf-8 -*-
from PIL import Image
sheet = Image.open(r"_tmp_sheet_pick.jpg")
Wt,Ht = sheet.size
PAD,LBL,CELL_W,CELL_H = 8,22,300,240
rowh = LBL+CELL_H+PAD+LBL
rows = {}
for i,name in enumerate(["A","B","C","D","E","F"]):
    y0 = PAD + i*rowh
    rows[name] = (y0, y0+LBL+CELL_H)
def crop(name, c0, c1, scale=2):
    y0,y1 = rows[name]
    x0 = PAD + c0*(CELL_W+PAD)
    x1 = PAD + c1*(CELL_W+PAD)
    im = sheet.crop((x0,y0,x1,y1))
    im = im.resize((im.width*scale, im.height*scale), Image.LANCZOS)
    out = r"_tmp_row_%s_%d_%d.jpg"%(name,c0,c1)
    im.save(out, quality=92)
    print("SAVED", out, im.size)
crop("A",0,6); crop("A",6,12)
crop("B",0,9)
crop("C",0,9)
crop("D",0,6)
crop("E",0,3)
