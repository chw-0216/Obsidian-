# -*- coding: utf-8 -*-
r"""
phone_photos.py —— 手机照片「搜集」（★ 挑能用的，不是把手机全拷出来）

与「全量拉取」的区别：
  · 全量拉取 = `adb pull /sdcard/DCIM/Camera` → 3,323 张、约 8 GB，大半用不上
  · 本脚本   = 先查 MediaStore 元数据 → **按可用性规则筛** → 只 pull 选中的那些

可用性规则（默认，都可用参数改）
  ① 相册（bucket_display_name）命中 --buckets（默认 Camera）
  ② 单张 ≥ --min-mb（默认 0.8 MB）—— 太小的是缩略图/表情/缓存
  ③ 拍摄时间 ≥ --since（默认 2025-09-01，即「考上央美之后」）
  ④ 去重：(_size, _display_name) 相同只留一条
  ⑤ 排除：Screenshots / 缓存目录 / .recycle / 微信转发（如需要请显式加进 --buckets）

两种运行模式
  --index <media_images2.txt>   ★ 离线预演（不需要设备）——用手上已有的索引出清单
  （不加 --index）              走设备：adb content query 现场查

用法
  # 离线预演：看看会挑出哪些
  python tools\phone_photos.py --index "...\media_images2.txt" --dry
  # 真取回（需手机 USB 调试可用、HonorSuite 已退出）
  python tools\phone_photos.py --pull --out "C:\Users\wardc\Desktop\手机相机原片_2026-10-06"
"""
import os, re, io, sys, csv, json, argparse, datetime, subprocess
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import adb_run  # 固定 TEMP + 清代理 + 自动找 adb

DEFAULT_INDEX = (r"C:\Users\wardc\Documents\New project gpt\AI-archive\outputs"
                 r"\手机全文件解析_2026-09-29\01_结构化数据\media_images2.txt")


# ---------------------------------------------------------------- 解析
def parse_rows(txt):
    r"""content query 输出 → [{k:v}]（技能坑 4：`Row: \d+ ` 记录级切分）"""
    out = []
    for m in re.finditer(r"(?:^|\n)Row: \d+ (.*?)(?=\nRow: \d+ |\Z)", txt, re.S):
        body = m.group(1)
        d = {}
        for k, v in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)=([^,]*)", body):
            d[k] = v.strip()
        out.append(d)
    return out


def parse_ls(txt, remote_dir="/sdcard/DCIM/Camera"):
    r"""把 `ls -l` 输出解析成与 MediaStore 同形的记录。

    ★ 为什么要这条路：MediaStore 里会残留「文件已不在原路径」的陈旧记录
      （实测 IMG_20250901_224156.jpg 在库里但 pull 报 no such file），
      所以**取文件必须以文件系统实况为准**。日期优先从文件名 `IMG_YYYYMMDD_HHMMSS` 取，
      取不到才退回 mtime。
    """
    out = []
    pat = re.compile(r"^[-dl][rwxstST-]{9}[.+@]?\s+\d+\s+\S+\s+\S+\s+(\d+)\s+"
                     r"(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})\s+(.+?)\s*$")
    for line in txt.splitlines():
        m = pat.match(line)
        if not m:
            continue
        size, y, mo, d, hh, mm, name = m.groups()
        name = name.strip()
        # ★ 只收图片；`ls` 里混着 .mp4 视频（单个可达 3.7 GB）和 .tmp 半成品
        ext = os.path.splitext(name)[1].lower()
        if ext not in (".jpg", ".jpeg", ".png", ".heic", ".dng", ".webp"):
            continue
        if name.endswith(".tmp") or ".tmp." in name:
            continue
        # ★ 只有相机直出（IMG_*.jpg）算 Camera；其余归 Other，默认被 --buckets Camera 滤掉
        bucket = "Camera" if (name.startswith("IMG_") and ext in (".jpg", ".jpeg")) else "Other"
        fm = re.match(r"IMG_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})", name)
        try:
            if fm:
                yy, mmo, dd, H, M, S = fm.groups()
                dt = datetime.datetime(int(yy), int(mmo), int(dd), int(H), int(M), int(S))
            else:
                dt = datetime.datetime(int(y), int(mo), int(d), int(hh), int(mm))
        except Exception:
            continue
        out.append(dict(_id="", _data=remote_dir + "/" + name, _display_name=name,
                        _size=size, datetaken=str(int(dt.timestamp() * 1000)),
                        width="", height="", bucket_display_name=bucket, mime_type=""))
    return out


def num(s, default=0):
    try:
        return int(float(s))
    except Exception:
        return default


def ts_of(r):
    t = num(r.get("datetaken"))
    return t / 1000.0 if t > 1e11 else float(t)


