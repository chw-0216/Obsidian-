# -*- coding: utf-8 -*-
"""陈晔会话 654 张图片：全量定位 + 解密 + 归档。
三档文件：_h.dat(高清) > .dat(中图, wxgf) > _t.dat(缩略图, JPEG)
输出：定位索引 CSV + 图片目录 + 统计
"""
import json, os, re, struct, datetime, collections, subprocess, csv

JSON_P = r"C:\Users\wardc\Desktop\导_聊天记录.json"
ATTACH = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\attach\f349341f7efaa6679217d8c436e64d91"
OUT = r"C:\Users\wardc\Desktop\中期汇报_2026-09\17_陈晔会话图片全量定位_2026-10-12"
IMG_DIR = os.path.join(OUT, "02_图片")
FFMPEG = r"C:\Users\wardc\Documents\New project gpt\AI-archive\apps\FFmpeg\package\ffmpeg-n8.1-latest-win64-gpl-8.1\bin\ffmpeg.exe"
AES_KEY = b"d24287c68e6e3244"
XOR_KEY = 0xE1

from Cryptodome.Cipher import AES
from Cryptodome.Util import Padding

os.makedirs(IMG_DIR, exist_ok=True)

def dec_size(p):
    try:
        with open(p, "rb") as f:
            h = f.read(15)
    except OSError:
        return None
    if len(h) < 14 or h[:6] != bytes.fromhex("070856320807"):
        return None
    _, a, x = struct.unpack_from("<6sLL", h)
    return a + x

def decode(d):
    _, a, x = struct.unpack_from("<6sLL", d)
    al = a + 16 - (a % 16)
    body = d[15:]
    if al > len(body):
        raise ValueError("size mismatch")
    p = AES.new(AES_KEY, AES.MODE_ECB).decrypt(body[:al])
    try:
        p = Padding.unpad(p, 16)
    except Exception:
        pass
    return p + body[al:len(body) - x] + bytes(b ^ XOR_KEY for b in body[-x:])

def classify(img):
    if img[:3] == b"\xff\xd8\xff": return "jpg"
    if img[:8] == b"\x89PNG\r\n\x1a\n": return "png"
    if img[:6] in (b"GIF87a", b"GIF89a"): return "gif"
    if img[:4] == b"wxgf": return "wxgf"
    return None

# ---------- 1. 消息 ----------
msgs = json.load(open(JSON_P, encoding="utf-8"))
imgs = []
for m in msgs:
    if str(m.get("localType")) != "3":
        continue
    ct = m.get("content") or ""
    gi = lambda k: (re.search(rf'\b{k}="(\d+)"', ct) or [None, None])[1]
    ts = int(m["createTime"])
    dt = datetime.datetime.fromtimestamp(ts)
    imgs.append({"ts": ts, "dt": dt, "ym": dt.strftime("%Y-%m"),
                 "isSend": str(m.get("isSend")),
                 "md5": (re.search(r'\bmd5="([0-9a-f]+)"', ct) or [None, None])[1],
                 "length": gi("length"), "thumb": gi("cdnthumblength"), "hd": gi("hdlength")})

# ---------- 2. 本地文件索引 ----------
files = []
for ym in sorted(os.listdir(ATTACH)):
    d = os.path.join(ATTACH, ym, "Img")
    if not os.path.isdir(d):
        continue
    for f in os.listdir(d):
        if not f.endswith(".dat"):
            continue
        p = os.path.join(d, f)
        files.append({"path": p, "ym": ym, "name": f, "stem": f[:-4], "dec": dec_size(p)})
by_stem = {r["stem"]: r for r in files}
by_dec = collections.defaultdict(list)
for r in files:
    if r["dec"]:
        by_dec[r["dec"]].append(r)

# ---------- 3. 匹配（收集三档）----------
def _find(sizes, want_suffix, ym, allow_any_ym=False):
    """在 by_dec 里按尺寸找文件；want_suffix='_h.dat'/'_t.dat'/None(非 _t/_h)"""
    for sz in sizes:
        for r in by_dec.get(sz, []):
            if not allow_any_ym and r["ym"] != ym:
                continue
            n = r["name"]
            if want_suffix == "_h.dat" and not n.endswith("_h.dat"):
                continue
            if want_suffix == "_t.dat" and not n.endswith("_t.dat"):
                continue
            if want_suffix is None and n.endswith(("_t.dat", "_h.dat")):
                continue
            return r
    return None

