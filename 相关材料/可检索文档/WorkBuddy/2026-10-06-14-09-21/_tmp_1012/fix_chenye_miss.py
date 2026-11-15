# -*- coding: utf-8 -*-
"""第二轮：把 CSV 里 MISS 的图片用「全放宽」规则补匹配 + 解密。"""
import json, os, re, struct, collections, subprocess, csv, datetime
from Cryptodome.Cipher import AES
from Cryptodome.Util import Padding

ATTACH = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\attach\f349341f7efaa6679217d8c436e64d91"
OUT = r"C:\Users\wardc\Desktop\中期汇报_2026-09\17_陈晔会话图片全量定位_2026-10-12"
IMG_DIR = os.path.join(OUT, "02_图片")
CSV_P = os.path.join(OUT, "01_定位索引.csv")
FFMPEG = r"C:\Users\wardc\Documents\New project gpt\AI-archive\apps\FFmpeg\package\ffmpeg-n8.1-latest-win64-gpl-8.1\bin\ffmpeg.exe"
AES_KEY, XOR_KEY = b"d24287c68e6e3244", 0xE1

def dec_size(p):
    try: h = open(p, "rb").read(15)
    except OSError: return None
    if len(h) < 14 or h[:6] != bytes.fromhex("070856320807"): return None
    _, a, x = struct.unpack_from("<6sLL", h); return a + x

def decode(d):
    _, a, x = struct.unpack_from("<6sLL", d)
    al = a + 16 - (a % 16); body = d[15:]
    p = AES.new(AES_KEY, AES.MODE_ECB).decrypt(body[:al])
    try: p = Padding.unpad(p, 16)
    except Exception: pass
    return p + body[al:len(body) - x] + bytes(b ^ XOR_KEY for b in body[-x:])

def classify(img):
    if img[:3] == b"\xff\xd8\xff": return "jpg"
    if img[:8] == b"\x89PNG\r\n\x1a\n": return "png"
    if img[:6] in (b"GIF87a", b"GIF89a"): return "gif"
    if img[:4] == b"wxgf": return "wxgf"
    return None

# 全盘索引
by_dec = collections.defaultdict(list)
by_stem = {}
for ym in os.listdir(ATTACH):
    d = os.path.join(ATTACH, ym, "Img")
    if not os.path.isdir(d): continue
    for f in os.listdir(d):
        if not f.endswith(".dat"): continue
        p = os.path.join(d, f)
        s = dec_size(p)
        rec = {"path": p, "ym": ym, "name": f}
        by_stem[f[:-4]] = rec
        if s: by_dec[s].append(rec)

rows = list(csv.DictReader(open(CSV_P, encoding="utf-8-sig")))
fields = list(rows[0].keys())
miss = [r for r in rows if not r["本地源文件"]]
print("待补:", len(miss))

seq = collections.Counter()
fixed = 0
for r in miss:
    szs = []
    if r["hd"] and int(r["hd"]) > 0: szs.append(("hd", int(r["hd"])))
    if r["length"]: szs.append(("mid", int(r["length"])))
    if r["thumb"]: szs.append(("thumb", int(r["thumb"])))
    best = None
    for lvl, s in szs:
        for cand in by_dec.get(s, []):
            best = cand; break
        if best: break
    if not best and r["md5"] and r["md5"] in by_stem:
        best = by_stem[r["md5"]]
    if not best:
        continue
    ym = r["月份"]
    try:
        img = decode(open(best["path"], "rb").read())
        kind = classify(img)
        saved = ""
        seq[ym] += 1
        base = datetime.datetime.strptime(r["时间"], "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d_%H%M%S")
        if kind == "wxgf":
            mm = re.search(b"\x00\x00\x00\x01", img)
            if mm:
                h = os.path.join(IMG_DIR, "_t.h265"); open(h, "wb").write(img[mm.start():])
                dstp = os.path.join(IMG_DIR, ym, f"{base}_{r['发送方']}_补{seq[ym]:03d}.png")
                os.makedirs(os.path.dirname(dstp), exist_ok=True)
                subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", h, "-frames:v", "1", dstp], capture_output=True)
                if os.path.exists(dstp) and os.path.getsize(dstp) > 0: saved = dstp
                os.remove(h)
        elif kind:
            dstp = os.path.join(IMG_DIR, ym, f"{base}_{r['发送方']}_补{seq[ym]:03d}.{kind}")
            os.makedirs(os.path.dirname(dstp), exist_ok=True)
            open(dstp, "wb").write(img); saved = dstp
        if saved:
            r["本地源文件"] = best["path"]; r["解密产物"] = saved
            r["清晰度档"] = "补-" + best["name"].rsplit(".", 1)[0][-1]
            fixed += 1
    except Exception:
        pass

with open(CSV_P, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
print("补回:", fixed, "| 仍缺:", sum(1 for r in rows if not r["本地源文件"]))
