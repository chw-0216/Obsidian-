# -*- coding: utf-8 -*-
r"""
extract_office_images.py —— 从 Office 文件里直接抠出内嵌图片（★ 不需要 OCR）

为什么单独做
------------
任务书第三部分说得很对：**PPTX / DOCX / XLSX 本身就能直接提取文字和图片**。
- `python-pptx`：`shape.shape_type == PICTURE` → `shape.image.blob`（原图二进制）
- `python-docx`：`document.part.related_parts` 里 `image/*` 类型
- `openpyxl`：`ws._images` → `img._data()`

这些**不是截图**，是**原始嵌入图**，分辨率常常比微信照片高 ——
所以「部分材料不需要 OCR」这句话是对的，而且还能**白捡一批高清原图**。

产出
----
  `_tmp\batch\office_images\<源文件序号>_<n>.<ext>`  +  `office_images.csv`
  （同时登记进 batch.sqlite 的 photos 表，category = 「⑤ Office 内嵌图」）

用法
----
  python tools\extract_office_images.py
"""
import os, io, re, sys, csv, json, zipfile, sqlite3, datetime, traceback
from collections import Counter

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
BATCH = os.path.join(WS, "_tmp", "batch")
DB = os.path.join(BATCH, "batch.sqlite")
OUTDIR = os.path.join(BATCH, "office_images")
MANIFEST = os.path.join(BATCH, "office_images.csv")

MAX_PER_FILE = 200
MIN_BYTES = 8 << 10        # 小于 8 KB 的多半是图标/装饰，跳过


def from_pptx(path, out_prefix):
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    got = []
    prs = Presentation(path)
    n = 0
    for si, slide in enumerate(prs.slides, 1):
        for sh in slide.shapes:
            try:
                is_pic = (sh.shape_type == MSO_SHAPE_TYPE.PICTURE)
            except Exception:
                is_pic = False
            if not is_pic:
                continue
            try:
                img = sh.image
                blob = img.blob
                ext = (img.ext or "png").lower()
            except Exception:
                continue
            if len(blob) < MIN_BYTES:
                continue
            n += 1
            p = "%s_p%02d_%02d.%s" % (out_prefix, si, n, ext)
            io.open(os.path.join(OUTDIR, p), "wb").write(blob)
            got.append((p, len(blob), "PPTX 第 %d 页" % si))
            if n >= MAX_PER_FILE:
                return got
    return got


def from_docx(path, out_prefix):
    import docx
    got = []
    d = docx.Document(path)
    n = 0
    for rid, part in d.part.related_parts.items():
        ct = getattr(part, "content_type", "") or ""
        if not ct.startswith("image/"):
            continue
        try:
            blob = part.blob
        except Exception:
            continue
        if len(blob) < MIN_BYTES:
            continue
        ext = ct.split("/")[-1].lower().replace("jpeg", "jpg")
        n += 1
        p = "%s_%02d.%s" % (out_prefix, n, ext)
        io.open(os.path.join(OUTDIR, p), "wb").write(blob)
        got.append((p, len(blob), "DOCX 内嵌"))
        if n >= MAX_PER_FILE:
            break
    return got


def from_xlsx(path, out_prefix):
    import openpyxl
    got = []
    wb = openpyxl.load_workbook(path)
    n = 0
    for ws in wb.worksheets:
        for im in getattr(ws, "_images", []) or []:
            try:
                blob = im._data()
                ext = (getattr(im, "format", None) or "png").lower()
            except Exception:
                continue
            if len(blob) < MIN_BYTES:
                continue
            n += 1
            p = "%s_s%d_%02d.%s" % (out_prefix, wb.index(ws) + 1, n, ext)
            io.open(os.path.join(OUTDIR, p), "wb").write(blob)
            got.append((p, len(blob), "XLSX %s" % ws.title))
    wb.close()
    return got