def query_device(projection):
    if not adb_run.ensure_device():
        print("!! 没有可用设备 —— 多半是 HonorSuite 占着 USB（坑 24）")
        return ""
    args = ["exec-out", "content", "query",
            "--user", "0",                          # ★ 少了这个在荣耀上返回 0 行
            "--uri", "content://media/external/images/media",
            "--projection", projection]
    txt = adb_run.run_retry(args, timeout=900)
    if "Row: 0" not in txt:
        print("!! content query 可能失败，前 400 字：", txt[:400])
    return txt


PROJ = ("_id:_data:_display_name:_size:datetaken:width:height:"
        "bucket_display_name:mime_type:relative_path")


# ---------------------------------------------------------------- 筛选
def select(rows, buckets, since, min_mb, until=None):
    keep, drop = [], Counter()
    seen = set()
    for r in rows:
        b = (r.get("bucket_display_name") or "").strip()
        size = num(r.get("_size"))
        dp = r.get("_data") or ""
        t = ts_of(r)
        if buckets and b not in buckets:
            drop["相册不在范围"] += 1; continue
        if size < min_mb * 1048576:
            drop["文件过小"] += 1; continue
        if t and t < since:
            drop["早于起始日期"] += 1; continue
        if until and t > until:
            drop["晚于截止日期"] += 1; continue
        if not t:
            drop["无拍摄时间"] += 1; continue
        if any(x in dp for x in (".recycle", "collectcenter", "/cache/", "Thumbs")):
            drop["缓存/回收站"] += 1; continue
        k = (size, r.get("_display_name") or os.path.basename(dp))
        if k in seen:
            drop["重复"] += 1; continue
        seen.add(k)
        keep.append(dict(_id=r.get("_id"), path=dp, name=os.path.basename(dp),
                         size=size, ts=t, w=num(r.get("width")), h=num(r.get("height")),
                         bucket=b, mime=r.get("mime_type") or ""))
    keep.sort(key=lambda x: x["ts"])
    return keep, drop


def summarize(items):
    by_month = Counter(datetime.datetime.fromtimestamp(x["ts"]).strftime("%Y-%m") for x in items)
    total_mb = sum(x["size"] for x in items) / 1048576
    print("\n选中 %d 张 / %.1f MB" % (len(items), total_mb))
    print("逐月分布：")
    for k in sorted(by_month):
        print("   %s  %4d 张" % (k, by_month[k]))
    return by_month, total_mb


# ---------------------------------------------------------------- 取回
def pull_tar(items, outdir):
    r"""★ 设备端先 tar 成一个包，再一次性 pull 回来，本地解包。

    为什么不用逐个 `adb pull`：2,500 个文件 = 2,500 次进程启动 + 2,500 次会话建立，
    既慢（20 分钟起）又极易在中间被 HonorSuite 挤掉（坑 24）。
    打包法只有 4 次 adb 调用。
    """
    import tarfile, shutil
    names = [os.path.basename(x["path"]) for x in items]
    os.makedirs(outdir, exist_ok=True)
    lst = os.path.join(outdir, "_sel_list.txt")
    io.open(lst, "w", encoding="utf-8", newline="\n").write("\n".join(names) + "\n")
    dev_lst, dev_tar = "/sdcard/_phone_sel.txt", "/sdcard/_phone_sel.tar"
    remote_dir = os.path.dirname(items[0]["path"])

    print("  ① 推送文件清单（%d 行）..." % len(names), flush=True)
    adb_run.run_retry(["push", lst, dev_lst], timeout=300)

    print("  ② 设备端打包（%.1f GB，可能要几分钟）..." % (sum(x["size"] for x in items) / 1073741824), flush=True)
    r = adb_run.run_retry(["shell", "cd %s && tar -cf %s -T %s && echo TAR_OK" % (remote_dir, dev_tar, dev_lst)],
                          timeout=3600)
    if "TAR_OK" not in r:
        print("     打包可能失败：", r.strip()[:300])
        return 0, [("<tar>", r.strip()[:200])]

    local_tar = os.path.join(outdir, "_phone_sel.tar")
    print("  ③ 取回打包文件...", flush=True)
    adb_run.run_retry(["pull", dev_tar, local_tar], timeout=7200)
    if not os.path.exists(local_tar):
        return 0, [("<pull tar>", "本地未出现 tar 文件")]

    print("  ④ 本地解包并改名...", flush=True)
    ts_map = {os.path.basename(x["path"]): x["ts"] for x in items}
    done, fail = 0, []
    with tarfile.open(local_tar) as tf:
        for m in tf:
            if not m.isfile():
                continue
            base = os.path.basename(m.name)
            ts = ts_map.get(base)
            stamp = datetime.datetime.fromtimestamp(ts).strftime("%Y%m%d_%H%M%S") if ts else ""
            dst = os.path.join(outdir, ("%s_%s" % (stamp, base)) if stamp else base)
            try:
                f = tf.extractfile(m)
                with open(dst, "wb") as out:
                    shutil.copyfileobj(f, out)
                done += 1
            except Exception as e:
                fail.append((base, str(e)[:120]))
    try:
        os.remove(local_tar)
        adb_run.run_retry(["shell", "rm -f %s %s" % (dev_tar, dev_lst)], timeout=120)
    except Exception:
        pass
    print("  解包完成：%d 个，失败 %d" % (done, len(fail)), flush=True)
    return done, fail


