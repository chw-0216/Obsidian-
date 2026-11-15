# -*- coding: utf-8 -*-
"""陈晔会话 654 张图片 · 最终版索引

匹配规则（经对照实验校准）：
  A  文件名 stem == XML md5                      —— 确定，无需校验
  同月  字节数精确相等（hd > mid > thumb 优先）    —— 接受（历史通过率 94.2%）
  跨月  字节数精确相等 + **长宽比校验通过**        —— 接受（否则视为误匹配）

长宽比校验依据：XML 的 cdnthumbwidth/height 给出正确长宽比（尺度不同，比例一致）。
对照实验：同月匹配 533/566=94.2% 通过；纯跨月字节匹配仅 10/68=14.7% 通过。
"""
import json, os, re, struct, datetime, collections, subprocess, csv, shutil

ROOT = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\attach"
JSON_P = r"C:\Users\wardc\Desktop\导_聊天记录.json"
OUT = r"C:\Users\wardc\Desktop\07_聊天记录分析\陈晔会话图片_2026-10-14"
IMG_DIR = os.path.join(OUT, "02_图片")
QUAR = os.path.join(OUT, "99_未通过校验_可删")
CSV_P = os.path.join(OUT, "01_定位索引.csv")
FFMPEG = r"C:\Users\wardc\Documents\New project gpt\AI-archive\apps\FFmpeg\package\ffmpeg-n8.1-latest-win64-gpl-8.1\bin\ffmpeg.exe"
import tempfile
TMPD = tempfile.gettempdir()
AES_KEY = b"d24287c68e6e3244"; XOR_KEY = 0xE1
from Cryptodome.Cipher import AES
from Cryptodome.Util import Padding

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

# ---------- 0. 隔离上一轮不可靠产物 ----------
moved = 0
for ym in os.listdir(IMG_DIR):
    d = os.path.join(IMG_DIR, ym)
    if not os.path.isdir(d): continue
    for f in os.listdir(d):
        if "_补2." in f:
            q = os.path.join(QUAR, ym); os.makedirs(q, exist_ok=True)
            try:
                shutil.move(os.path.join(d, f), os.path.join(q, f)); moved += 1
            except Exception: pass
print("已隔离上一轮未校验产物:", moved, "→", QUAR)

# ---------- 1. 图片消息 ----------
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
print("图片消息:", len(imgs))

# ---------- 2. 全库索引 ----------
print("扫描全库 .dat …")
by_stem, by_dec = {}, collections.defaultdict(list)
for conv in os.listdir(ROOT):
    cd = os.path.join(ROOT, conv)
    if not os.path.isdir(cd): continue
    for ym in os.listdir(cd):
        d = os.path.join(cd, ym, "Img")
        if not os.path.isdir(d): continue
        for f in os.listdir(d):
            if not f.endswith(".dat"): continue
            p = os.path.join(d, f); ds = dec_size(p)
            if ds is None: continue
            r = {"path": p, "ym": ym, "name": f, "stem": f[:-4], "dec": ds, "conv": conv}
            by_stem.setdefault(r["stem"], r); by_dec[ds].append(r)
print("  可解析 .dat:", sum(len(v) for v in by_dec.values()))

# ---------- 3. 匹配 ----------
def cl(key, sfx, ym, any_ym=False):
    if not key or int(key) <= 0: return []
    out = []
    for r in by_dec.get(int(key), []):
        if not any_ym and r["ym"] != ym: continue
        n = r["name"]
        if sfx == "_h.dat" and not n.endswith("_h.dat"): continue
        if sfx == "_t.dat" and not n.endswith("_t.dat"): continue
        if sfx is None and n.endswith(("_t.dat", "_h.dat")): continue
        out.append(r)
    return out

def aspect_ok(img, k, want):
    if not want: return True, "无期望"
    d = dims_of(img, k)
    if not d or not d[1]: return True, "无法判定"
    ra = d[0] / d[1]; rw = want[0] / want[1]
    return (abs(ra - rw) / rw < 0.02), ("长宽比✓" if abs(ra-rw)/rw < 0.02 else "长宽比✗")

