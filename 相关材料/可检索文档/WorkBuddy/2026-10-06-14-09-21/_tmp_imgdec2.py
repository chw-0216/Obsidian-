# -*- coding: utf-8 -*-
import struct, hashlib, re
from pathlib import Path
from Cryptodome.Cipher import AES
from Cryptodome.Util import Padding
AES_KEY = hashlib.md5(("2562432481"+"wxid_zn4ozsnn8esr21").encode()).hexdigest()[:16].encode("ascii")
XOR = 2562432481 & 0xFF; HDR = 15
def decode(d):
    _, aes_size, xor_size = struct.unpack_from("<6sLL", d)
    aligned = aes_size + 16 - (aes_size % 16); body = d[HDR:]
    if aligned > len(body): raise ValueError("size")
    plain = AES.new(AES_KEY, AES.MODE_ECB).decrypt(body[:aligned])
    try: plain = Padding.unpad(plain, 16)
    except Exception: pass
    mid = body[aligned:len(body)-xor_size] if xor_size else body[aligned:]
    tail = bytes(b ^ XOR for b in body[-xor_size:]) if xor_size else b""
    return plain + mid + tail
FFMPEG = r"C:/Users/wardc/Documents/New project gpt/AI-archive/apps/FFmpeg/package/ffmpeg-n8.1-latest-win64-gpl-8.1/bin/ffmpeg.exe"
import subprocess
out = Path("_tmp_jinglin/chenye_1003"); out.mkdir(parents=True, exist_ok=True)
for base in ["f349341f7efaa6679217d8c436e64d91"]:
    src = Path(r"C:/Users/wardc/xwechat_files/wxid_zn4ozsnn8esr21_db45/msg/attach")/base/"2026-10"/"Img"
    if not src.is_dir(): print("无目录", src); continue
    for f in sorted(src.glob("*.dat")):
        try:
            img = decode(f.read_bytes())
        except Exception as e:
            print("fail", f.name, e); continue
        if img[:3] == b"\xff\xd8\xff":
            (out/(f.stem+".jpg")).write_bytes(img); print("JPG", f.name, len(img))
        elif img[:8] == b"\x89PNG\r\n\x1a\n":
            (out/(f.stem+".png")).write_bytes(img); print("PNG", f.name, len(img))
        elif img[:4] in (b"wxgf", b"WXGF"):
            m = re.search(b"\x00\x00\x00\x01", img)
            if m:
                h = out/(f.stem+".h265"); h.write_bytes(img[m.start():])
                png = out/(f.stem+".png")
                subprocess.run([FFMPEG,"-y","-loglevel","error","-i",str(h),"-frames:v","1",str(png)],capture_output=True)
                if png.exists(): print("WXGF→PNG", f.name, png.stat().st_size)
                else: print("WXGF 解码失败", f.name)
            else: print("wxgf 无起始码", f.name)
        else:
            print("未知", f.name, img[:8].hex())
