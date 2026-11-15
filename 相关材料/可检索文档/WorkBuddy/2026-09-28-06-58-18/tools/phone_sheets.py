# -*- coding: utf-8 -*-
r"""
phone_sheets.py —— 给「手机相机原片」出逐月带编号联系表，供人工筛选

输入：`--dir <手机相机原片目录>`（文件名形如 `20250901_224156_IMG_20250901_224156.jpg`）
产出：`<dir>\_联系表\`
  · `<前缀>.jpg`  带编号拼版（编号烧进图里，如 `2509-017`）
  · `<前缀>.csv`  编号 ↔ 文件名 ↔ 日期 对照
  · `00_手机原片总览.jpg`  每月一张代表图的「一图看全」
编号前缀 = `YYMM`（2025-09 → `2509`）；某月超过 --chunk 张时自动分段 `2509A` / `2509B`…

用法：
  python tools\phone_sheets.py --dir "C:\Users\wardc\Desktop\手机相机原片_2026-10-06"
"""
import os, sys, io, csv, glob, math, argparse, datetime
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
import contact_sheet as CS

Image.MAX_IMAGE_PIXELS = None
EXTS = (".jpg", ".jpeg", ".png", ".webp")
FONTS = [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc",
         r"C:\Windows\Fonts\simhei.ttf"]


def font(size):
    for f in FONTS:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                pass
    return ImageFont.load_default()


def month_of(name):
    """从 `20250901_224156_IMG_...jpg` 取 YYYY-MM"""
    if len(name) >= 8 and name[:8].isdigit():
        return name[:4] + "-" + name[4:6]
    return "未知"


def overview(rows, out, cols=6, cell=260):
    """每月取 6 张代表图的「一图看全」"""
    by = OrderedDict()
    for p in rows:
        by.setdefault(month_of(os.path.basename(p)), []).append(p)
    W = 190 + cols * (cell + 10) + 10
    H = 74 + len(by) * (cell + 10) + 10
    cv = Image.new("RGB", (W, H), (247, 246, 243))
    dr = ImageDraw.Draw(cv)
    dr.rectangle([0, 0, W, 74], fill=(31, 61, 43))
    dr.text((18, 12), "手机相机原片 · 逐月总览", fill=(255, 255, 255), font=font(28))
    dr.text((20, 48), "共 %d 张 ｜ %d 个月 ｜ 每行 6 张代表图（完整编号见各联系表）"
            % (len(rows), len(by)), fill=(207, 224, 212), font=font(13))
    f_lab, f_num = font(17), font(13)
    for ri, (mo, ps) in enumerate(by.items()):
        y = 74 + 10 + ri * (cell + 10)
        dr.rectangle([10, y, 180, y + cell], fill=(255, 255, 255), outline=(228, 224, 216))
        dr.text((22, y + 16), mo, fill=(31, 61, 43), font=font(21))
        dr.text((22, y + 46), "%d 张" % len(ps), fill=(158, 59, 46), font=font(15))
        step = max(1, (len(ps) - 1) // (cols - 1)) if len(ps) > 1 else 1
        picks = [ps[min(i * step, len(ps) - 1)] for i in range(cols)]
        for ci, p in enumerate(picks):
            x = 190 + ci * (cell + 10)
            try:
                with Image.open(p) as im:
                    im = im.convert("RGB")
                    im.thumbnail((cell, cell))
                    cv.paste(im, (x + (cell - im.width) // 2, y + (cell - im.height) // 2))
            except Exception:
                continue
            dr.rectangle([x + 3, y + 3, x + 3 + 20 + 11 * len(mo), y + 26], fill=(158, 59, 46))
            dr.text((x + 8, y + 6), mo, fill=(255, 255, 255), font=f_num)
    cv.save(out, quality=86)
    print("  → %s (%d×%d)" % (out, W, H))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--chunk", type=int, default=160, help="每张联系表最多多少张")
    ap.add_argument("--cols", type=int, default=10)
    ap.add_argument("--cell", type=int, default=230)
    a = ap.parse_args()

    rows = sorted(p for p in glob.glob(os.path.join(a.dir, "*"))
                  if os.path.splitext(p)[1].lower() in EXTS
                  and not os.path.basename(p).startswith("_")
                  and not os.path.basename(p).startswith("联系表"))
    print("扫描到 %d 张" % len(rows))
    if not rows:
        return
    sheet_dir = os.path.join(a.dir, "_联系表")
    os.makedirs(sheet_dir, exist_ok=True)

    by = OrderedDict()
    for p in rows:
        by.setdefault(month_of(os.path.basename(p)), []).append(p)

    allrec = []
    for mo, ps in by.items():
        pre = mo.replace("-", "")[2:]          # 2025-09 → 2509
        parts = math.ceil(len(ps) / a.chunk)
        for k in range(parts):
            seg = ps[k * a.chunk:(k + 1) * a.chunk]
            tag = pre + (chr(65 + k) if parts > 1 else "")
            items = [dict(path=p, date=os.path.basename(p)[:8], date_src="文件名",
                          category="手机相机原片", role="me",
                          session_name="手机相机", session_type="", width=0, height=0,
                          note=mo, md5=None) for p in seg]
            jp = os.path.join(sheet_dir, "%s.jpg" % tag)
            CS.build_sheet(items, jp, prefix=tag, title="手机相机原片 ｜ %s ｜ %d 张" % (mo, len(seg)),
                           cols=a.cols, cell=a.cell)
            allrec.append((tag, mo, len(seg)))
        print("  %s  共 %d 张 → %d 张表" % (mo, len(ps), parts))

    # 汇总 CSV
    rows_csv = []
    for tag, mo, n in allrec:
        c = os.path.join(sheet_dir, tag + ".csv")
        if os.path.exists(c):
            for r in csv.DictReader(io.open(c, encoding="utf-8-sig")):
                r["表"] = tag
                rows_csv.append(r)
    outp = os.path.join(sheet_dir, "联系表索引.csv")
    if rows_csv:
        with io.open(outp, "w", encoding="utf-8-sig", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=list(rows_csv[0].keys()))
            wr.writeheader(); wr.writerows(rows_csv)
        print("  → %s（%d 行）" % (outp, len(rows_csv)))

    overview(rows, os.path.join(sheet_dir, "00_手机原片总览.jpg"))
    print("\n联系表共 %d 张 → %s" % (len(allrec), sheet_dir))


if __name__ == "__main__":
    main()
