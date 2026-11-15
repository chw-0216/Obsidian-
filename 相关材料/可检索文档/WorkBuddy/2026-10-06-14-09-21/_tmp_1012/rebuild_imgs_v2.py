# -*- coding: utf-8 -*-
"""陈晔会话 654 张图片 · 重建（v2：索引缓存 + 进度输出 + 可续跑）

与 final_chenye_img_index.py 的匹配规则一致：
  A  文件名 stem == XML md5                      —— 确定
  同月  字节数精确相等（hd > mid > thumb 优先）
  跨月  字节数精确相等 + 长宽比校验（容差 2%）
差异：
  1. .dat 索引缓存到 _dat_index.json，第二次跑秒级启动
  2. 每 50 个会话目录打印一次进度
  3. 不做任何删除动作（临时文件写到系统 temp）
"""
import json, os, re, struct, datetime, collections, subprocess, csv, sys, time, shutil

ROOT = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\attach"
JSON_P = r"C:\Users\wardc\Desktop\导_聊天记录.json"
OUT = r"C:\Users\wardc\Desktop\07_聊天记录分析\陈晔会话图片_2026-10-14"
IMG_DIR = os.path.join(OUT, "02_图片")
CSV_P = os.path.join(OUT, "01_定位索引.csv")
CACHE = r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21\_tmp_1012\_dat_index.json"
FFMPEG = r"C:\Users\wardc\Documents\New project gpt\AI-archive\apps\FFmpeg\package\ffmpeg-n8.1-latest-win64-gpl-8.1\bin\ffmpeg.exe"
import tempfile
TMPD = tempfile.gettempdir()
AES_KEY = b"d24287c68e6e3244"; XOR_KEY = 0xE1
from Cryptodome.Cipher import AES
from Cryptodome.Util import Padding

def log(*a):
    print(*a); sys.stdout.flush()

def dec_size(p):
    try:
        with open(p, "rb") as f: h = f.read(15)
    except OSError: return None
    if len(h) < 14 or h[:6] != bytes.fromhex("070856320807"): return None
    _, a, x = struct.unpack_from("<6sLL", h); return a + x

def decode(d):
    _, a, x = struct.unpack_from("<6sLL", d)
    al = a + 16 - (a % 16); body = d[15:]
    if al > len(body): raise ValueError("size mismatch")
    p = AES.new(AES_KEY, AES.MODE_ECB).decrypt(body[:al])
    try: p = Padding.unpad(p, 16)
    except Exception: pass
    return p + body[al:len(body) - x] + bytes(b ^ XOR_KEY for b in body[-x:])

def kind_of(b):
    if b[:3] == b"\xff\xd8\xff": return "jpg"
    if b[:8] == b"\x89PNG\r\n\x1a\n": return "png"
    if b[:6] in (b"GIF87a", b"GIF89a"): return "gif"
    if b[:4] == b"wxgf": return "wxgf"
    return None

def jpeg_size(b):
    i = 2; n = len(b)
    while i < n - 9:
        if b[i] != 0xFF: i += 1; continue
        m = b[i+1]
        if m in (0xD8,0xD9) or 0xD0 <= m <= 0xD7: i += 2; continue
        seg = struct.unpack_from(">H", b, i+2)[0]
        if m in (0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF):
            h, w = struct.unpack_from(">HH", b, i+5); return w, h
        i += 2 + seg
    return None
def png_size(b): return struct.unpack_from(">II", b, 16) if len(b) >= 24 else None
def dims_of(b, k):
    if k == "jpg": return jpeg_size(b)
    if k == "png": return png_size(b)
    return None

# ---------- 1. .dat 索引（带缓存） ----------
t0 = time.time()
if os.path.exists(CACHE):
    log("[1] 读取 .dat 索引缓存 …")
    recs = json.load(open(CACHE, encoding="utf-8"))
    log("    缓存条目:", len(recs))
else:
    log("[1] 扫描全库 .dat …")
    recs = []
    convs = sorted(os.listdir(ROOT))
    log("    会话目录:", len(convs))
    for i, conv in enumerate(convs, 1):
        cd = os.path.join(ROOT, conv)
        if not os.path.isdir(cd): continue
        try:
            months = os.listdir(cd)
        except OSError:
            continue
        for ym in months:
            d = os.path.join(cd, ym, "Img")
            if not os.path.isdir(d): continue
            try:
                fs = os.listdir(d)
            except OSError:
                continue
            for f in fs:
                if not f.endswith(".dat"): continue
                p = os.path.join(d, f); ds = dec_size(p)
                if ds is None: continue
                recs.append({"path": p, "ym": ym, "name": f, "stem": f[:-4], "dec": ds, "conv": conv})
        if i % 50 == 0:
            log("    %d/%d 会话 · 已索引 %d 个 .dat · %.0fs" % (i, len(convs), len(recs), time.time() - t0))
    json.dump(recs, open(CACHE, "w", encoding="utf-8"))
    log("    索引完成:", len(recs), "→", CACHE, "(%.0fs)" % (time.time() - t0))

