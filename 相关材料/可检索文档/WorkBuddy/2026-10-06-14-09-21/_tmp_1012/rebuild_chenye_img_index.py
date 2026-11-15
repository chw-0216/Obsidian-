# -*- coding: utf-8 -*-
"""陈晔会话 654 张图片 · 全量重建索引（跨全库 + 尺寸校验）

匹配层级（逐级下探）：
  A  文件名 stem == XML md5                 —— 确定
  H  解密尺寸 == hdlength 且 *_h.dat         —— 同月优先
  M  解密尺寸 == length   且非 _t/_h         —— 同月优先
  T  解密尺寸 == cdnthumblength 且 *_t.dat   —— 同月优先
  （H/M/T 各再放宽「任意月」一次）

校验：XML 给出 cdnthumbwidth/height（654 条全有），缩略图必须尺寸完全一致才算命中。
输出：01_定位索引.csv（654 行，含匹配层级 / 来源会话 / 校验结果）
"""
import json, os, re, struct, datetime, collections, subprocess, csv

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

# ---------- 工具 ----------
def dec_size(p):
    try:
        with open(p, "rb") as f: h = f.read(15)
    except OSError: return None
    if len(h) < 14 or h[:6] != bytes.fromhex("070856320807"): return None
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

def jpeg_size(b):
    """最小 JPEG SOF 解析，返回 (w,h)"""
    i = 2
    n = len(b)
    while i < n - 9:
        if b[i] != 0xFF: i += 1; continue
        m = b[i + 1]
        if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7: i += 2; continue
        seg = struct.unpack_from(">H", b, i + 2)[0]
        if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack_from(">HH", b, i + 5)
            return w, h
        i += 2 + seg
    return None

def png_size(b):
    if len(b) < 24: return None
    w, h = struct.unpack_from(">II", b, 16)
    return w, h

def dims(b, k):
    if k == "jpg": return jpeg_size(b)
    if k == "png": return png_size(b)
    return None

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
            p = os.path.join(d, f)
            ds = dec_size(p)
            if ds is None: continue
            r = {"path": p, "ym": ym, "name": f, "stem": f[:-4], "dec": ds, "conv": conv}
            by_stem.setdefault(r["stem"], r)
            by_dec[ds].append(r)
print("  可解析 .dat:", sum(len(v) for v in by_dec.values()))

# ---------- 3. 匹配 + 解密 ----------
def cands(key, sfx, ym, any_ym=False):
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

def verify(r, m, expect_dims):
    """解码候选并做尺寸校验。返回 (ok, img, kind, note)"""
    try:
        img = decode(open(r["path"], "rb").read())
    except Exception as e:
        return False, None, None, "解码失败"
    k = kind_of(img)
    if not k: return False, None, None, "非图片"
    if expect_dims and k in ("jpg", "png"):
        d = dims(img, k)
        if d and tuple(expect_dims) == d: return True, img, k, "尺寸✓"
        if d: return False, None, None, "尺寸✗%s" % (d,)
    return True, img, k, "尺寸?"

stat = collections.Counter()
records = []
for m in imgs:
    tstr = m["dt"].strftime("%Y-%m-%d %H:%M:%S")
    who = "我" if m["isSend"] == "1" else "陈晔"
    prefix = f"{m['dt'].strftime('%Y%m%d_%H%M%S')}_{who}"
    mdir = os.path.join(IMG_DIR, m["ym"])

    # 已有产物直接复用（避免重复解密）
    have = []
    if os.path.isdir(mdir):
        have = [f for f in os.listdir(mdir) if f.startswith(prefix + "_")]
    if have:
        stat["已有"] += 1
        records.append({"时间": tstr, "发送方": who, "月份": m["ym"], "清晰度档": "已有",
                        "匹配层级": "复用", "md5": m["md5"] or "", "length": m["length"] or "",
                        "thumb": m["thumb"] or "", "hd": m["hd"] or "",
                        "来源会话": "", "本地源文件": "",
                        "解密产物": os.path.join(mdir, sorted(have)[0]), "校验": "—"})
        continue

    want = (int(m["tw"]), int(m["th"])) if m["tw"] and m["th"] else None
    plans = [
        ("A-md5",  [by_stem[m["md5"]]] if (m["md5"] and m["md5"] in by_stem) else [], "尺寸?"),
        ("H-hd",   cands(m["hd"], "_h.dat", m["ym"]), "尺寸?"),
        ("M-mid",  cands(m["length"], None, m["ym"]), "尺寸?"),
        ("T-thumb", cands(m["thumb"], "_t.dat", m["ym"]), "尺寸✓"),
        ("H-any",  cands(m["hd"], "_h.dat", m["ym"], True), "尺寸?"),
        ("M-any",  cands(m["length"], None, m["ym"], True), "尺寸?"),
        ("T-any",  cands(m["thumb"], "_t.dat", m["ym"], True), "尺寸✓"),
    ]
    hit = img = kind = note = lvl = None
    for name, cl, _ in plans:
        for r in cl:
            ok, i2, k2, nt = verify(r, m, want)
            if ok:
                hit, img, kind, note, lvl = r, i2, k2, nt, name
                break
        if hit: break

    saved = ""
    if hit:
        if kind == "wxgf":
            mm = re.search(b"\x00\x00\x00\x01", img)
            if mm:
                h = os.path.join(IMG_DIR, "_tmp3.h265")
                open(h, "wb").write(img[mm.start():])
                dst = os.path.join(mdir, prefix + "_000.png")
                os.makedirs(mdir, exist_ok=True)
                subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", h, "-frames:v", "1", dst], capture_output=True)
                if os.path.exists(dst) and os.path.getsize(dst) > 0: saved = dst
                os.remove(h)
        else:
            dst = os.path.join(mdir, prefix + "_000." + kind)
            os.makedirs(mdir, exist_ok=True)
            open(dst, "wb").write(img); saved = dst
    stat[lvl or "MISS"] += 1
    records.append({"时间": tstr, "发送方": who, "月份": m["ym"],
                    "清晰度档": (lvl.split("-")[0] if lvl else "MISS"),
                    "匹配层级": lvl or "", "md5": m["md5"] or "",
                    "length": m["length"] or "", "thumb": m["thumb"] or "", "hd": m["hd"] or "",
                    "来源会话": hit["conv"] if hit else "",
                    "本地源文件": hit["path"] if hit else "",
                    "解密产物": saved, "校验": note or ""})

print()
print("匹配统计:", dict(stat))
ok = sum(1 for r in records if r["解密产物"])
print("已归档:", ok, "/", len(records))

with open(CSV_P, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(records[0].keys()))
    w.writeheader(); w.writerows(records)
print("索引 ->", CSV_P, "(%d 行)" % len(records))

print()
print("=== 仍 MISS ===")
for r in records:
    if not r["解密产物"]:
        print("%s  %s  %s  md5=%s len=%s thumb=%s hd=%s" %
              (r["时间"], r["发送方"], r["月份"], r["md5"], r["length"], r["thumb"], r["hd"]))
print()
print("=== 非确定匹配（A-md5 之外）分布 ===")
c = collections.Counter(r["匹配层级"] for r in records)
for k in sorted(c): print("  %-10s %d" % (k, c[k]))
print()
print("=== 跨会话匹配（来源会话 != 陈晔会话）===")
CC = "f349341f7efaa6679217d8c436e64d91"
n = 0
for r in records:
    if r["来源会话"] and r["来源会话"] != CC:
        n += 1
        if n <= 20: print("  %s  %s  %s  %s" % (r["时间"], r["匹配层级"], r["校验"], r["来源会话"]))
print("  合计:", n)
