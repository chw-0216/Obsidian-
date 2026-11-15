# -*- coding: utf-8 -*-
r"""
photo_sources.py —— 把「非微信聊天」的照片来源补进照片索引

★★★ 背景（2026-10-06）
----------------------
`photo_index.py` 只覆盖了微信聊天导出目录 + 少量策展目录。但本机还有一大批**项目照片**：

  · **朋友圈 media（7,905 张 / 1.5 GB）** —— 配 `朋友圈导出_*.json`，
    可精确拿到 **发帖时间 + 昵称 + 文案**；`nickname=蔡浩文` 的即**他本人发的朋友圈**
  · 井邻项目（489 张 / 3.15 GB，含 575 周年原图 / 交互主视觉 / 悲鸿 / 制版）
  · 井邻宣传（123 张，工作站海报 / 丝网印刷工作坊宣传页 / 知行计划）
  · Capture One 原片（383 张 / 2.78 GB，他的摄影原片，含 34 张 .cr2）
  · WeFlow 图片（1,194 张）
  · 澜沧提交包 / 定稿图 / 图片素材 / RAW 优化版 / 知行计划 / 媒体导出

这些都是「我拍摄的」「我做的设计」的直接证据，但**完全没进过索引**。

产出：写进同一张 `photos` 表，`root` 用上表的名字；本脚本只 delete 自己负责的 root（幂等）。

★ 诚实边界
  · 朋友圈：`nickname=蔡浩文` → `role='me'`（他发的）；其他昵称 → `role='them'`
  · 其他目录：无语义 → `role=NULL`、`category='待确认'`，**拍摄者待确认**
  · 文件名不含时间的，退回「目录名里的日期」→ 再退回 mtime

用法
----
  python tools\photo_sources.py --build
  python tools\photo_sources.py --report
"""
import os, io, re, sys, csv, json, time, sqlite3, hashlib, datetime, argparse, traceback
from collections import Counter, defaultdict

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
BATCH = os.path.join(WS, "_tmp", "batch")
DB = os.path.join(BATCH, "batch.sqlite")

SNS_JSON = (r"C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理"
            r"\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出\朋友圈"
            r"\朋友圈导出_2026-07-23T20-36-32.json")
SNS_MEDIA = (r"C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理"
             r"\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出\朋友圈\media")

# (路径, root 名, 优先级) —— 本脚本负责的 root（与 photo_index / hevc_photos 不重叠）
SRC_ROOTS = [
    (SNS_MEDIA, "朋友圈", 1),
    (r"C:\Users\wardc\Desktop\05_井邻项目_视觉与丝网印刷", "井邻项目", 1),
    (r"C:\Users\wardc\Desktop\06_井邻项目_宣传申报与合作", "井邻宣传", 1),
    (r"C:\Users\wardc\Desktop\澜沧支教_提交包", "澜沧提交包", 1),
    (r"C:\Users\wardc\Desktop\_定稿图_1002晚", "定稿图", 1),
    (r"C:\Users\wardc\Desktop\08_图片素材", "图片素材", 1),
    (r"C:\Users\wardc\Desktop\新增RAW优化版", "RAW优化版", 1),
    (r"C:\Users\wardc\Desktop\知行计划最终材料", "知行最终材料", 1),
    (r"C:\Users\wardc\Desktop\知行计划最终版", "知行最终版", 1),
    (r"C:\Users\wardc\Desktop\_media_export", "媒体导出", 1),
    (r"C:\Users\wardc\Pictures\Capture One Catalog\Originals", "C1原片", 1),
    (r"C:\Users\wardc\Documents\WeFlow\Images", "WeFlow图片", 1),
]
MY_ROOTS = tuple(b for _, b, _ in SRC_ROOTS)
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".gif", ".webp", ".heic", ".hevc",
           ".cr2", ".cr3", ".arw", ".dng", ".nef", ".psd"}
SKIP_DIR = {"node_modules", ".git", "__pycache__", "site-packages", "预览图"}


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


def dims(p):
    try:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        with Image.open(p) as im:
            return im.size
    except Exception:
        return 0, 0


# ────────────────────────────────── 朋友圈
def load_sns():
    """localPath 文件名 → (ts, nickname, desc, nmedia, type)"""
    m = {}
    if not os.path.exists(SNS_JSON):
        return m
    with io.open(SNS_JSON, encoding="utf-8") as f:
        d = json.load(f)
    for p in d.get("posts", []):
        ts = p.get("createTime") or 0
        nick = p.get("nickname") or ""
        desc = (p.get("contentDesc") or "").replace("\n", " ")[:120]
        likes = len(p.get("likes") or [])
        cmts = len(p.get("comments") or [])
        for md in (p.get("media") or []):
            lp = md.get("localPath") or ""
            if lp:
                m[os.path.basename(lp)] = (ts, nick, desc, likes, cmts, p.get("type"))
    return m