by_stem, by_dec = {}, collections.defaultdict(list)
for r in recs:
    by_stem.setdefault(r["stem"], r)
    by_dec[r["dec"]].append(r)

# ---------- 2. 图片消息 ----------
log("[2] 读取图片消息 …")
msgs = json.load(open(JSON_P, encoding="utf-8"))
imgs = []
for m in msgs:
    if str(m.get("localType")) != "3": continue
    ct = m.get("content") or ""
    gi = lambda k: (re.search(rf'\b{k}="(\d+)"', ct) or [None, None])[1]
    ts = int(m["createTime"]); dt = datetime.datetime.fromtimestamp(ts)
    imgs.append({"ts": ts, "dt": dt, "ym": dt.strftime("%Y-%m"),
                 "isSend": str(m.get("isSend")),
                 "md5": (re.search(r'\bmd5="([0-9a-f]+)"', ct) or [None, None])[1],
                 "length": gi("length"), "thumb": gi("cdnthumblength"), "hd": gi("hdlength"),
                 "tw": gi("cdnthumbwidth"), "th": gi("cdnthumbheight")})
imgs.sort(key=lambda x: x["ts"])
log("    图片消息:", len(imgs))

# ---------- 3. 匹配 ----------
def cl(key, pref, ym, any_ym=False):
    """pref: 'h' → 优先 _h.dat；'t' → 优先 _t.dat；'m' → 优先无后缀。不排除任何后缀。"""
    if not key or int(key) <= 0: return []
    cand = [r for r in by_dec.get(int(key), []) if any_ym or r["ym"] == ym]
    def rank(r):
        n = r["name"]
        if pref == "h":
            return 0 if n.endswith("_h.dat") else (1 if not n.endswith("_t.dat") else 2)
        if pref == "t":
            return 0 if n.endswith("_t.dat") else (1 if not n.endswith("_h.dat") else 2)
        return 0 if not n.endswith(("_t.dat", "_h.dat")) else (1 if n.endswith("_h.dat") else 2)
    cand.sort(key=rank)
    return cand

def aspect_ok(img, k, want):
    if not want: return True, "无期望"
    d = dims_of(img, k)
    if not d or not d[1]: return True, "无法判定"
    ra = d[0] / d[1]; rw = want[0] / want[1]
    return (abs(ra - rw) / rw < 0.02), ("长宽比✓" if abs(ra-rw)/rw < 0.02 else "长宽比✗")

def wxgf_to_jpg(img, dst):
    """wxgf 容器 → HEVC → ffmpeg 首帧。
    部分 wxgf 带一个 10 字节的假 VPS NAL，ffmpeg 会报
    「vps_base_layer_internal_flag ... not set」而拒绝解码；
    此时丢掉第一个 NAL 再解即可。返回 True 表示成功。"""
    mm = re.search(b"\x00\x00\x00\x01", img)
    if not mm: return False
    stream = img[mm.start():]
    # 切出 NAL 列表
    pos = [m.start() for m in re.finditer(b"\x00\x00\x00\x01", stream)]
    cands = [("整段", 0)]
    if len(pos) >= 2 and (pos[1] - pos[0]) < 16:          # 首个 NAL 异常短
        cands.append(("跳过首个NAL", pos[1]))
    for tag, off in cands:
        h = os.path.join(TMPD, "_t.h265")
        with open(h, "wb") as fh: fh.write(stream[off:])
        tmp_out = os.path.join(TMPD, "_t_frame.jpg")
        if os.path.exists(tmp_out):
            open(tmp_out, "wb").close()            # 覆盖清空，不做删除
        r = subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", h,
                            "-frames:v", "1", tmp_out], capture_output=True)
        if r.returncode == 0 and os.path.exists(tmp_out) and os.path.getsize(tmp_out) > 0:
            shutil.copyfile(tmp_out, dst)
            return True
    return False

