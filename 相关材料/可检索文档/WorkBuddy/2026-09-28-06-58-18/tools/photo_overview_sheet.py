# -*- coding: utf-8 -*-
r"""
photo_overview_sheet.py —— 把「照片汇总」11 个主题压成一张缩略总览图（一图看全）

产出：`<汇总目录>\00_缩略总览.jpg` —— 11 行（每主题一行）× 每行 5 张代表图 + 主题名/张数。

用法：python tools\photo_overview_sheet.py [汇总目录]
"""
import os, sys, math, io, glob
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None

DEFAULT_DIR = r"C:\Users\wardc\Desktop\中期汇报_2026-09\10_照片汇总_2026-10-06"
FONTS = [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc",
         r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\simsun.ttc"]

CELL = 250
COLS = 5
LABEL_W = 210
PAD = 10
HEADER = 74


def font(size):
    for f in FONTS:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                pass
    return ImageFont.load_default()


def pick_even(paths, n):
    """在列表里等距取 n 张（保证头尾都取到）"""
    if len(paths) <= n:
        return paths
    step = (len(paths) - 1) / (n - 1)
    return [paths[round(i * step)] for i in range(n)]


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DIR
    themes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    rows = []
    for t in themes:
        d = os.path.join(root, t)
        pics = sorted(p for p in glob.glob(os.path.join(d, "*"))
                      if os.path.splitext(p)[1].lower() in (".jpg", ".jpeg", ".png", ".webp")
                      and not os.path.basename(p).startswith("联系表"))
        if pics:
            rows.append((t, pics))
    if not rows:
        print("没有可用主题目录"); return

    cw = CELL + PAD
    W = LABEL_W + COLS * cw + PAD
    H = HEADER + len(rows) * (CELL + PAD) + PAD
    canvas = Image.new("RGB", (W, H), (247, 246, 243))
    dr = ImageDraw.Draw(canvas)

    dr.rectangle([0, 0, W, HEADER], fill=(31, 61, 43))
    dr.text((PAD + 8, 14), "中期汇报 · 照片汇总缩略总览", fill=(255, 255, 255), font=font(30))
    dr.text((PAD + 10, 50), "%d 个主题 ｜ 每主题取 5 张代表图 ｜ 完整编号见各目录 联系表_XX.jpg"
            % len(rows), fill=(207, 224, 212), font=font(14))

    f_lab = font(17)
    f_num = font(13)
    for ri, (t, pics) in enumerate(rows):
        y = HEADER + PAD + ri * (CELL + PAD)
        # 左侧主题标签
        dr.rectangle([PAD, y, PAD + LABEL_W - PAD - 6, y + CELL], fill=(255, 255, 255),
                     outline=(228, 224, 216))
        name = t.split("_", 1)[1] if "_" in t else t
        num = t.split("_", 1)[0]
        dr.text((PAD + 10, y + 12), num, fill=(158, 59, 46), font=font(22))
        # 主题名按宽度折行
        line, yy = "", y + 46
        for ch in name:
            if dr.textlength(line + ch, font=f_lab) > LABEL_W - 30:
                dr.text((PAD + 10, yy), line, fill=(31, 61, 43), font=f_lab); yy += 22; line = ""
            line += ch
        if line:
            dr.text((PAD + 10, yy), line, fill=(31, 61, 43), font=f_lab)
        dr.text((PAD + 10, y + CELL - 26), "%d 张" % len(pics), fill=(138, 134, 126), font=f_num)

        for ci, p in enumerate(pick_even(pics, COLS)):
            x = PAD + LABEL_W + ci * cw
            try:
                with Image.open(p) as im:
                    im = im.convert("RGB")
                    im.thumbnail((CELL, CELL))
                    canvas.paste(im, (x + (CELL - im.width) // 2, y + (CELL - im.height) // 2))
            except Exception as e:
                print("  跳过", p, e)
                continue
            # 序号角标
            no = "%s-%02d" % (num, pics.index(p) + 1)
            dr.rectangle([x + 4, y + 4, x + 4 + 20 + 13 * len(no), y + 30], fill=(158, 59, 46))
            dr.text((x + 9, y + 7), no, fill=(255, 255, 255), font=f_num)

    out = os.path.join(root, "00_缩略总览.jpg")
    canvas.save(out, quality=86)
    print("→ %s  (%d×%d, %.2f MB)" % (out, W, H, os.path.getsize(out) / 1048576))


if __name__ == "__main__":
    main()
