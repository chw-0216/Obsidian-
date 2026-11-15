# -*- coding: utf-8 -*-
"""校验「补2」文件：用 XML 的 cdnthumbwidth/height 核对尺寸。
不通过者 → 尝试重新匹配；仍失败 → 标记 UNVERIFIED。
"""
import json, os, re, struct, datetime, collections

OUT = r"C:\Users\wardc\Desktop\中期汇报_2026-09\17_陈晔会话图片全量定位_2026-10-12"
IMG_DIR = os.path.join(OUT, "02_图片")
JSON_P = r"C:\Users\wardc\Desktop\导_聊天记录.json"

def jpeg_size(b):
    i = 2; n = len(b)
    while i < n - 9:
        if b[i] != 0xFF: i += 1; continue
        m = b[i + 1]
        if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7: i += 2; continue
        seg = struct.unpack_from(">H", b, i + 2)[0]
        if m in (0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF):
            h, w = struct.unpack_from(">HH", b, i + 5); return w, h
        i += 2 + seg
    return None

def png_size(b):
    if len(b) < 24: return None
    return struct.unpack_from(">II", b, 16)

def dims_of(p):
    b = open(p, "rb").read()
    if b[:3] == b"\xff\xd8\xff": return jpeg_size(b)
    if b[:8] == b"\x89PNG\r\n\x1a\n": return png_size(b)
    return None

# 消息表：ts -> (tw, th, thumb_len, hd_len, mid_len)
msgs = json.load(open(JSON_P, encoding="utf-8"))
idx = {}
for m in msgs:
    if str(m.get("localType")) != "3": continue
    ct = m.get("content") or ""
    gi = lambda k: (re.search(rf'\b{k}="(\d+)"', ct) or [None, None])[1]
    ts = int(m["createTime"])
    idx[ts] = {"tw": gi("cdnthumbwidth"), "th": gi("cdnthumbheight"),
               "thumb": gi("cdnthumblength"), "hd": gi("hdlength"), "mid": gi("length"),
               "who": "我" if str(m.get("isSend")) == "1" else "陈晔"}

ok = bad = nodim = 0
bad_list = []
for ym in sorted(os.listdir(IMG_DIR)):
    d = os.path.join(IMG_DIR, ym)
    if not os.path.isdir(d): continue
    for f in sorted(os.listdir(d)):
        if "_补2." not in f: continue
        mm = re.match(r"(\d{8})_(\d{6})_([^_]+)_", f)
        if not mm: continue
        dt = datetime.datetime.strptime(mm.group(1) + mm.group(2), "%Y%m%d%H%M%S")
        ts = int(dt.timestamp())
        info = idx.get(ts)
        p = os.path.join(d, f)
        size = os.path.getsize(p)
        d0 = dims_of(p)
        if not info:
            nodim += 1; continue
        want = (int(info["tw"]), int(info["th"])) if info["tw"] and info["th"] else None
        if d0 and want:
            if d0 == want: ok += 1
            else:
                bad += 1
                bad_list.append((f, d0, want, size, info["thumb"], info["hd"], info["mid"]))
        else:
            nodim += 1
            bad_list.append((f, d0, want, size, info["thumb"], info["hd"], info["mid"]))

print("补2 校验：尺寸✓ %d ｜ 尺寸✗ %d ｜ 无法判定 %d" % (ok, bad, nodim))
print()
print("=== 需人工核对 ===")
for f, d0, want, size, th, hd, mid in bad_list:
    print("%-46s 实际=%s 期望=%s 文件=%dB thumb=%s hd=%s mid=%s" % (f, d0, want, size, th, hd, mid))