stat = collections.Counter(); records = []
log("[3] 匹配 …")
for idx, m in enumerate(imgs, 1):
    tstr = m["dt"].strftime("%Y-%m-%d %H:%M:%S")
    who = "我" if m["isSend"] == "1" else "陈晔"
    prefix = f"{m['dt'].strftime('%Y%m%d_%H%M%S')}_{who}"
    mdir = os.path.join(IMG_DIR, m["ym"])
    have = [f for f in os.listdir(mdir) if f.startswith(prefix + "_")] if os.path.isdir(mdir) else []

    want = (int(m["tw"]), int(m["th"])) if m["tw"] and m["th"] else None
    hit = img = kind = note = lvl = None

    if m["md5"] and m["md5"] in by_stem:
        r = by_stem[m["md5"]]
        try:
            i2 = decode(open(r["path"], "rb").read()); k2 = kind_of(i2)
            if k2: hit, img, kind, note, lvl = r, i2, k2, "md5确定", "A-md5"
        except Exception: pass

    if not hit:
        for tag, key, pref in (("H", m["hd"], "h"), ("M", m["length"], "m"), ("T", m["thumb"], "t")):
            for r in cl(key, pref, m["ym"]):
                try:
                    i2 = decode(open(r["path"], "rb").read()); k2 = kind_of(i2)
                except Exception: continue
                if not k2: continue
                ok, nt = aspect_ok(i2, k2, want)
                hit, img, kind, note, lvl = r, i2, k2, "同月·" + nt, "同月-" + tag
                break
            if hit: break

    if not hit:
        for tag, key, pref in (("H", m["hd"], "h"), ("M", m["length"], "m"), ("T", m["thumb"], "t")):
            for r in cl(key, pref, m["ym"], True):
                try:
                    i2 = decode(open(r["path"], "rb").read()); k2 = kind_of(i2)
                except Exception: continue
                if not k2: continue
                ok, nt = aspect_ok(i2, k2, want)
                if not ok: continue
                hit, img, kind, note, lvl = r, i2, k2, "跨月·" + nt, "跨月-" + tag
                break
            if hit: break

    saved = ""
    if have:
        stat["复用"] += 1
        records.append({"时间": tstr, "发送方": who, "月份": m["ym"],
                        "清晰度档": (lvl.split("-")[-1] if lvl else "历史"),
                        "匹配层级": (lvl + "+复用") if lvl else "历史已存在",
                        "来源会话": hit["conv"] if hit else "",
                        "本地源文件": hit["path"] if hit else "",
                        "解密产物": os.path.join(mdir, sorted(have)[0]),
                        "校验": note if note else ("—" if not lvl else "")})
        if idx % 100 == 0:
            log("    %d/%d · 已归档 %d" % (idx, len(imgs), sum(1 for r in records if r["解密产物"])))
        continue

    if hit:
        try:
            if kind == "wxgf":
                dst = os.path.join(mdir, prefix + "_补.jpg"); os.makedirs(mdir, exist_ok=True)
                if wxgf_to_jpg(img, dst): saved = dst
            else:
                dst = os.path.join(mdir, prefix + "_补." + kind); os.makedirs(mdir, exist_ok=True)
                with open(dst, "wb") as fh: fh.write(img)
                saved = dst
        except Exception as e:
            log("      ! 写盘失败", tstr, e)
    stat[lvl or "MISS"] += 1
    records.append({"时间": tstr, "发送方": who, "月份": m["ym"],
                    "清晰度档": (lvl.split("-")[-1] if lvl else "MISS"),
                    "匹配层级": lvl or "", "来源会话": hit["conv"] if hit else "",
                    "本地源文件": hit["path"] if hit else "",
                    "解密产物": saved, "校验": note or ""})
    if idx % 100 == 0:
        log("    %d/%d · 已归档 %d" % (idx, len(imgs), sum(1 for r in records if r["解密产物"])))

log("")
log("匹配统计:", dict(stat))
log("已归档: %d / %d" % (sum(1 for r in records if r["解密产物"]), len(records)))
with open(CSV_P, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(records[0].keys())); w.writeheader(); w.writerows(records)
log("索引 -> %s (%d 行)" % (CSV_P, len(records)))
log("")
log("=== 仍 MISS（需手机点开后重跑）===")
for r in records:
    if not r["解密产物"]:
        log("  %s  %s  %s" % (r["时间"], r["发送方"], r["月份"]))
log("")
log("=== 跨月补回（已过长宽比校验）===")
for r in records:
    if r["匹配层级"].startswith("跨月"):
        log("  %s  %s  %s  %s" % (r["时间"], r["发送方"], r["匹配层级"], r["校验"]))
log("")
log("总耗时 %.0fs" % (time.time() - t0))
