# -*- coding: utf-8 -*-
r"""
photo_index.py —— 照片索引：给每张照片定位「时间 + 会话 + 谁发的」

★★★ 核心发现（2026-10-06）
---------------------------
微信**把 EXIF 全剥了**（60 张抽样只有 2 张有拍摄时间）→ EXIF 路线不可用。
但照片文件名是 MD5，而 **照片文件的「内容 MD5」能对上聊天库里图片消息的 `md5` / `originsourcemd5` 属性**
（实测命中率 **128/150 ≈ 85%**）。

对上之后就能拿到：
  · **精确发送时间**（ts，秒级）
  · **会话**（session_key → 会话名 / 私聊或群聊）
  · **谁发的**（`role=me` = **他本人发的** ← 这是「我做了什么」的直接证据）

三类判定（对应任务书第一部分）
------------------------------
  ① 我拍摄/记录     role=me 且是图片消息 → 他主动发出
  ② 记录我工作过程   role=me 且在项目/工作会话 → 需结合会话性质
  ③ 项目现场/成果   role=them（别人发来）→ 可能是别人拍的现场

★ 拍摄者暂不明确的**保留待确认**，不硬判。

用法
----
  python tools\photo_index.py --build     # 建索引（首次约 1-2 分钟）
  python tools\photo_index.py --report
"""
import os, io, re, sys, csv, json, time, sqlite3, hashlib, datetime, argparse, traceback
from collections import Counter, defaultdict

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
BATCH = os.path.join(WS, "_tmp", "batch")
DB = os.path.join(BATCH, "batch.sqlite")
INDEX_DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"

# 照片根目录：(路径, 桶名, 优先级；数字小=优先取原图)
PHOTO_ROOTS = [
    (r"C:\Users\wardc\Desktop\微信照片_最新\原图_HD", "微信原图HD", 1),
    (r"C:\Users\wardc\Desktop\微信照片_最新\图片", "微信图片", 2),
    (r"C:\Users\wardc\Desktop\微信照片_最新\缩略图", "微信缩略图", 3),
    (r"C:\Users\wardc\Desktop\中期汇报_2026-09\07_照片素材", "汇报照片素材", 1),
    (r"C:\Users\wardc\Desktop\中期汇报_2026-09\09_PPT用图", "PPT用图", 1),
    (r"C:\Users\wardc\Desktop\澜沧支教_课堂照片_评审优化版_20260903", "澜沧课堂照", 1),
    (r"C:\Users\wardc\Documents\New project gpt\AI-archive\outputs", "AI产物", 2),
]
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".gif", ".webp"}
SKIP_DIR = {"_联系表", "预览图", "node_modules", ".git", "__pycache__"}


def db():
    c = sqlite3.connect(DB)
    c.execute("""create table if not exists photos(
        pid integer primary key autoincrement,
        path text, root text, rel text, name text, ext text, bytes integer,
        md5 text, dup_of integer,
        ts integer, date text, date_src text,
        session_key text, session_name text, session_type text,
        role text, sender text,
        width integer, height integer,
        category text, note text)""")
    c.execute("create index if not exists ix_photos_date on photos(date)")
    c.execute("create index if not exists ix_photos_md5  on photos(md5)")
    c.execute("create index if not exists ix_photos_cat  on photos(category)")
    c.commit()
    return c


def build_msg_index():
    """照片内容 MD5 → [(ts, session_key, role)]；同时取会话名映射"""
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


def md5file(p, cap=40 << 20):
    h = hashlib.md5()
    with io.open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
            if cap and h.digest_size and f.tell() > cap:
                break
    return h.hexdigest()


def guess_category(role, skey, sname, stype):
    """① 我拍摄/记录  ② 记录我工作过程  ③ 项目现场/成果  待确认"""
    if role == "me":
        if skey == "filehelper":
            return "① 我拍摄/记录（存给自己）"
        return "① 我拍摄/记录（我发出）"
    if role == "them":
        return "③ 别人发来（现场/成果，拍摄者待确认）"
    return "待确认"