def pick(m):
    cands = {"hd": None, "mid": None, "thumb": None}
    hd_sz = [int(m["hd"])] if m["hd"] and int(m["hd"]) > 0 else []
    mid_sz = [int(m["length"])] if m["length"] else []
    th_sz = [int(m["thumb"])] if m["thumb"] else []
    # ① 高清 _h.dat
    cands["hd"] = _find(hd_sz, "_h.dat", m["ym"])
    # ② 中图：优先文件名=md5
    if m["md5"] and m["md5"] in by_stem and not by_stem[m["md5"]]["name"].endswith(("_t.dat", "_h.dat")):
        cands["mid"] = by_stem[m["md5"]]
    if not cands["mid"]:
        cands["mid"] = _find(mid_sz + th_sz, None, m["ym"])
    # ③ 缩略
    cands["thumb"] = _find(th_sz, "_t.dat", m["ym"])
    # ④ 放宽月份约束兜底
    if not any(cands.values()):
        cands["hd"] = _find(hd_sz, "_h.dat", m["ym"], True)
        cands["mid"] = _find(mid_sz + th_sz, None, m["ym"], True)
        cands["thumb"] = _find(th_sz, "_t.dat", m["ym"], True)
    return cands

stat = collections.Counter()
records = []
seq = collections.Counter()
for m in imgs:
    c = pick(m)
    best = c["hd"] or c["mid"] or c["thumb"]
    lvl = "hd" if c["hd"] else ("mid" if c["mid"] else ("thumb" if c["thumb"] else "MISS"))
    stat[lvl] += 1
    saved = ""
    if best:
        try:
            img = decode(open(best["path"], "rb").read())
            kind = classify(img)
            if kind == "wxgf":
                mm = re.search(b"\x00\x00\x00\x01", img)
                if mm:
                    h = os.path.join(IMG_DIR, "_tmp.h265")
                    open(h, "wb").write(img[mm.start():])
                    seq[m["ym"]] += 1
                    name = f"{m['dt'].strftime('%Y%m%d_%H%M%S')}_{'我' if m['isSend']=='1' else '陈晔'}_{seq[m['ym']]:03d}.png"
                    dstp = os.path.join(IMG_DIR, m["ym"], name)
                    os.makedirs(os.path.dirname(dstp), exist_ok=True)
                    r = subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", h, "-frames:v", "1", dstp],
                                       capture_output=True)
                    if os.path.exists(dstp) and os.path.getsize(dstp) > 0:
                        saved = dstp
                    os.remove(h)
            elif kind:
                seq[m["ym"]] += 1
                name = f"{m['dt'].strftime('%Y%m%d_%H%M%S')}_{'我' if m['isSend']=='1' else '陈晔'}_{seq[m['ym']]:03d}.{kind}"
                dstp = os.path.join(IMG_DIR, m["ym"], name)
                os.makedirs(os.path.dirname(dstp), exist_ok=True)
                open(dstp, "wb").write(img)
                saved = dstp
        except Exception as e:
            saved = "ERR:" + str(e)[:40]
    records.append({
        "时间": m["dt"].strftime("%Y-%m-%d %H:%M:%S"),
        "发送方": "我" if m["isSend"] == "1" else "陈晔",
        "月份": m["ym"], "清晰度档": lvl,
        "md5": m["md5"] or "", "length": m["length"] or "",
        "thumb": m["thumb"] or "", "hd": m["hd"] or "",
        "本地源文件": best["path"] if best else "",
        "解密产物": saved,
    })

print("三档命中:", dict(stat))
print("已解密:", sum(1 for r in records if r["解密产物"] and not r["解密产物"].startswith("ERR")))

with open(os.path.join(OUT, "01_定位索引.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(records[0].keys()))
    w.writeheader(); w.writerows(records)
print("索引 ->", os.path.join(OUT, "01_定位索引.csv"))
