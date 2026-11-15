# -*- coding: utf-8 -*-
r"""
hevc_photos.py —— 把被漏掉的 .hevc 高清静帧纳入照片索引

★★★ 背景（2026-10-06 发现）
---------------------------
`微信照片_最新\原图_HD` 与 `\图片` 里各有一大批 **`.hevc` 文件**。
它们**不是视频**，而是 WeChat 把「原图」以 **HEVC 单帧**编码存储的**高清静帧图片**
（`ffprobe` 报 `format_name=hevc, codec_type=video`，但 `ffmpeg -frames:v 1` 能解出完整画面）。

旧版 `photo_index.py` 的 `IMG_EXT` 不含 `.hevc` → **9,766 张高清静帧整批漏掉**。
它们恰好覆盖 2025-05 → 2026-09，密度最高在 2026-01（北京台实习期）与 2026-04/05（厦门授课期）。

本脚本做的事
------------
  1. 扫 `原图_HD` / `图片` 里的 `.hevc`
  2. `ffprobe` 取真实宽高（**不解码，秒级**）
  3. 算**内容 MD5** → 对上微信图片消息 → 拿 **ts / 会话 / role**
  4. 写进 `photos` 表（root = `微信原图HEVC` / `微信图片HEVC`）
  5. 需要真正看图时，`decode()` 懒解码到 `_tmp\hevc_cache\<md5>.jpg`（并记 `is_blank`）

★ 与 `photo_index.py` 的关系
  `photo_index.py` 负责 jpg/png/tif 等常规图片；本脚本**只补 .hevc**，
  两者共用同一张 `photos` 表，用 `root` 区分，互不覆盖（本脚本只 delete 自己那两个 root）。

用法
----
  python tools\hevc_photos.py --build        # 建索引（约 6-12 分钟，可后台跑）
  python tools\hevc_photos.py --report
  python tools\hevc_photos.py --decode --date 2026-04-01 2026-05-31
"""
import os, io, re, sys, csv, json, time, sqlite3, hashlib, datetime, argparse, traceback, subprocess
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
BATCH = os.path.join(WS, "_tmp", "batch")
DB = os.path.join(BATCH, "batch.sqlite")
CACHE = os.path.join(WS, "_tmp", "hevc_cache")
INDEX_DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"

HEVC_ROOTS = [
    (r"C:\Users\wardc\Desktop\微信照片_最新\原图_HD", "微信原图HEVC", 1),
    (r"C:\Users\wardc\Desktop\微信照片_最新\图片", "微信图片HEVC", 2),
]
MY_ROOTS = tuple(b for _, b, _ in HEVC_ROOTS)
WORKERS = 8
FFPROBE = "ffprobe"
FFMPEG = "ffmpeg"


def db():
    c = sqlite3.connect(DB, timeout=60)
    c.execute("""create table if not exists photos(
        pid integer primary key autoincrement,
        path text, root text, rel text, name text, ext text, bytes integer,
        md5 text, dup_of integer,
        ts integer, date text, date_src text,
        session_key text, session_name text, session_type text,
        role text, sender text,
        width integer, height integer,
        category text, note text)""")
    for ix, col in [("ix_photos_date", "date"), ("ix_photos_md5", "md5"),
                    ("ix_photos_cat", "category"), ("ix_photos_root", "root")]:
        c.execute("create index if not exists %s on photos(%s)" % (ix, col))
    c.commit()
    return c


# ─────────────────────────────────── 消息索引（与 photo_index.py 同源）
def build_msg_index():
    con = sqlite3.connect("file:" + INDEX_DB.replace("\\", "/") + "?mode=ro", uri=True)
    name = {}
    for sk, dn, st in con.execute("select talker, display_name, session_type from sessions"):
        name[sk] = (dn or sk, st or "")
    idx = defaultdict(list)
    n = 0
    for ts, sk, role, content in con.execute(
            "select ts,session_key,role,content from messages where type='image'"):
        n += 1
        for pat in (r'md5="([0-9a-f]{32})"', r'originsourcemd5="([0-9a-f]{32})"'):
            for h in re.findall(pat, content or ""):
                idx[h].append((ts, sk, role))
    con.close()
    return idx, name, n


def md5file(p, cap=60 << 20):
    h = hashlib.md5()
    with io.open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
            if f.tell() > cap:
                break
    return h.hexdigest()


def probe(p):
    """ffprobe 取宽高（不解码）"""
    try:
        r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", p],
                           capture_output=True, text=True, timeout=25)
        s = (r.stdout or "").strip().split(",")
        if len(s) >= 2:
            return int(float(s[0] or 0)), int(float(s[1] or 0))
    except Exception:
        pass
    return 0, 0


def decode(path, md5, force=False):
    """懒解码 .hevc → jpg。返回 (jpg_path, is_blank) 或 (None, None)"""
    os.makedirs(CACHE, exist_ok=True)
    o = os.path.join(CACHE, (md5 or hashlib.md5(path.encode()).hexdigest()) + ".jpg")
    if force or not os.path.exists(o):
        r = subprocess.run([FFMPEG, "-y", "-v", "error", "-i", path,
                            "-frames:v", "1", "-q:v", "3", o], capture_output=True)
        if r.returncode != 0 or not os.path.exists(o):
            return None, None
    blank = None
    try:
        from PIL import Image, ImageStat
        Image.MAX_IMAGE_PIXELS = None
        with Image.open(o) as im:
            g = im.convert("L").resize((64, 64))
            st = ImageStat.Stat(g)
            blank = (st.stddev[0] < 3.0)          # 近乎纯色 → 空白/占位图
    except Exception:
        pass
    return o, blank