def from_zip_fallback(path, out_prefix):
    """★ 兜底：Office 文件本质是 zip —— 直接扫 media/ 目录，能救回上面 API 漏掉的图"""
    got = []
    n = 0
    try:
        with zipfile.ZipFile(path) as z:
            for nm in z.namelist():
                if not re.search(r"(media|images)/", nm, re.I):
                    continue
                if not re.search(r"\.(png|jpe?g|gif|bmp|tiff?|emf|wmf)$", nm, re.I):
                    continue
                try:
                    blob = z.read(nm)
                except Exception:
                    continue
                if len(blob) < MIN_BYTES:
                    continue
                ext = os.path.splitext(nm)[1].lower().lstrip(".")
                n += 1
                p = "%s_zip%02d.%s" % (out_prefix, n, ext)
                io.open(os.path.join(OUTDIR, p), "wb").write(blob)
                got.append((p, len(blob), "ZIP 兜底：%s" % nm))
    except Exception:
        pass
    return got


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    c = sqlite3.connect(DB)
    rows = list(c.execute("""select mid,path,ext,bytes from materials
                             where ext in ('.pptx','.docx','.xlsx')
                             order by bytes desc"""))
    print("=" * 78)
    print("Office 内嵌图片提取")
    print("=" * 78)
    print("待处理 %d 个 Office 文件" % len(rows))

    out = []
    stat = Counter()
    for i, (mid, path, ext, nb) in enumerate(rows, 1):
        if not os.path.exists(path):
            stat["文件不存在"] += 1
            continue
        pref = "M%05d" % mid
        got = []
        try:
            if ext == ".pptx":
                got = from_pptx(path, pref)
            elif ext == ".docx":
                got = from_docx(path, pref)
            elif ext == ".xlsx":
                got = from_xlsx(path, pref)
        except Exception as e:
            stat["API 失败: %s" % type(e).__name__] += 1
        if not got:
            got = from_zip_fallback(path, pref)
            if got:
                stat["ZIP 兜底救回"] += 1
        if got:
            stat["有图"] += 1
            for p, sz, where in got:
                out.append({"源文件": os.path.basename(path), "源路径": path,
                            "图": p, "字节": sz, "位置": where})
        else:
            stat["无内嵌图"] += 1
        if i % 20 == 0:
            print("   … %d/%d" % (i, len(rows)))

    with io.open(MANIFEST, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["源文件", "源路径", "图", "字节", "位置"])
        w.writeheader()
        w.writerows(out)

    # 登记进 photos 表（去重：按 md5）
    import hashlib
    added = 0
    seen = set(r[0] for r in c.execute("select md5 from photos where md5 is not null"))
    for r in out:
        p = os.path.join(OUTDIR, r["图"])
        try:
            h = hashlib.md5(io.open(p, "rb").read()).hexdigest()
        except Exception:
            continue
        if h in seen:
            continue
        seen.add(h)
        src_date = ""
        c.execute("""insert into photos(path,root,rel,name,ext,bytes,md5,dup_of,ts,date,date_src,
                     session_key,session_name,session_type,role,sender,width,height,category,note)
                     values(?,?,?,?,?,?,?,NULL,0,?,?,?,?,?,?,?,0,0,?,?)""",
                  (p, "Office内嵌图", r["图"], r["图"], os.path.splitext(r["图"])[1].lower(),
                   r["字节"], h, "", "来自 Office 内嵌（日期待定）", "", r["源文件"], "Office",
                   "", "", "⑤ Office 内嵌图", r["位置"]))
        added += 1
    c.commit()

    print("\n有内嵌图的文件 %d 个 ｜ 抠出图片 %d 张 ｜ 新登记 %d 张（去重后）"
          % (stat.get("有图", 0), len(out), added))
    for k, v in stat.most_common():
        print("  %-24s %4d" % (k, v))
    print("→ %s" % MANIFEST)
    print("→ %s" % OUTDIR)
    c.close()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
