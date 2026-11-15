# -*- coding: utf-8 -*-
r"""
extract_materials.py —— 材料正文提取（把「找到文件」推进到「提取正文」）

设计原则
--------
1. **只读源**：所有材料 `open(..., 'rb')` 只读；产物只写 `_tmp\batch\text\`。
2. **四态推进**：`found` → `extracted` → `modeled` → `analyzed`。本脚本只做 `extracted`。
3. **失败要分类**：不是「失败」一个筐，而是 `fail_reason` + `need_tool` 分开记 ——
   因为「扫描件没文字层」和「文件损坏」是两件完全不同的事。
4. **不虚报**：提不出正文就写提不出，**不算已读**。

工具依赖（★ 用系统 Python 3.12，它才有这些包）
--------------------------------------------
  python-docx 1.2.0 · openpyxl 3.1.5 · python-pptx 1.0.2 · pypdf 6.15 · PyMuPDF 1.27 · Pillow 12.2

用法
----
  python tools\extract_materials.py --stage text     # 纯文本类（txt/md/csv/json/html/代码…）
  python tools\extract_materials.py --stage office   # docx/xlsx/pptx
  python tools\extract_materials.py --stage pdf      # PDF（自动分辨「文字型」与「扫描件」）
  python tools\extract_materials.py --stage queue    # 只做队列归类（图片/音频/视频 → OCR/ASR/vision）
  python tools\extract_materials.py --stage all
  python tools\extract_materials.py --report
"""
import os, io, re, sys, csv, json, time, sqlite3, datetime, traceback, argparse

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
BATCH = os.path.join(WS, "_tmp", "batch")
DB = os.path.join(BATCH, "batch.sqlite")
TEXTDIR = os.path.join(BATCH, "text")

MAX_BYTES = 20 << 20          # 单文件超过 20 MB 不做正文提取（记 skip）
MAX_CHARS = 400_000           # 单文件最多留 40 万字符
PDF_TEXT_MIN = 80             # PDF 文字层少于这个字数 → 判为扫描件

TEXT_EXT = {".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".jsonl", ".xml", ".html", ".htm",
            ".py", ".js", ".mjs", ".ts", ".tsx", ".jsx", ".ps1", ".sh", ".bat", ".cmd", ".css",
            ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf", ".log", ".sql", ".r", ".m", ".java",
            ".c", ".h", ".cpp", ".cs", ".go", ".rs", ".php", ".rb", ".vue", ".svelte", ".svg"}
OFFICE_EXT = {".docx", ".xlsx", ".pptx"}
PDF_EXT = {".pdf"}
IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".raw"}
AUDIO_EXT = {".wav", ".mp3", ".m4a", ".amr", ".aac", ".flac", ".ogg", ".silk"}
VIDEO_EXT = {".mp4", ".mov", ".avi", ".mkv", ".hevc", ".wmv", ".flv", ".m4v", ".webm"}

ENCODINGS = ["utf-8-sig", "utf-8", "gb18030", "gbk", "big5", "utf-16", "latin-1"]


# ──────────────────────────────────────────────────────── 工具
def read_text_bytes(path):
    """按常见中文编码依次尝试，返回 (text, encoding)"""
    with io.open(path, "rb") as f:
        raw = f.read(MAX_BYTES)
    for enc in ENCODINGS:
        try:
            return raw.decode(enc), enc
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8/replace"


