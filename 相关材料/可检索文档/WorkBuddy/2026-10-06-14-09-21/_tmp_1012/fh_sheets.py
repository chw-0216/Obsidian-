# -*- coding: utf-8 -*-
"""生成联系表，用于逐张识别 filehelper 2026-10-12 批次全部图片。"""
import os
from PIL import Image, ImageDraw, ImageFont

SRC = r"C:\Users\wardc\Desktop\文件传输助手_导出_2026-10-12\01_图片_2026-10-12"
OUT = r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21\_tmp_1012"

# 收集
items = []
for folder in sorted(os.listdir(SRC)):
    d = os.path.join(SRC, folder)
    if not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        if f.lower().endswith((".png", ".jpg")):
            items.append((folder, f, os.path.join(d, f)))

# 只做未识别的那批（排除已看过的）
SEEN = {"113031", "113038", "113048", "113410", "111337", "111402"}
def keep(p):
    return True

def sheet(rows_items, out_name, cols=4, cell=(640, 480)):
    rows = (len(rows_items) + cols - 1) // cols
    W = cols * cell[0]
    H = rows * (cell[1] + 34) + 12
    canvas = Image.new("RGB", (W, H), (250, 249, 245))
    dr = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
    except Exception:
        font = ImageFont.load_default()
    for i, (folder, f, p) in enumerate(rows_items):
        r, c = divmod(i, cols)
        x = c * cell[0]
        y = r * (cell[1] + 34) + 12
        try:
            im = Image.open(p).convert("RGB")
        except Exception:
            continue
        im.thumbnail((cell[0] - 16, cell[1] - 16), Image.LANCZOS)
        ox = x + (cell[0] - im.width) // 2
        oy = y + (cell[1] - im.height) // 2
        canvas.paste(im, (ox, oy))
        label = f"[{i+1}] {f[:34]}  ({folder[:2]})"
        dr.text((x + 8, y + cell[1] + 6), label, fill=(40, 45, 42), font=font)
    op = os.path.join(OUT, out_name)
    canvas.save(op, quality=88)
    print(op, canvas.size, len(rows_items), "张")

A = [it for it in items if any(k in it[1] for k in ("OPC", "教室", "木刻"))]
B = [it for it in items if any(k in it[1] for k in ("石版", "丝网", "四型", "蜡染", "冰醋酸", "展场"))]
sheet(A, "_fh_sheet_A.jpg", cols=3, cell=(660, 500))
sheet(B, "_fh_sheet_B.jpg", cols=3, cell=(660, 500))
