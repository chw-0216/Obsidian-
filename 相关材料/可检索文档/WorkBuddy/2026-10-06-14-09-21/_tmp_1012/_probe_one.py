# -*- coding: utf-8 -*-
import struct, sys, os
sys.path.insert(0, r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21\_tmp_1012")
AES_KEY = b"d24287c68e6e3244"; XOR_KEY = 0xE1
from Cryptodome.Cipher import AES
from Cryptodome.Util import Padding

P = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\attach\f349341f7efaa6679217d8c436e64d91\2026-10\Img\08f891f4e256cb50124c8898cce0636b.dat"

d = open(P, "rb").read()
print("文件大小:", len(d))
print("头 15 字节:", d[:15].hex())
_, a, x = struct.unpack_from("<6sLL", d)
print("aes_size=%d xor_size=%d" % (a, x))
al = a + 16 - (a % 16); body = d[15:]
print("al=%d body=%d" % (al, len(body)))
p = AES.new(AES_KEY, AES.MODE_ECB).decrypt(body[:al])
try:
    p = Padding.unpad(p, 16)
except Exception as e:
    print("unpad fail:", e)
out = p + body[al:len(body) - x] + bytes(b ^ XOR_KEY for b in body[-x:])
print("解密长度:", len(out))
print("前 16 字节:", out[:16].hex())
print("前 16 可见:", out[:16])
mm = None
for sig in (b"\x00\x00\x00\x01", b"\x00\x00\x01", b"ftyp", b"wxgf"):
    i = out.find(sig)
    print("  查找", sig, "->", i)