def strip_html(t):
    t = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = (t.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<")
          .replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'"))
    return re.sub(r"[ \t\x0b\f\r]+", " ", t)


def extract_docx(path):
    import docx
    d = docx.Document(path)
    out = []
    for p in d.paragraphs:
        s = (p.text or "").strip()
        if s:
            out.append(s)
    for ti, tb in enumerate(d.tables, 1):
        out.append("[表 %d]" % ti)
        for row in tb.rows:
            cells = [(c.text or "").replace("\n", " ").strip() for c in row.cells]
            if any(cells):
                out.append(" | ".join(cells))
    return "\n".join(out)


def extract_xlsx(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = []
    for ws in wb.worksheets:
        out.append("[工作表] %s" % ws.title)
        n = 0
        for row in ws.iter_rows(values_only=True):
            vals = ["" if v is None else str(v).strip() for v in row]
            if any(vals):
                out.append(" | ".join(vals))
                n += 1
            if n > 4000:
                out.append("…（截断）")
                break
    wb.close()
    return "\n".join(out)


def extract_pptx(path):
    from pptx import Presentation
    prs = Presentation(path)
    out = []
    for i, slide in enumerate(prs.slides, 1):
        out.append("[第 %d 页]" % i)
        for sh in slide.shapes:
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    s = "".join(r.text for r in p.runs).strip()
                    if s:
                        out.append(s)
            if getattr(sh, "has_table", False) and sh.has_table:
                for row in sh.table.rows:
                    cells = [(c.text or "").replace("\n", " ").strip() for c in row.cells]
                    if any(cells):
                        out.append(" | ".join(cells))
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None:
            nt = (slide.notes_slide.notes_text_frame.text or "").strip()
            if nt:
                out.append("[备注] " + nt)
    return "\n".join(out)


def extract_pdf(path):
    """返回 (text, npages, kind)；kind ∈ text / scanned / error"""
    import fitz  # PyMuPDF
    doc = fitz.open(path)
    try:
        npages = doc.page_count
        parts = []
        for i in range(min(npages, 300)):
            parts.append(doc.load_page(i).get_text("text") or "")
        txt = "\n".join(parts).strip()
        txt = re.sub(r"\n{3,}", "\n\n", txt)
        if len(txt) < PDF_TEXT_MIN:
            return txt, npages, "scanned"
        return txt, npages, "text"
    finally:
        doc.close()


def save_text(mid, text):
    os.makedirs(TEXTDIR, exist_ok=True)
    p = os.path.join(TEXTDIR, "%d.txt" % mid)
    io.open(p, "w", encoding="utf-8").write(text)
    return p


# ──────────────────────────────────────────────────────── 主流程
def run_stage(c, stage, limit=None):
    if stage == "text":
        where = "ext like '%.txt' or " + " or ".join("ext='%s'" % e for e in sorted(TEXT_EXT))
        where = "(" + where + ")"
    elif stage == "office":
        where = " or ".join("ext='%s'" % e for e in sorted(OFFICE_EXT))
    elif stage == "pdf":
        where = "ext='.pdf'"
    elif stage == "queue":
        where = " or ".join("ext='%s'" % e for e in sorted(IMG_EXT | AUDIO_EXT | VIDEO_EXT))
    else:
        where = "1=1"

    q = ("select mid,path,ext,kind,bytes,need_tool,fail_reason from materials "
         "where (%s) order by bytes desc" % where)
    if limit:
        q += " limit %d" % limit
    rows = list(c.execute(q))

    ok = skip = fail = 0
    stats = {}
    t0 = time.time()
    for i, (mid, path, ext, kind, nbytes, need_tool, fail_reason) in enumerate(rows, 1):
        ext = (ext or "").lower()
        res = None
        try:
            # ---- 队列归类（不提取正文，只定队列）----
            if stage == "queue":
                if ext in IMG_EXT:
                    res = ("queue", "ocr", "图片 → OCR/图像理解队列")
                elif ext in AUDIO_EXT:
                    res = ("queue", "asr", "音频 → 转录队列")
                elif ext in VIDEO_EXT:
                    res = ("queue", "asr/vision", "视频 → 抽帧 + 转录队列")
                else:
                    res = ("skip", "", "非队列类型")

            # ---- 正文提取 ----
            elif not os.path.exists(path):
                res = ("fail", "", "文件不存在（登记后已被移动/删除）")
            elif nbytes and nbytes > MAX_BYTES:
                res = ("skip", "", "超过 %d MB，暂不提取" % (MAX_BYTES >> 20))
            elif ext in TEXT_EXT:
                t, enc = read_text_bytes(path)
                if ext in (".html", ".htm", ".xml", ".svg"):
                    t = strip_html(t)
                t = t[:MAX_CHARS]
                if not t.strip():
                    res = ("fail", "", "文本为空（0 字节或全空白）")
                else:
                    save_text(mid, t)
                    res = ("ok", "", "编码 %s ｜ %d 字" % (enc, len(t)))
            elif ext == ".docx":
                t = extract_docx(path)[:MAX_CHARS]
                res = ("ok", "", "%d 字" % len(t)) if t.strip() else ("fail", "", "docx 无正文")
                if res[0] == "ok":
                    save_text(mid, t)
            elif ext == ".xlsx":
                t = extract_xlsx(path)[:MAX_CHARS]
                res = ("ok", "", "%d 字" % len(t)) if t.strip() else ("fail", "", "xlsx 无正文")
                if res[0] == "ok":
                    save_text(mid, t)
            elif ext == ".pptx":
                t = extract_pptx(path)[:MAX_CHARS]
                res = ("ok", "", "%d 字" % len(t)) if t.strip() else ("fail", "", "pptx 无正文")
                if res[0] == "ok":
                    save_text(mid, t)
            elif ext == ".pdf":
                t, npages, k = extract_pdf(path)
                if k == "scanned":
                    res = ("queue", "ocr", "PDF 无文字层（%d 页）→ OCR 队列" % npages)
                else:
                    t = t[:MAX_CHARS]
                    save_text(mid, t)
                    res = ("ok", "", "%d 页 ｜ %d 字" % (npages, len(t)))
            else:
                res = ("skip", "", "未覆盖类型")

        except ImportError as e:
            res = ("fail", "", "缺依赖：%s" % e)
        except Exception as e:
            res = ("fail", "", "%s: %s" % (type(e).__name__, str(e)[:90]))

        status, need, note = res
        if status == "ok":
            ok += 1
            c.execute("update materials set extracted=1, fail_reason='', need_tool=? where mid=?",
                      (need, mid))
        elif status == "queue":
            c.execute("update materials set extracted=0, fail_reason=?, need_tool=? where mid=?",
                      (note, need, mid))
        elif status == "fail":
            fail += 1
            c.execute("update materials set extracted=0, fail_reason=?, need_tool=? where mid=?",
                      (note, need, mid))
        else:
            skip += 1
            if note:
                c.execute("update materials set fail_reason=? where mid=?", (note, mid))

        stats[note.split("｜")[0][:34] if note else "—"] = \
            stats.get(note.split("｜")[0][:34] if note else "—", 0) + 1

        if i % 500 == 0:
            c.commit()
            print("   … %d/%d  ok=%d fail=%d skip=%d" % (i, len(rows), ok, fail, skip))

    c.commit()
    return len(rows), ok, fail, skip, stats, time.time() - t0


def report(c):
    print("=" * 78)
    print("正文提取现状")
    print("=" * 78)
    tot = c.execute("select count(*) from materials").fetchone()[0]
    ext = c.execute("select count(*) from materials where extracted=1").fetchone()[0]
    nf = c.execute("select count(*) from materials where fail_reason<>'' and extracted=0").fetchone()[0]
    q = c.execute("select need_tool,count(*) from materials where need_tool<>'' "
                  "group by 1 order by 2 desc").fetchall()
    print("登记 %d ｜ 已提取正文 %d（%.1f%%）｜ 有失败/队列标记 %d" % (tot, ext, 100 * ext / max(tot, 1), nf))
    print("\n按待办队列：")
    for k, n in q:
        print("  %-16s %7d" % (k, n))
    print("\n失败原因 TOP15：")
    for r in c.execute("select fail_reason,count(*) from materials where fail_reason<>'' "
                       "group by 1 order by 2 desc limit 15"):
        print("  %-56s %6d" % (r[0][:56], r[1]))
    print("\n按类型：")
    for r in c.execute("select ext,count(*),sum(extracted) from materials "
                       "group by 1 order by 2 desc limit 18"):
        print("  %-10s %7d  已提取 %s" % (r[0] or "(无)", r[1], r[2] or 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=["text", "office", "pdf", "queue", "all", "report"])
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()

    c = sqlite3.connect(DB)
    if a.stage == "report":
        report(c)
        return

    stages = ["text", "office", "pdf", "queue"] if a.stage == "all" else [a.stage]
    for st in stages:
        print("=" * 78)
        print("提取阶段：%s" % st)
        print("=" * 78)
        n, ok, fail, skip, stats, dt = run_stage(c, st, a.limit)
        print("扫描 %d ｜ 成功 %d ｜ 失败 %d ｜ 跳过 %d ｜ %.1f 秒" % (n, ok, fail, skip, dt))
        for k, v in sorted(stats.items(), key=lambda x: -x[1])[:12]:
            print("    %-38s %6d" % (k, v))
    print()
    report(c)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