def guess_category(role, skey, sname, stype):
    if role == "me":
        return "① 我拍摄/记录（存给自己）" if skey == "filehelper" else "① 我拍摄/记录（我发出）"
    if role == "them":
        return "③ 别人发来（现场/成果，拍摄者待确认）"
    return "待确认"


def collect():
    out = []
    for root, bucket, prio in HEVC_ROOTS:
        if not os.path.isdir(root):
            print("  跳过（不存在）：%s" % root)
            continue
        for dp, ds, fs in os.walk(root):
            for fn in fs:
                if not fn.lower().endswith(".hevc"):
                    continue
                p = os.path.join(dp, fn)
                try:
                    st = os.stat(p)
                except Exception:
                    continue
                if st.st_size < 2048:
                    continue
                out.append((p, bucket, st.st_size, dp, fn))
    return out


def build(limit=None, date_filter=None):
    t0 = time.time()
    c = db()
    idx, names, nimg = build_msg_index()
    print("图片消息 %d 条 → md5 键 %d 个" % (nimg, len(idx)))

    files = collect()
    if date_filter:
        lo, hi = date_filter
        files = [f for f in files if any(lo <= m <= hi for m in re.findall(r"(20\d\d-\d\d)", f[3]))]
    print("待索引 .hevc %d 个（%.1f 分钟预估）" % (len(files), len(files) * 0.05 / 60))

    # 清掉自己那两个 root（幂等）
    c.execute("delete from photos where root in (%s)" % ",".join("?" * len(MY_ROOTS)), MY_ROOTS)
    c.commit()

    # 已有 md5（避免与 jpg 重复计入）
    existing = {}
    for pid, h in c.execute("select pid, md5 from photos where root not in (%s)" %
                            ",".join("?" * len(MY_ROOTS)), MY_ROOTS):
        existing.setdefault(h, pid)

    # ---- 并行 ffprobe
    dims = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        fut = {ex.submit(probe, f[0]): f[0] for f in files}
        done = 0
        for fu in as_completed(fut):
            dims[fut[fu]] = fu.result()
            done += 1
            if done % 500 == 0:
                print("    ffprobe %d/%d" % (done, len(files)))

    rows = []
    stat = Counter()
    for p, bucket, size, dp, fn in files:
        try:
            h = md5file(p)
        except Exception:
            stat["md5失败"] += 1
            continue
        w, hgt = dims.get(p, (0, 0))
        ts, date, src, skey, sname, stype, role, sender = 0, "", "", "", "", "", "", ""
        if h in idx:
            cand = sorted(idx[h])
            ts, skey, role = cand[0]
            date = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            src = "微信消息时间（内容MD5 匹配）"
            sname, stype = names.get(skey, (skey, ""))
            sender = "我" if role == "me" else skey
            stat["命中消息"] += 1
        else:
            m = re.search(r"(20\d\d)-(\d\d)", dp)
            if m:
                date = "%s-%s-01" % (m.group(1), m.group(2))
                src = "目录月份（微信按月导出）"
            else:
                date = datetime.datetime.fromtimestamp(os.stat(p).st_mtime).strftime("%Y-%m-%d")
                src = "文件修改时间（弱依据）"
            stat["未命中"] += 1
        dup = existing.get(h)
        cat = guess_category(role, skey, sname, stype)
        rows.append((p, bucket, os.path.relpath(p, os.path.dirname(p)), fn, ".hevc", size,
                     h, dup, ts, date, src, skey, sname, stype, role, sender, w, hgt, cat, ""))
        if limit and len(rows) >= limit:
            break

    c.executemany("""insert into photos
        (path,root,rel,name,ext,bytes,md5,dup_of,ts,date,date_src,session_key,session_name,
         session_type,role,sender,width,height,category,note)
        values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", rows)
    c.commit()
    return len(rows), dict(stat), time.time() - t0


def report(c):
    tot = c.execute("select count(*) from photos").fetchone()[0]
    print("=" * 78)
    print("照片索引现状（含 HEVC）")
    print("=" * 78)
    print("照片合计 %s 张" % "{:,}".format(tot))
    print("\n按 root：")
    for r in c.execute("select root,count(*) from photos group by 1 order by 2 desc"):
        print("  %-16s %7d" % (r[0], r[1]))
    print("\nHEVC 桶：拿到精确消息时间 / 可用（宽≥800）")
    for r in c.execute("""select root, count(*),
                            sum(case when date_src like '微信消息时间%' then 1 else 0 end),
                            sum(case when width>=800 then 1 else 0 end)
                          from photos where root like '%HEVC' group by 1"""):
        print("  %-16s n=%-6d 精确时间=%-5d 宽≥800=%d" % (r[0], r[1], r[2], r[3]))
    print("\nHEVC 按月：")
    for r in c.execute("""select substr(date,1,7) m,count(*) from photos
                          where root like '%HEVC' group by 1 order by 1"""):
        print("  %-9s %6d" % (r[0], r[1]))
    print("\nHEVC 里他本人发出的（role=me，TOP 会话）：")
    for r in c.execute("""select session_name,session_type,count(*) from photos
                          where root like '%HEVC' and role='me' group by 1,2 order by 3 desc limit 15"""):
        print("  %-30s %-6s %6d" % ((r[0] or "")[:30], r[1], r[2]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--date", nargs=2, default=None, metavar=("LO", "HI"))
    a = ap.parse_args()
    c = db()
    if a.build:
        n, stat, dt = build(a.limit, a.date)
        print("索引 %s 张 ｜ %.1f 秒 ｜ %s" % ("{:,}".format(n), dt, stat))
    report(c)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