def build():
    t0 = time.time()
    c = db()
    sns = load_sns()
    print("朋友圈 JSON：%d 条 media 映射" % len(sns))

    c.execute("delete from photos where root in (%s)" % ",".join("?" * len(MY_ROOTS)), MY_ROOTS)
    c.commit()
    existing = {}
    for pid, h in c.execute("select pid, md5 from photos where root not in (%s)" %
                            ",".join("?" * len(MY_ROOTS)), MY_ROOTS):
        existing.setdefault(h, pid)

    rows, stat = [], Counter()
    for root, bucket, prio in SRC_ROOTS:
        if not os.path.isdir(root):
            print("  跳过（不存在）：%s" % root)
            continue
        cnt = 0
        for dp, ds, fs in os.walk(root):
            ds[:] = [d for d in ds if d not in SKIP_DIR]
            for fn in fs:
                ext = os.path.splitext(fn)[1].lower()
                if ext not in IMG_EXT:
                    continue
                p = os.path.join(dp, fn)
                try:
                    st = os.stat(p)
                except Exception:
                    stat["stat失败"] += 1
                    continue
                if st.st_size < 4096:
                    continue
                try:
                    h = md5file(p)
                except Exception:
                    stat["md5失败"] += 1
                    continue
                ts, date, src = 0, "", ""
                skey = sname = stype = role = sender = note = ""
                cat = "待确认"
                if bucket == "朋友圈" and fn in sns:
                    ts, nick, desc, likes, cmts, ptype = sns[fn]
                    if ts:
                        date = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                        src = "朋友圈发帖时间（JSON createTime）"
                    role = "me" if nick == "蔡浩文" else "them"
                    sname = "朋友圈"
                    stype = "朋友圈"
                    skey = "sns"
                    sender = nick
                    cat = ("① 我拍摄/记录（我发的朋友圈）" if role == "me"
                           else "③ 别人发来（朋友圈，拍摄者待确认）")
                    note = ("%s｜赞%d 评%d" % (desc, likes, cmts)) if desc else ("赞%d 评%d" % (likes, cmts))
                    stat["朋友圈映射"] += 1
                if not date:
                    # ★ 必须带分隔符（`2026-04` / `2026_04` / `2026/04/15`），
                    #   否则账号哈希里的数字串会被误当日期（曾出现「2062-96-22」）
                    m = re.search(r"(20\d\d)[-_/](\d\d)(?:[-_/](\d\d))?(?!\d)", dp)
                    if m and m.group(3) and 1 <= int(m.group(2)) <= 12 and 1 <= int(m.group(3)) <= 31:
                        date = "%s-%s-%s" % (m.group(1), m.group(2), m.group(3)); src = "目录名日期"
                    elif m and 1 <= int(m.group(2)) <= 12:
                        date = "%s-%s-01" % (m.group(1), m.group(2)); src = "目录月份"
                    else:
                        date = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d")
                        src = "文件修改时间（弱依据）"
                w, hgt = dims(p)
                dup = existing.get(h)
                rows.append((p, bucket, os.path.relpath(p, root), fn, ext, st.st_size,
                             h, dup, ts, date, src, skey, sname, stype, role, sender,
                             w, hgt, cat, note))
                cnt += 1
        print("  %-12s %6d 张" % (bucket, cnt))

    c.executemany("""insert into photos
        (path,root,rel,name,ext,bytes,md5,dup_of,ts,date,date_src,session_key,session_name,
         session_type,role,sender,width,height,category,note)
        values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", rows)
    c.commit()
    return len(rows), dict(stat), time.time() - t0


def report(c):
    print("=" * 78)
    print("照片索引（新增来源）")
    print("=" * 78)
    for r in c.execute("select root,count(*),sum(case when width>=800 then 1 else 0 end) "
                       "from photos group by 1 order by 2 desc"):
        print("  %-16s %7d  宽≥800=%d" % (r[0], r[1], r[2] or 0))
    print("\n朋友圈：他本人发的（role=me）按月：")
    for r in c.execute("""select substr(date,1,7) m,count(*) from photos
                          where root='朋友圈' and role='me' group by 1 order by 1 desc limit 20"""):
        print("  %-9s %5d" % (r[0], r[1]))
    print("\n新增来源可用池（宽≥800 且 ≥80KB）：")
    for r in c.execute("""select root,count(*) from photos
                          where root in (%s) and width>=800 and bytes>=80000
                          group by 1 order by 2 desc""" % ",".join("?" * len(MY_ROOTS)), MY_ROOTS):
        print("  %-16s %5d" % (r[0], r[1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    c = db()
    if a.build:
        n, stat, dt = build()
        print("索引 %s 张 ｜ %.1f 秒 ｜ %s" % ("{:,}".format(n), dt, stat))
    report(c)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
