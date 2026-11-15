# -*- coding: utf-8 -*-
"""filehelper 2026-10-12 全批次：消息 XML ↔ 本地 .dat 精确匹配 + 解密归档。
方法：XML 的 length(中图) / cdnthumblength(缩略图) / hdlength(高清) == 本地 .dat 解密后字节数 = aes_size + xor_size
"""
import os, re, struct, hashlib, subprocess, sqlite3, datetime, shutil, sys
from Cryptodome.Cipher import AES
from Cryptodome.Util import Padding

WXID = "wxid_zn4ozsnn8esr21"
SRC = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\attach\9e20f478899dc29eb19741386f9343c8\2026-10\Img"
IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
OUT = r"C:\Users\wardc\Desktop\中期汇报_2026-09\18_文件传输助手_1012全批次"
FFMPEG = r"C:\Users\wardc\Documents\New project gpt\AI-archive\apps\FFmpeg\package\ffmpeg-n8.1-latest-win64-gpl-8.1\bin\ffmpeg.exe"
HDR = 15

os.makedirs(OUT, exist_ok=True)

def derive(code):
    return hashlib.md5(f"{code}{WXID}".encode()).hexdigest()[:16].encode(), (code & 0xFF)

def find_codes():
    out = []
    base = os.path.join(os.environ["APPDATA"], "Tencent", "xwechat")
    for dp, _, fs in os.walk(base):
        for f in fs:
            m = re.match(r"^key_(\d+)_.+\.statistic$", f, re.I)
            if m:
                out.append(int(m.group(1)))
    return sorted(set(out))

def decode_v2(d, aes_key, xor_key):
    _, aes_size, xor_size = struct.unpack_from("<6sLL", d)
    aligned = aes_size + 16 - (aes_size % 16)
    body = d[HDR:]
    if aligned > len(body):
        raise ValueError("size mismatch")
    plain = AES.new(aes_key, AES.MODE_ECB).decrypt(body[:aligned])
    try:
        plain = Padding.unpad(plain, 16)
    except Exception:
        pass
    if xor_size:
        mid = body[aligned:len(body) - xor_size]
        tail = bytes(b ^ xor_key for b in body[-xor_size:])
    else:
        mid = body[aligned:]
        tail = b""
    return plain + mid + tail

def classify(img):
    if img[:3] == b"\xff\xd8\xff": return "jpg"
    if img[:8] == b"\x89PNG\r\n\x1a\n": return "png"
    if img[:6] in (b"GIF87a", b"GIF89a"): return "gif"
    if img[:4] == b"wxgf": return "wxgf"
    return "?"

# ---------- 1. 建立 .dat 尺寸表（带 mtime 用于消歧） ----------
sizes = {}   # decrypted_bytes -> [(filename, mtime)]
for f in os.listdir(SRC):
    if not f.endswith(".dat"):
        continue
    p = os.path.join(SRC, f)
    d = open(p, "rb").read()
    if len(d) < HDR:
        continue
    try:
        _, aes_size, xor_size = struct.unpack_from("<6sLL", d)
    except Exception:
        continue
    n = aes_size + xor_size
    sizes.setdefault(n, []).append((f, os.path.getmtime(p)))
print(f"尺寸表: {len(sizes)} 个不同字节数")

# ---------- 2. 读 filehelper 今天消息 ----------
con = sqlite3.connect(IDX)
st = int(datetime.datetime(2026, 10, 12, 0, 0).timestamp())
rows = list(con.execute(
    "select ts,type,content from messages where session_key like '%filehelper%' and ts>=? order by ts", (st,)))

imgs = []
for ts, typ, content in rows:
    if typ != "image" or not content:
        continue
    aes = re.search(r'(?<![A-Za-z])aeskey="([0-9a-f]{32})"', content)
    vals = {}
    for k in ("hdlength", "length", "cdnthumblength"):
        m = re.search(r'(?<![A-Za-z])%s="(\d+)"' % k, content)   # 词边界：避免 cdnthumblength 被当成 length
        vals[k] = int(m.group(1)) if m else 0
    m = re.search(r'hevc_mid_size="(\d+)"', content)
    vals["hevc_mid_size"] = int(m.group(1)) if m else 0
    imgs.append((ts, aes.group(1) if aes else "", vals))

print(f"今天 image 消息: {len(imgs)}")

# ---------- 3. 锁密钥 ----------
codes = find_codes()
key = xor = None
sample = [f for f in os.listdir(SRC) if f.endswith(".dat") and not f.endswith("_t.dat")][:8]
for code in codes:
    k, x = derive(code)
    for f in sample:
        d = open(os.path.join(SRC, f), "rb").read()
        try:
            img = decode_v2(d, k, x)
        except Exception:
            continue
        if classify(img) != "?":
            key, xor = k, x
            print(f"锁定密钥 code={code} aes_key={k.decode()} xor=0x{x:02X}")
            break
    if key: break

if not key:
    print("!! 未锁定密钥"); sys.exit(1)

# ---------- 4. 匹配 + 解密 ----------
log = []
for i, (ts, aes, vals) in enumerate(imgs, 1):
    t = datetime.datetime.fromtimestamp(ts).strftime("%H%M%S")
    hit = None; hitkind = ""
    for k in ("hdlength", "length", "hevc_mid_size", "cdnthumblength"):
        v = vals.get(k, 0)
        if v and v in sizes:
            cands = sizes[v]
            # 同尺寸多文件时，取 mtime 最接近消息时间的
            cands.sort(key=lambda c: abs(c[1] - ts))
            hit, hitkind = cands[0][0], k
            break
    if not hit:
        log.append((t, aes[:12], vals, "MISS", ""))
        continue
    d = open(os.path.join(SRC, hit), "rb").read()
    try:
        img = decode_v2(d, key, xor)
    except Exception as e:
        log.append((t, aes[:12], vals, "ERR " + str(e), hit)); continue
    kind = classify(img)
    stem = f"{t}_{i:02d}_{hitkind}"
    if kind in ("jpg", "png", "gif"):
        p = os.path.join(OUT, f"{stem}.{kind}")
        open(p, "wb").write(img)
        log.append((t, aes[:12], vals, f"{kind} {len(img):,}", os.path.basename(p)))
    elif kind == "wxgf":
        m = re.search(b"\x00\x00\x00\x01", img)
        if m:
            h = os.path.join(OUT, f"{stem}.h265")
            open(h, "wb").write(img[m.start():])
            p = os.path.join(OUT, f"{stem}.png")
            subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", h, "-frames:v", "1", p], capture_output=True)
            if os.path.exists(p) and os.path.getsize(p) > 0:
                os.remove(h)
                log.append((t, aes[:12], vals, f"wxgf->png {len(img):,}", os.path.basename(p)))
            else:
                log.append((t, aes[:12], vals, "wxgf FAIL", h))
    else:
        log.append((t, aes[:12], vals, "unknown " + kind, hit))

print()
print(f"{'时间':8} {'aeskey':12} {'hd/mid/thumb':26} {'结果':18} 文件")
for t, a, v, r, f in log:
    vv = f"{v['hdlength']}/{v['length']}/{v['cdnthumblength']}"
    print(f"{t:8} {a:12} {vv:26} {r:18} {f}")
