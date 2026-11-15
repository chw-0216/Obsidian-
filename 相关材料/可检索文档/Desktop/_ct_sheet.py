# -*- coding: utf-8 -*-
import os, sys, io
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
d = r"C:\Users\wardc\Desktop\_素材预览"
files = sorted([f for f in os.listdir(d) if f.endswith(".jpg") and not f.startswith("_")])
print(f"共 {len(files)} 张")

CW, CH = 480, 480
cols, rows = 4, 2
sheet = Image.new("RGB", (CW*cols, CH*rows), (24,24,24))
def font(sz):
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\arial.ttf"):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except Exception: pass
    return ImageFont.load_default()
f = font(22)

for i, name in enumerate(files[:8]):
    im = Image.open(os.path.join(d, name)).convert("RGB")
    im.thumbnail((CW-16, CH-52), Image.LANCZOS)
    x = (i % cols) * CW + (CW - im.width)//2
    y = (i // cols) * CH + 8
    sheet.paste(im, (x, y))
    ImageDraw.Draw(sheet).text(((i % cols)*CW + 10, (i//cols)*CH + CH - 38),
                               name.replace(".jpg",""), fill=(230,230,230), font=f)

out = os.path.join(d, "_联系表.jpg")
sheet.save(out, quality=88)
print(f"✅ {out}  ({os.path.getsize(out)//1024} KB)")
