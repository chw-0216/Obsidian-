# -*- coding: utf-8 -*-
"""陈晔会话图片 · 第二轮补全（跨全库匹配）。
上一轮只扫了 deerluna 自己的 attach 目录（1,366 个 .dat），
本轮扫整个 xwechat_files（55,733 个 .dat），把 MISS 找回来。

匹配层级：
  A 确定  文件名 stem == XML md5            ← 最可靠
  B 尺寸  解密后字节数精确相等 + 同月
  C 尺寸  解密后字节数精确相等 + 任意月
"""
import json, os, re, struct, datetime, collections, subprocess, csv, shutil

ROOT = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\attach"
JSON_P = r"C:\Users\wardc\Desktop\导_聊天记录.json"
OUT = r"C:\Users\wardc\Desktop\中期汇报_2026-09\17_陈晔会话图片全量定位_2026-10-12"
IMG_DIR = os.path.join(OUT, "02_图片")
CSV_P = os.path.join(OUT, "01_定位索引.csv")
FFMPEG = r"C:\Users\wardc\Documents\New project gpt\AI-archive\apps\FFmpeg\package\ffmpeg-n8.1-latest-win64-gpl-8.1\bin\ffmpeg.exe"
AES_KEY = b"d24287c68e6e3244"
XOR_KEY = 0xE1
from Cryptodome.Cipher import AES
from Cryptodome.Util import Padding

def dec_size(p):
    try:
        with open(p, "rb") as f: h = f.read(15)
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
    if al > len(body): raise ValueError("size mismatch")
    p = AES.new(AES_KEY, AES.MODE_ECB).decrypt(body[:al])
    try: p = Padding.unpad(p, 16)
    except Exception: pass
    return p + body[al:len(body) - x] + bytes(b ^ XOR_KEY for b in body[-x:])

def kind_of(img):
    if img[:3] == b"\xff\xd8\xff": return "jpg"
    if img[:8] == b"\x89PNG\r\n\x1a\n": return "png"
    if img[:6] in (b"GIF87a", b"GIF89a"): return "gif"
    if img[:4] == b"wxgf": return "wxgf"
    return None

# ---------- 1. 全部 654 条图片消息 ----------
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
                 "length": gi("length"), "thumb": gi("cdnthumblength"), "hd": gi("hdlength")})

# ---------- 2. 全库索引 ----------
print("扫描全库 .dat …")
by_stem, by_dec = {}, collections.defaultdict(list)
n = 0
for conv in os.listdir(ROOT):
    cd = os.path.join(ROOT, conv)
    if not os.path.isdir(cd): continue
    for ym in os.listdir(cd):
        d = os.path.join(cd, ym, "Img")
        if not os.path.isdir(d): continue
        for f in os.listdir(d):
            if not f.endswith(".dat"): continue
            p = os.path.join(d, f)
            ds = dec_size(p)
            if ds is None: continue
            rec = {"path": p, "ym": ym, "name": f, "stem": f[:-4], "dec": ds, "conv": conv}
            by_stem.setdefault(rec["stem"], rec)
            by_dec[ds].append(rec); n += 1
print("  可解析 .dat:", n)

# ---------- 3. 已有产物 ----------
done = {}
with open(CSV_P, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        done[r["时间"]] = r
print("  既有索引行:", len(done))

# ---------- 4. 补全 ----------
stat = collections.Counter()
new_rows = []
for m in imgs:
    tstr = m["dt"].strftime("%Y-%m-%d %H:%M:%S")
    old = done.get(tstr)
    if old and old.get("解密产物") and not old["解密产物"].startswith("ERR"):
        stat["已有"] += 1
        continue
    hit = how = None
    # A 文件名=md5
    if m["md5"] and m["md5"] in by_stem:
        hit, how = by_stem[m["md5"]], "A-md5"
    # B 同月尺寸
    if not hit:
        for key, sfx in ((m["hd"], "_h.dat"), (m["length"], None), (m["thumb"], "_t.dat")):
            if not key or int(key) <= 0: continue
            for r in by_dec.get(int(key), []):
                if r["ym"] != m["ym"]: continue
                if sfx == "_h.dat" and not r["name"].endswith("_h.dat"): continue
                if sfx == "_t.dat" and not r["name"].endswith("_t.dat"): continue
                if sfx is None and r["name"].endswith(("_t.dat", "_h.dat")): continue
                hit, how = r, "B-size"
                break
            if hit: break
    # C 任意月尺寸
    if not hit:
        for key, sfx in ((m["hd"], "_h.dat"), (m["length"], None), (m["thumb"], "_t.dat")):
            if not key or int(key) <= 0: continue
            for r in by_dec.get(int(key), []):
                if sfx == "_h.dat" and not r["name"].endswith("_h.dat"): continue
                if sfx == "_t.dat" and not r["name"].endswith("_t.dat"): continue
                if sfx is None and r["name"].endswith(("_t.dat", "_h.dat")): continue
                hit, how = r, "C-any"
                break
            if hit: break
    saved = ""
    if hit:
        try:
            img = decode(open(hit["path"], "rb").read())
            k = kind_of(img)
            if k == "wxgf":
                mm = re.search(b"\x00\x00\x00\x01", img)
                if mm:
                    h = os.path.join(IMG_DIR, "_tmp2.h265")
                    open(h, "wb").write(img[mm.start():])
                    name = f"{m['dt'].strftime('%Y%m%d_%H%M%S')}_{'我' if m['isSend']=='1' else '陈晔'}_补2.png"
                    dstp = os.path.join(IMG_DIR, m["ym"], name)
                    os.makedirs(os.path.dirname(dstp), exist_ok=True)
                    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", h, "-frames:v", "1", dstp], capture_output=True)
                    if os.path.exists(dstp) and os.path.getsize(dstp) > 0: saved = dstp
                    os.remove(h)
            elif k:
                name = f"{m['dt'].strftime('%Y%m%d_%H%M%S')}_{'我' if m['isSend']=='1' else '陈晔'}_补2.{k}"
                dstp = os.path.join(IMG_DIR, m["ym"], name)
                os.makedirs(os.path.dirname(dstp), exist_ok=True)
                open(dstp, "wb").write(img); saved = dstp
        except Exception as e:
            saved = "ERR:" + str(e)[:40]
    stat[how or "MISS"] += 1
    new_rows.append({
        "时间": tstr,
        "发送方": "我" if m["isSend"] == "1" else "陈晔",
        "月份": m["ym"], "清晰度档": how or "MISS",
        "md5": m["md5"] or "", "length": m["length"] or "",
        "thumb": m["thumb"] or "", "hd": m["hd"] or "",
        "本地源文件": hit["path"] if hit else "",
        "解密产物": saved,
    })

print()
print("补全结果:", dict(stat))
ok = sum(1 for r in new_rows if r["解密产物"] and not r["解密产物"].startswith("ERR"))
print("最终已解密:", ok, "/", len(new_rows))

# ---------- 5. 重写 CSV ----------
with open(CSV_P, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(new_rows[0].keys()))
    w.writeheader(); w.writerows(new_rows)
print("索引已更新 ->", CSV_P)

print()
print("=== 仍 MISS 的明细 ===")
for r in new_rows:
    if r["清晰度档"] == "MISS":
        print("%s  %s  %s  md5=%s len=%s thumb=%s hd=%s" %
              (r["时间"], r["发送方"], r["月份"], r["md5"], r["length"], r["thumb"], r["hd"]))
