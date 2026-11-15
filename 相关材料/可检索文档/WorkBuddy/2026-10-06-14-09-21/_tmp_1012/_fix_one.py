# -*- coding: utf-8 -*-
import struct, os, re, subprocess, tempfile, sys
AES_KEY = b"d24287c68e6e3244"; XOR_KEY = 0xE1
from Cryptodome.Cipher import AES
from Cryptodome.Util import Padding

FFMPEG = r"C:\Users\wardc\Documents\New project gpt\AI-archive\apps\FFmpeg\package\ffmpeg-n8.1-latest-win64-gpl-8.1\bin\ffmpeg.exe"
SRC = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\attach\f349341f7efaa6679217d8c436e64d91\2026-10\Img\08f891f4e256cb50124c8898cce0636b.dat"
DST = r"C:\Users\wardc\Desktop\07_聊天记录分析\陈晔会话图片_2026-10-14\02_图片\2026-10\20261002_191738_陈晔_补.jpg"

d = open(SRC, "rb").read()
_, a, x = struct.unpack_from("<6sLL", d)
al = a + 16 - (a % 16); body = d[15:]
p = AES.new(AES_KEY, AES.MODE_ECB).decrypt(body[:al])
try: p = Padding.unpad(p, 16)
except Exception: pass
img = p + body[al:len(body) - x] + bytes(b ^ XOR_KEY for b in body[-x:])
mm = re.search(b"\x00\x00\x00\x01", img)
print("mm:", mm.start() if mm else None)
h = os.path.join(tempfile.gettempdir(), "_t.h265")
open(h, "wb").write(img[mm.start():])
print("h265 size:", os.path.getsize(h))
r = subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", h, "-frames:v", "1", DST],
                   capture_output=True)
print("rc:", r.returncode)
print("stderr:", r.stderr.decode("utf-8", "replace")[:800])
print("dst exists:", os.path.exists(DST), os.path.getsize(DST) if os.path.exists(DST) else "")
