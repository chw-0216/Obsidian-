# -*- coding: utf-8 -*-
"""解密微信 4.x 图片 .dat（V2 格式）—— filehelper 2026-10-12 批次。"""
import os, re, struct, hashlib, subprocess, io, sys
from Cryptodome.Cipher import AES
from Cryptodome.Util import Padding

SRC = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\attach\9e20f478899dc29eb19741386f9343c8\2026-10\Img"
OUT = r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21\_tmp_1012\fh_dec"
FFMPEG = r"C:\Users\wardc\Documents\New project gpt\AI-archive\apps\FFmpeg\package\ffmpeg-n8.1-latest-win64-gpl-8.1\bin\ffmpeg.exe"
WXID = "wxid_zn4ozsnn8esr21"
HDR = 15
MAGIC = bytes.fromhex("070856320807")

os.makedirs(OUT, exist_ok=True)

# ---------- 密钥派生 ----------
def derive(code):
    aes_key = hashlib.md5(f"{code}{WXID}".encode()).hexdigest()[:16].encode()
    return aes_key, (code & 0xFF)

def find_codes():
    out = []
    base = os.path.join(os.environ["APPDATA"], "Tencent", "xwechat")
    for dp, _, fs in os.walk(base):
        for f in fs:
            m = re.match(r"^key_(\d+)_.+\.statistic$", f, re.I)
            if m:
                out.append(int(m.group(1)))
    return sorted(set(out))

def probe(aes_key, blocks):
    for b in blocks:
        if len(b) < 16:
            continue
        p = AES.new(aes_key, AES.MODE_ECB).decrypt(b[:16])
        if p[:3] == b"\xff\xd8\xff" or p[:8] == b"\x89PNG\r\n\x1a\n" or p[:6] in (b"GIF87a", b"GIF89a") or p[:4] == b"wxgf":
            return True
    return False

def decode_v2(d, aes_key, xor_key):
    _, aes_size, xor_size = struct.unpack_from("<6sLL", d)
    aligned = aes_size + 16 - (aes_size % 16)
    body = d[HDR:]
    if aligned > len(body):
        raise ValueError(f"size mismatch aligned={aligned} body={len(body)}")
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
    if img[:3] == b"\xff\xd8\xff": return "jpeg"
    if img[:8] == b"\x89PNG\r\n\x1a\n": return "png"
    if img[:6] in (b"GIF87a", b"GIF89a"): return "gif"
    if img[:4] == b"wxgf": return "wxgf"
    return "?"

def save(img, stem, kind):
    if kind in ("jpeg", "png", "gif"):
        ext = {"jpeg": "jpg", "png": "png", "gif": "gif"}[kind]
        p = os.path.join(OUT, f"{stem}.{ext}")
        open(p, "wb").write(img)
        return p
    if kind == "wxgf":
        m = re.search(b"\x00\x00\x00\x01", img)
        if not m:
            return None
        h = os.path.join(OUT, f"{stem}.h265")
        open(h, "wb").write(img[m.start():])
        p = os.path.join(OUT, f"{stem}.png")
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", h, "-frames:v", "1", p],
                       capture_output=True)
        if os.path.exists(p) and os.path.getsize(p) > 0:
            os.remove(h)
            return p
        return None
    return None

# ---------- 主流程 ----------
codes = find_codes()
print("kvcomm codes:", codes)

dats = sorted(f for f in os.listdir(SRC) if f.endswith(".dat") and not f.endswith("_t.dat"))
print(f"待解密 .dat: {len(dats)}")

# 自动锁定密钥：用真实密文块验证
key = xor = None
for code in codes:
    k, x = derive(code)
    ok = False
    for f in dats[:6]:
        d = open(os.path.join(SRC, f), "rb").read()
        if len(d) < HDR + 16:
            continue
        try:
            img = decode_v2(d, k, x)
        except Exception:
            continue
        if classify(img) != "?":
            ok = True
            break
    if ok:
        key, xor = k, x
        print(f"锁定密钥: code={code} aes_key={k.decode()} xor=0x{x:02X}")
        break

if key is None:
    print("!! 未能锁定密钥")
    sys.exit(1)

results = []
for f in dats:
    p = os.path.join(SRC, f)
    d = open(p, "rb").read()
    try:
        img = decode_v2(d, key, xor)
    except Exception as e:
        results.append((f, "ERR", str(e), 0)); continue
    kind = classify(img)
    stem = f[:-4]
    out = save(img, stem, kind)
    results.append((f, kind, os.path.basename(out) if out else "FAIL", len(img)))

print()
for f, kind, out, n in results:
    print(f"{kind:6s} {n:>9,}  {f[:16]}…  ->  {out}")
