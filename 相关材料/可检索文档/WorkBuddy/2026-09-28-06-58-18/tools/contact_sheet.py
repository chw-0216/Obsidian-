# -*- coding: utf-8 -*-
r"""
contact_sheet.py —— 带编号 / 缩略图 / 来源的「照片联系表」

任务书第一部分要求：
  「建**带编号、缩略图和来源的联系表**；重复照片归并，有内容差异的版本保留。」

产出（每次一份）：
  · `_tmp\sheets\<name>.jpg`     —— 拼版图（编号烧进图里，可直接打印/贴进汇报）
  · `_tmp\sheets\<name>.csv`     —— 编号对照表（编号 → 原始路径 / 日期 / 会话 / 谁发的 / 三类归属）

编号规则：`<组前缀>-<序号>`，如 `A-01`。组前缀用于「一段经历一组」。

★ 诚实边界
  · `.hevc` 用 ffmpeg 懒解码（缓存 `_tmp\hevc_cache\`），**原始文件不动**
  · 近纯色的空白/占位图会被标记 `blank=1` 并可剔除
  · 拍摄者只在有依据时写：`我发出`(role=me) / `他人发来`(role=them) / `待确认`

用法
----
  python tools\contact_sheet.py --query --lo 2026-04-01 --hi 2026-05-31 --prefix A
  python tools\contact_sheet.py --from-csv _tmp\sheets\x.csv
"""
import os, io, sys, csv, re, math, argparse, sqlite3, datetime, traceback, subprocess
from collections import Counter, defaultdict

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
BATCH = os.path.join(WS, "_tmp", "batch")
DB = os.path.join(BATCH, "batch.sqlite")
SHEETS = os.path.join(WS, "_tmp", "sheets")
CACHE = os.path.join(WS, "_tmp", "hevc_cache")

from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\simsun.ttc",
]


def _font(size):
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                pass
    return ImageFont.load_default()


def decode(p, md5=None):
    """把 .hevc 解成 jpg（懒解码，带缓存）。返回 jpg 路径或 None。"""
    if not p.lower().endswith(".hevc"):
        return p if os.path.exists(p) else None
    os.makedirs(CACHE, exist_ok=True)
    key = md5 or (os.path.splitext(os.path.basename(p))[0])
    o = os.path.join(CACHE, key + ".jpg")
    if not os.path.exists(o):
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", p,
                            "-frames:v", "1", "-q:v", "3", o], capture_output=True)
        if r.returncode != 0 or not os.path.exists(o):
            return None
    return o


def is_blank(img_path):
    try:
        with Image.open(img_path) as im:
            from PIL import ImageStat
            g = im.convert("L").resize((64, 64))
            return ImageStat.Stat(g).stddev[0] < 3.0
    except Exception:
        return False


def query(lo=None, hi=None, roots=None, cats=None, roles=None,
          min_w=0, min_bytes=0, kws=None, limit=None, order="date,width desc"):
    c = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    w, a = ["1=1"], []
    if lo:
        w.append("date>=?"); a.append(lo)
    if hi:
        w.append("date<=?"); a.append(hi)
    if roots:
        w.append("root in (%s)" % ",".join("?" * len(roots))); a += list(roots)
    if cats:
        w.append("(" + " or ".join("category like ?" for _ in cats) + ")")
        a += [x + "%" for x in cats]
    if roles:
        w.append("(" + " or ".join(["role=?" if r else "role is null" for r in roles]) + ")")
        a += [r for r in roles if r]
    if min_w:
        w.append("width>=?"); a.append(min_w)
    if min_bytes:
        w.append("bytes>=?"); a.append(min_bytes)
    if kws:
        w.append("(" + " or ".join(["path like ? or session_name like ?" for _ in kws]) + ")")
        for k in kws:
            a += ["%" + k + "%", "%" + k + "%"]
    sql = "select * from photos where " + " and ".join(w) + " order by " + order
    if limit:
        sql += " limit %d" % limit
    rows = [dict(r) for r in c.execute(sql, a)]
    c.close()
    return rows


