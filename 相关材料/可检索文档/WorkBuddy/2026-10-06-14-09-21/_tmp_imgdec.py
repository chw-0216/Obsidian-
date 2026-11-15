# -*- coding: utf-8 -*-
import os, re, glob, hashlib, struct, sys
from pathlib import Path

ACCOUNT = Path(r"C:/Users/wardc/xwechat_files/wxid_zn4ozsnn8esr21_db45")
WXID = "wxid_zn4ozsnn8esr21"
V2_MAGIC = bytes.fromhex("070856320807")
HDR = 15

# 1) 找 kvcomm code
codes = []
for root in [Path(os.environ.get("APPDATA",""))/"Tencent"/"xwechat",
             Path(os.environ.get("LOCALAPPDATA",""))/"Tencent"/"xwechat"]:
    if not root.is_dir(): continue
    for p in root.rglob("key_*_*.statistic"):
        m = re.match(r"^key_(\d+)_.+\.statistic$", p.name, re.I)
        if m: codes.append((int(m.group(1)), str(p)))
print("候选 code:", codes)

try:
    from Cryptodome.Cipher import AES
    from Cryptodome.Util import Padding
    print("Cryptodome OK")
except Exception as e:
    print("Cryptodome 缺失:", e); sys.exit(1)

def probe(aes_key, blocks):
    for b in blocks:
        if len(b) < 16: continue
        try:
            plain = AES.new(aes_key, AES.MODE_ECB).decrypt(b[:16])
        except Exception: continue
        if plain[:3] == b"\xff\xd8\xff" or plain[:8] == b"\x89PNG\r\n\x1a\n" or plain[:6] in (b"GIF87a", b"GIF89a"):
            return True
    return False

# 2) 取模板块
blocks = []
for d in ACCOUNT.glob("msg/attach/*/*/Img"):
    for f in list(d.glob("*.dat"))[:3]:
        try:
            with open(f, "rb") as fh: head = fh.read(HDR+16)
        except Exception: continue
        if head[:6] == V2_MAGIC: blocks.append(head[HDR:])
        if len(blocks) >= 30: break
    if len(blocks) >= 30: break
print("模板块:", len(blocks))

keys = None
for code, path in codes:
    aes_key = hashlib.md5(f"{code}{WXID}".encode()).hexdigest()[:16].encode("ascii")
    if probe(aes_key, blocks):
        keys = (code, aes_key, code & 0xFF)
        print("★ 命中 code =", code, "xor =", hex(code & 0xFF))
        break
if not keys:
    print("未找到可用密钥"); sys.exit(1)

code, aes_key, xor_key = keys
def decode(data):
    _, aes_size, xor_size = struct.unpack_from("<6sLL", data)
    aligned = aes_size + 16 - (aes_size % 16)
    body = data[HDR:]
    if aligned > len(body): raise ValueError("size mismatch")
    plain = AES.new(aes_key, AES.MODE_ECB).decrypt(body[:aligned])
    try: plain = Padding.unpad(plain, 16)
    except Exception: pass
    if xor_size:
        middle = body[aligned:len(body)-xor_size]
        trailer = bytes(b ^ xor_key for b in body[-xor_size:])
    else:
        middle = body[aligned:]; trailer = b""
    return plain + middle + trailer

out = Path("_tmp_jinglin/wumanman_1003"); out.mkdir(parents=True, exist_ok=True)
src = ACCOUNT/"msg"/"attach"/"f0cec7ff81016605a8cefc84c48e0b5b"/"2026-10"/"Img"
n = 0
for f in sorted(src.glob("*.dat")):
    if f.name.endswith("_t.dat"): continue
    try:
        data = f.read_bytes()
        img = decode(data)
        ext = "jpg" if img[:3] == b"\xff\xd8\xff" else ("png" if img[:8] == b"\x89PNG\r\n\x1a\n" else "bin")
        op = out/f"{f.stem}.{ext}"
        op.write_bytes(img); n += 1
        print("解码:", f.name, "->", op.name, len(img), "bytes", ext)
    except Exception as e:
        print("失败:", f.name, e)
print("完成", n, "张")
