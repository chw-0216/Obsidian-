# -*- coding: utf-8 -*-
"""为关键时间簇生成联系表（contact sheet），便于目视挑选补充材料。"""
import os, csv, datetime, math
from PIL import Image, ImageDraw, ImageFont

ROOT = r"C:\Users\wardc\Desktop\中期汇报_2026-09\17_陈晔会话图片全量定位_2026-10-12"
IDX = os.path.join(ROOT, "01_定位索引.csv")
SHEET = os.path.join(ROOT, "04_联系表")
os.makedirs(SHEET, exist_ok=True)

rows = [r for r in csv.DictReader(open(IDX, encoding="utf-8-sig")) if r["解密产物"]]

CLUSTERS = {
    "A_0729政协主席与宣传部长": ("2026-07-29", "2026-07-30"),
    "B_0529至0608制版与配色决策": ("2026-05-29", "2026-06-09"),
    "C_0813至0820悲鸿文化墙科学家": ("2026-08-13", "2026-08-21"),
    "D_0410体验七幕概念图": ("2026-04-09", "2026-04-11"),
    "E_0924至1003海报与国庆": ("2026-09-24", "2026-10-04"),
    "F_0315至0330早期刻版与方案二": ("2026-03-14", "2026-03-31"),
    "G_0723至0728活动计划": ("2026-07-22", "2026-07-29"),
}

def font(sz):
    for p in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\msyhbd.ttc"]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except Exception: pass
    return ImageFont.load_default()

F = font(17)

for name, (d0, d1) in CLUSTERS.items():
    sel = [r for r in rows if d0 <= r["时间"][:10] <= d1]
    if not sel:
        print(f"{name}: 0 张（跳过）"); continue
    sel.sort(key=lambda r: r["时间"])
    COLS, CW, CH = 4, 300, 300
    ROWS = math.ceil(len(sel) / COLS)
    W, H = COLS * CW, ROWS * (CH + 26)
    sheet = Image.new("RGB", (W, H), (246, 242, 233))
    dr = ImageDraw.Draw(sheet)
    for i, r in enumerate(sel):
        cx, cy = (i % COLS) * CW, (i // COLS) * (CH + 26)
        try:
            im = Image.open(r["解密产物"]).convert("RGB")
        except Exception:
            dr.rectangle([cx+4, cy+4, cx+CW-8, cy+CH-8], fill=(230, 226, 218))
            continue
        im.thumbnail((CW - 10, CH - 10))
        ox = cx + (CW - 10 - im.width) // 2 + 5
        oy = cy + (CH - 10 - im.height) // 2 + 5
        sheet.paste(im, (ox, oy))
        lab = f"{i+1:02d} {r['时间'][5:16]} {r['发送方']}"
        dr.rectangle([cx, cy + CH, cx + CW, cy + CH + 24], fill=(32, 35, 33))
        dr.text((cx + 5, cy + CH + 3), lab, font=F, fill=(242, 237, 227))
    p = os.path.join(SHEET, f"{name}.png")
    sheet.save(p, quality=88)
    print(f"{name}: {len(sel)} 张 -> {p}  ({sheet.size[0]}x{sheet.size[1]})")

# 同时输出「本簇图片清单」便于对照编号
with open(os.path.join(ROOT, "04_联系表_清单.md"), "w", encoding="utf-8") as f:
    f.write("# 联系表图片清单（编号 → 文件）\n\n")
    for name, (d0, d1) in CLUSTERS.items():
        sel = sorted([r for r in rows if d0 <= r["时间"][:10] <= d1], key=lambda r: r["时间"])
        f.write(f"## {name}（{len(sel)} 张）\n\n")
        for i, r in enumerate(sel):
            f.write(f"{i+1:02d}. `{r['时间']}` {r['发送方']} [{r['清晰度档']}]  \n    `{r['解密产物']}`\n")
        f.write("\n")
print("-> 04_联系表_清单.md")