def build(limit=None):
    t0 = time.time()
    c = db()
    idx, names, nimg = build_msg_index()
    print("图片消息 %d 条 → md5 索引 %d 个" % (nimg, len(idx)))

    c.execute("delete from photos")
    c.commit()

    seen = {}          # md5 -> pid（去重）
    rows = []
    stat = Counter()
    for root, bucket, prio in PHOTO_ROOTS:
        if not os.path.isdir(root):
            print("  跳过（不存在）：%s" % root)
            continue
        cnt = 0
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIR]
            for fn in files:
                ext = os.path.splitext(fn)[1].lower()
                if ext not in IMG_EXT:
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    st = os.stat(p)
                except Exception:
                    stat["stat失败"] += 1
                    continue
                if st.st_size < 1024:            # 太小的当图标跳过
                    stat["过小跳过"] += 1
                    continue
                try:
                    h = md5file(p)
                except Exception:
                    stat["md5失败"] += 1
                    continue
                # 时间 / 会话 / 谁发的
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
                    # 退回：目录月份（微信照片按月组织）
                    m = re.search(r"(20\d\d)-(\d\d)", dirpath)
                    if m:
                        date = "%s-%s-01" % (m.group(1), m.group(2))
                        src = "目录月份（微信按月导出）"
                    else:
                        date = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d")
                        src = "文件修改时间（弱依据）"
                    stat["未命中"] += 1

                w = hgt = 0
                try:
                    from PIL import Image
                    with Image.open(p) as im:
                        w, hgt = im.size
                except Exception:
                    pass

                dup = seen.get(h)
                if dup is None:
                    seen[h] = len(rows) + 1
                cat = guess_category(role, skey, sname, stype)
                rows.append((p, bucket, os.path.relpath(p, root), fn, ext, st.st_size,
                             h, dup, ts, date, src, skey, sname, stype, role, sender,
                             w, hgt, cat, ""))
                cnt += 1
                if limit and len(rows) >= limit:
                    break
            if limit and len(rows) >= limit:
                break
        print("  %-12s %6d 张" % (bucket, cnt))
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
    dup = c.execute("select count(*) from photos where dup_of is not null").fetchone()[0]
    hit = c.execute("select count(*) from photos where date_src like '微信消息时间%'").fetchone()[0]
    print("=" * 78)
    print("照片索引现状")
    print("=" * 78)
    print("照片 %s 张 ｜ 重复副本 %s ｜ 拿到精确消息时间 %s（%.1f%%）"
          % ("{:,}".format(tot), "{:,}".format(dup), "{:,}".format(hit), 100 * hit / max(tot, 1)))
    print("\n按分类（任务书三类）：")
    for r in c.execute("select category,count(*) from photos group by 1 order by 2 desc"):
        print("  %-34s %7d" % (r[0], r[1]))
    print("\n按日期来源：")
    for r in c.execute("select date_src,count(*) from photos group by 1 order by 2 desc"):
        print("  %-34s %7d" % (r[0], r[1]))
    print("\n按月（有精确时间的）：")
    for r in c.execute("""select substr(date,1,7) m,count(*) from photos
                          where date_src like '微信消息时间%' group by 1 order by 1 desc limit 14"""):
        print("  %-10s %6d" % (r[0], r[1]))
    print("\nTOP 会话（他发出的照片，按会话）：")
    for r in c.execute("""select session_name,session_type,count(*) from photos
                          where role='me' and dup_of is null group by 1,2 order by 3 desc limit 12"""):
        print("  %-30s %-6s %6d" % ((r[0] or "")[:30], r[1], r[2]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    c = db()
    if a.build or not a.report:
        n, stat, dt = build(a.limit)
        print("索引 %s 张 ｜ %.1f 秒 ｜ %s" % ("{:,}".format(n), dt, stat))
    report(c)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