def build_sheet(items, out_jpg, prefix="A", title="", cols=8, cell=300,
                drop_blank=True, show_meta=True):
    """items: [{path,date,session,role,category,note,md5}] → 拼版 + 编号对照"""
    os.makedirs(SHEETS, exist_ok=True)
    used, skipped = [], []
    for it in items:
        jp = decode(it["path"], it.get("md5"))
        if not jp:
            skipped.append((it, "解码失败")); continue
        if drop_blank and is_blank(jp):
            skipped.append((it, "空白/占位图")); continue
        used.append((it, jp))
    if not used:
        print("  无可拼版图片"); return None, None

    f_num = _font(26)
    f_lab = _font(14)
    pad, cap = 8, 46
    cw, ch = cell + pad, cell + cap + pad
    rows = math.ceil(len(used) / cols)
    W, H = cols * cw + pad, rows * ch + pad + (48 if title else 0)
    canvas = Image.new("RGB", (W, H), (247, 246, 243))
    dr = ImageDraw.Draw(canvas)
    y0 = 0
    if title:
        dr.text((pad + 4, 12), title, fill=(31, 61, 43), font=_font(30))
        y0 = 48

    recs = []
    for i, (it, jp) in enumerate(used):
        cidx, ridx = i % cols, i // cols
        x = pad + cidx * cw
        y = y0 + pad + ridx * ch
        try:
            with Image.open(jp) as im:
                im = im.convert("RGB")
                im.thumbnail((cell, cell))
                canvas.paste(im, (x + (cell - im.width) // 2, y + (cell - im.height) // 2))
        except Exception:
            skipped.append((it, "读取失败")); continue
        no = "%s-%02d" % (prefix, i + 1)
        # 编号（左上角红底白字）
        bx = x + 4
        bw = 22 + 15 * len(no)
        dr.rectangle([bx, y + 4, bx + bw, y + 36], fill=(158, 59, 46))
        dr.text((bx + 7, y + 6), no, fill=(255, 255, 255), font=f_num)
        if show_meta:
            d = (it.get("date") or "日期待定")
            who = {"me": "我发出", "them": "他人发来"}.get(it.get("role"), "拍摄者待确认")
            dr.text((x + 4, y + cell + 6), "%s ｜ %s" % (d, who), fill=(70, 68, 64), font=f_lab)
            sess = (it.get("session_name") or "—")
            dr.text((x + 4, y + cell + 24), sess[:26], fill=(120, 116, 110), font=f_lab)
        recs.append(dict(编号=no, 日期=d, 日期来源=it.get("date_src") or "",
                         三类归属=it.get("category") or "", 拍摄者依据=who,
                         会话=it.get("session_name") or "", 会话类型=it.get("session_type") or "",
                         宽=it.get("width") or 0, 高=it.get("height") or 0,
                         原始路径=it.get("path") or "", 文件=os.path.basename(it.get("path") or ""),
                         说明=it.get("note") or ""))

    canvas.save(out_jpg, quality=84)
    csvp = os.path.splitext(out_jpg)[0] + ".csv"
    with io.open(csvp, "w", encoding="utf-8-sig", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(recs[0].keys()))
        wr.writeheader(); wr.writerows(recs)
    print("  → %s（%d 张，%s）" % (out_jpg, len(recs), "%dx%d" % canvas.size))
    print("  → %s" % csvp)
    if skipped:
        cnt = Counter(r for _, r in skipped)
        print("     剔除：%s" % dict(cnt))
    return out_jpg, csvp


def from_dir(d, recursive=True, min_bytes=4096):
    """直接扫目录（不走库）——用于目检还没入库的新来源"""
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".gif", ".webp",
            ".heic", ".hevc", ".cr2", ".cr3", ".arw", ".dng", ".nef", ".psd"}
    out = []
    if recursive:
        it = os.walk(d)
        for dp, ds, fs in it:
            for fn in fs:
                if os.path.splitext(fn)[1].lower() in exts:
                    p = os.path.join(dp, fn)
                    try:
                        if os.path.getsize(p) >= min_bytes:
                            out.append(dict(path=p, date="", date_src="目录扫描",
                                            category="待确认", role=None,
                                            session_name=os.path.basename(dp),
                                            session_type="", width=0, height=0,
                                            note=os.path.basename(dp), md5=None))
                    except Exception:
                        pass
    else:
        for fn in sorted(os.listdir(d)):
            if os.path.splitext(fn)[1].lower() in exts:
                out.append(dict(path=os.path.join(d, fn), date="", date_src="目录扫描",
                                category="待确认", role=None, session_name=os.path.basename(d),
                                session_type="", width=0, height=0, note="", md5=None))
    out.sort(key=lambda x: x["path"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", help="直接扫这个目录（不走库）")
    ap.add_argument("--no-rec", action="store_true")
    ap.add_argument("--lo"); ap.add_argument("--hi")
    ap.add_argument("--roots", nargs="*")
    ap.add_argument("--cats", nargs="*")
    ap.add_argument("--roles", nargs="*", help="me them none")
    ap.add_argument("--min-w", type=int, default=0)
    ap.add_argument("--min-bytes", type=int, default=0)
    ap.add_argument("--kws", nargs="*")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--prefix", default="A")
    ap.add_argument("--name", default=None)
    ap.add_argument("--title", default="")
    ap.add_argument("--cols", type=int, default=8)
    ap.add_argument("--cell", type=int, default=300)
    ap.add_argument("--keep-blank", action="store_true")
    a = ap.parse_args()
    roles = None
    if a.roles:
        roles = [None if r.lower() in ("none", "null", "-") else r for r in a.roles]
    if a.dir:
        items = from_dir(a.dir, not a.no_rec, a.min_bytes or 4096)
    else:
        items = query(a.lo, a.hi, a.roots, a.cats, roles, a.min_w, a.min_bytes, a.kws, a.limit)
    print("命中 %d 张" % len(items))
    name = a.name or ("sheet_%s_%s" % (a.prefix, (a.lo or "all").replace("-", "")))
    build_sheet(items, os.path.join(SHEETS, name + ".jpg"), a.prefix,
                a.title or ("联系表 " + a.prefix), a.cols, a.cell, not a.keep_blank)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