def pull(items, outdir):
    os.makedirs(outdir, exist_ok=True)
    done, fail = 0, []
    for i, it in enumerate(items, 1):
        # 目标名：拍摄时间 + 原文件名，便于按时间排序
        stamp = datetime.datetime.fromtimestamp(it["ts"]).strftime("%Y%m%d_%H%M%S")
        name = "%s_%s" % (stamp, it["name"])
        dst = os.path.join(outdir, name)
        if os.path.exists(dst) and os.path.getsize(dst) > 0:
            done += 1; continue
        r = adb_run.run_retry(["pull", it["path"], dst], timeout=600)
        ok = os.path.exists(dst) and os.path.getsize(dst) > 0
        if ok:
            done += 1
        else:
            fail.append((it["path"], r.strip()[:120]))
            adb_run.ensure_device()      # 掉线就重新抢
        if i % 25 == 0 or i == len(items):
            print("   %d/%d  已取回 %d  失败 %d" % (i, len(items), done, len(fail)), flush=True)
    if fail:
        log = os.path.join(outdir, "_pull_failed.txt")
        io.open(log, "w", encoding="utf-8").write(
            "\n".join("%s\t%s" % (a, b) for a, b in fail))
        print("   失败清单 →", log)
    return done, fail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default=None, help="离线索引文件（media_images2.txt）")
    ap.add_argument("--lsfile", default=None,
                    help="★ 用 `ls -l` 实况清单（推荐，MediaStore 有陈旧记录）")
    ap.add_argument("--remote-dir", default="/sdcard/DCIM/Camera")
    ap.add_argument("--dry", action="store_true", help="只出清单，不取回")
    ap.add_argument("--pull", action="store_true", help="真正取回")
    ap.add_argument("--perfile", action="store_true",
                    help="逐个 adb pull（慢、易被挤掉）；默认用设备端打包法")
    ap.add_argument("--out", default=os.path.join(r"C:\Users\wardc\Desktop",
                                                  "手机相机原片_" + datetime.date.today().strftime("%Y-%m-%d")))
    ap.add_argument("--buckets", nargs="*", default=["Camera"])
    ap.add_argument("--since", default="2025-09-01")
    ap.add_argument("--until", default=None)
    ap.add_argument("--min-mb", type=float, default=0.8)
    ap.add_argument("--list-out", default=None)
    a = ap.parse_args()

    since = datetime.datetime.strptime(a.since, "%Y-%m-%d").timestamp()
    until = datetime.datetime.strptime(a.until, "%Y-%m-%d").timestamp() if a.until else None

    if a.lsfile:
        print("模式：文件系统实况（%s）" % os.path.basename(a.lsfile))
        rows = parse_ls(io.open(a.lsfile, encoding="utf-8", errors="replace").read(),
                        a.remote_dir)
    elif a.index:
        print("模式：离线预演（索引 %s）" % os.path.basename(a.index))
        rows = parse_rows(io.open(a.index, encoding="utf-8", errors="replace").read())
    else:
        print("模式：现场查询设备（MediaStore）")
        rows = parse_rows(query_device(PROJ))
    print("索引记录 %d 条" % len(rows))

    items, drop = select(rows, set(a.buckets), since, a.min_mb, until)
    print("剔除明细：", dict(drop))
    by_month, total_mb = summarize(items)

    listp = a.list_out or os.path.join(WS, "手机可用照片清单_%s.csv"
                                       % datetime.date.today().strftime("%Y-%m-%d"))
    with io.open(listp, "w", encoding="utf-8-sig", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["_id", "name", "ts", "date", "size", "w", "h", "bucket", "path"])
        wr.writeheader()
        for it in items:
            wr.writerow(dict(_id=it["_id"], name=it["name"], ts=it["ts"],
                             date=datetime.datetime.fromtimestamp(it["ts"]).strftime("%Y-%m-%d %H:%M"),
                             size=it["size"], w=it["w"], h=it["h"], bucket=it["bucket"], path=it["path"]))
    print("→ 清单 %s（%d 行）" % (listp, len(items)))

    if a.dry or not a.pull:
        print("\n（预演结束。确认清单无误后加 --pull 真正取回）")
        return

    print("\n开始取回 → %s" % a.out, flush=True)
    if a.perfile:
        done, fail = pull(items, a.out)
    else:
        done, fail = pull_tar(items, a.out)
    print("\n完成：成功 %d / 失败 %d / 合计 %.1f MB"
          % (done, len(fail), total_mb))


if __name__ == "__main__":
    main()
