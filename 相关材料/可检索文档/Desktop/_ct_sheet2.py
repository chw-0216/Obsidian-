# -*- coding: utf-8 -*-
import os, sys, io
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
BASE = r"C:\Users\wardc\Desktop\中期汇报_2026-09\10_照片汇总_2026-10-06"
OUT = r"C:\Users\wardc\Desktop\_素材预览"

groups = [("03_版画三技", 6), ("02_工作站_接待与讲解", 6)]
CW, CH = 460, 460
sheet = Image.new("RGB", (CW*6, CH*2+60), (22,22,22))
def font(sz):
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\arial.ttf"):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except Exception: pass
    return ImageFont.load_default()
d = ImageDraw.Draw(sheet)
d.text((12, 10), "03_版画三技", fill=(255,220,120), font=font(28))
d.text((12, CH+38), "02_工作站_接待与讲解", fill=(255,220,120), font=font(28))

for row, (sub, n) in enumerate(groups):
    files = sorted([f for f in os.listdir(os.path.join(BASE, sub)) if f.lower().endswith((".jpg",".png"))])[:n]
    for i, fn in enumerate(files):
        try:
            im = Image.open(os.path.join(BASE, sub, fn)).convert("RGB")
            im.thumbnail((CW-16, CH-30), Image.LANCZOS)
            sheet.paste(im, (i*CW + (CW-im.width)//2, row*(CH+30) + 44))
        except Exception as e:
            print(f"  跳过 {fn}: {e}")
    print(f"{sub}: 取 {len(files)} 张")

out = os.path.join(OUT, "_版画与工作站.jpg")
sheet.save(out, quality=85)
print(f"✅ {out} ({os.path.getsize(out)//1024} KB)")
