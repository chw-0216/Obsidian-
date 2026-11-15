# -*- coding: utf-8 -*-
"""快速联系表：把某月 .hevc/.jpg 解码拼版，供目检"""
import os, sys, re, glob, subprocess, tempfile, math
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

ROOT = r"C:\Users\wardc\Desktop\微信照片_最新\原图_HD"
OUT = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\sheets"
os.makedirs(OUT, exist_ok=True)
TMP = os.path.join(OUT, "_tmpdec")
os.makedirs(TMP, exist_ok=True)

CELL = 260
COLS = 10

def decode(p):
    """返回 PIL Image；.hevc 用 ffmpeg 解码"""
    ext = os.path.splitext(p)[1].lower()
    if ext == ".hevc":
        o = os.path.join(TMP, os.path.splitext(os.path.basename(p))[0] + ".jpg")
        if not os.path.exists(o):
            r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", p, "-frames:v", "1",
                                "-vf", "scale=%d:-1" % CELL, o], capture_output=True)
            if r.returncode != 0 or not os.path.exists(o):
                return None
        p = o
    try:
        im = Image.open(p).convert("RGB")
        return im
    except Exception:
        return None

def sheet(month):
    d = os.path.join(ROOT, month)
    if not os.path.isdir(d):
        print("no dir", d); return
    files = sorted([f for f in os.listdir(d)
                    if os.path.splitext(f)[1].lower() in (".hevc", ".jpg", ".png")])
    print("%s : %d 文件" % (month, len(files)))
    ims = []
    for f in files:
        im = decode(os.path.join(d, f))
        if im: ims.append((f, im))
    if not ims: return
    rows = math.ceil(len(ims) / COLS)
    W = COLS * (CELL + 6) + 6
    H = rows * (CELL + 6) + 6
    canvas = Image.new("RGB", (W, H), (245, 244, 241))
    from PIL import ImageDraw
    dr = ImageDraw.Draw(canvas)
    for i, (f, im) in enumerate(ims):
        c, r = i % COLS, i // COLS
        x, y = 6 + c * (CELL + 6), 6 + r * (CELL + 6)
        im2 = im.copy(); im2.thumbnail((CELL, CELL))
        canvas.paste(im2, (x, y))
        dr.text((x + 3, y + CELL - 14), str(i + 1), fill=(180, 30, 30))
    out = os.path.join(OUT, "sheet_%s.jpg" % month)
    canvas.save(out, quality=82)
    print("  →", out, canvas.size)

for m in sys.argv[1:]:
    sheet(m)
