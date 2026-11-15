# -*- coding: utf-8 -*-
from PIL import Image
sheet = Image.open(r"_tmp_sheet_pick.jpg")
PAD,LBL,CELL_W,CELL_H = 8,22,300,240
rowh = LBL+CELL_H+PAD+LBL
names = ["A","B","C","D","E","F"]
rows = {n:(PAD+i*rowh, PAD+i*rowh+LBL+CELL_H) for i,n in enumerate(names)}
counts = {"A":12,"B":9,"C":9,"D":6,"E":3,"F":6}
for n in names:
    y0,y1 = rows[n]
    c = counts[n]
    for s in range(0, c, 3):
        e = min(s+3, c)
        x0 = PAD + s*(CELL_W+PAD)
        x1 = PAD + e*(CELL_W+PAD)
        im = sheet.crop((x0,y0,x1,y1))
        out = r"_tmp_z_%s_%d.jpg"%(n,s)
        im.save(out, quality=94)
        print("SAVED", out, im.size)