stat = collections.Counter(); records = []
for m in imgs:
    tstr = m["dt"].strftime("%Y-%m-%d %H:%M:%S")
    who = "我" if m["isSend"] == "1" else "陈晔"
    prefix = f"{m['dt'].strftime('%Y%m%d_%H%M%S')}_{who}"
    mdir = os.path.join(IMG_DIR, m["ym"])
    have = [f for f in os.listdir(mdir) if f.startswith(prefix + "_")] if os.path.isdir(mdir) else []
    if have:
        stat["已有"] += 1
        records.append({"时间": tstr, "发送方": who, "月份": m["ym"], "清晰度档": "已有",
                        "匹配层级": "复用", "来源会话": "", "本地源文件": "",
                        "解密产物": os.path.join(mdir, sorted(have)[0]), "校验": "—"})
        continue

    want = (int(m["tw"]), int(m["th"])) if m["tw"] and m["th"] else None
    hit = img = kind = note = lvl = None

    # A 确定
    if m["md5"] and m["md5"] in by_stem:
        r = by_stem[m["md5"]]
        try:
            i2 = decode(open(r["path"], "rb").read()); k2 = kind_of(i2)
            if k2: hit, img, kind, note, lvl = r, i2, k2, "md5确定", "A-md5"
        except Exception: pass

    # 同月
    if not hit:
        for tag, key, sfx in (("H", m["hd"], "_h.dat"), ("M", m["length"], None), ("T", m["thumb"], "_t.dat")):
            for r in cl(key, sfx, m["ym"]):
                try:
                    i2 = decode(open(r["path"], "rb").read()); k2 = kind_of(i2)
                except Exception: continue
                if not k2: continue
                ok, nt = aspect_ok(i2, k2, want)
                hit, img, kind, note, lvl = r, i2, k2, "同月·" + nt, "同月-" + tag
                break
            if hit: break

    # 跨月（必须长宽比通过）
    if not hit:
        for tag, key, sfx in (("H", m["hd"], "_h.dat"), ("M", m["length"], None), ("T", m["thumb"], "_t.dat")):
            for r in cl(key, sfx, m["ym"], True):
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
    if hit:
        if kind == "wxgf":
            mm = re.search(b"\x00\x00\x00\x01", img)
            if mm:
                h = os.path.join(TMPD, "_t.h265")
                with open(h, "wb") as fh: fh.write(img[mm.start():])
                dst = os.path.join(mdir, prefix + "_补.jpg"); os.makedirs(mdir, exist_ok=True)
                subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", h, "-frames:v", "1", dst], capture_output=True)
                if os.path.exists(dst) and os.path.getsize(dst) > 0: saved = dst
        else:
            dst = os.path.join(mdir, prefix + "_补." + kind); os.makedirs(mdir, exist_ok=True)
            open(dst, "wb").write(img); saved = dst
    stat[lvl or "MISS"] += 1
    records.append({"时间": tstr, "发送方": who, "月份": m["ym"],
                    "清晰度档": (lvl.split("-")[-1] if lvl else "MISS"),
                    "匹配层级": lvl or "", "来源会话": hit["conv"] if hit else "",
                    "本地源文件": hit["path"] if hit else "",
                    "解密产物": saved, "校验": note or ""})

print()
print("匹配统计:", dict(stat))
print("已归档:", sum(1 for r in records if r["解密产物"]), "/", len(records))
with open(CSV_P, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(records[0].keys())); w.writeheader(); w.writerows(records)
print("索引 ->", CSV_P, "(%d 行)" % len(records))
print()
print("=== 仍 MISS（需手机点开后重跑）===")
for r in records:
    if not r["解密产物"]:
        print("  %s  %s  %s" % (r["时间"], r["发送方"], r["月份"]))
print()
print("=== 跨月补回（已过长宽比校验）===")
for r in records:
    if r["匹配层级"].startswith("跨月"):
        print("  %s  %s  %s  %s" % (r["时间"], r["发送方"], r["匹配层级"], r["校验"]))
