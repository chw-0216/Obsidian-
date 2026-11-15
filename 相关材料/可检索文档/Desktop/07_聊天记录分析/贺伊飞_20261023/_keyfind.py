# -*- coding: utf-8 -*-
"""定位 WeFlow 刚抓到的解密密钥（本地只读扫描）"""
import os, re, sys, io, sqlite3, ctypes
from ctypes import wintypes
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PREFIX = b'ae68260c325b434d9ec494fb'
PREFIX16 = PREFIX.decode().encode('utf-16-le')
ROOT = os.path.expandvars(r'%APPDATA%\WeFlow')
HEXRE = re.compile(rb'[0-9a-fA-F]{64}')

print('== 1) 在 WeFlow 应用目录里按前缀/64hex 扫描 ==')
hits = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    # 跳过明显的大缓存目录
    dirnames[:] = [d for d in dirnames if d not in ('Cache', 'Code Cache', 'GPUCache', 'DawnGraphiteCache', 'DawnWebGPUCache', 'Dictionaries')]
    for fn in filenames:
        p = os.path.join(dirpath, fn)
        try:
            sz = os.path.getsize(p)
            if sz > 20 * 1024 * 1024 or sz == 0:
                continue
            data = open(p, 'rb').read()
        except Exception:
            continue
        found_prefix = (PREFIX in data) or (PREFIX16 in data)
        if found_prefix:
            i8 = data.find(PREFIX); i16 = data.find(PREFIX16)
            idx = i8 if i8 >= 0 else i16
            enc = 'utf-8' if i8 >= 0 else 'utf-16-le'
            try:
                txt = data[idx:idx+140].decode(enc, 'replace')
            except Exception:
                txt = ''
            hits.append((p, mtime := os.path.getmtime(p), 'PREFIX', txt[:120]))
        for m in HEXRE.finditer(data):
            hits.append((p, os.path.getmtime(p), 'HEX64', m.group().decode()))
print('hits:', len(hits))
for h in hits[:40]:
    print(h[0], '|', h[2], '|', h[3])

print('\n== 2) SharedStorage (sqlite?) ==')
p = os.path.join(ROOT, 'SharedStorage')
try:
    with open(p, 'rb') as f:
        head = f.read(16)
    print('head:', head)
    c = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
    tables = [r[0] for r in c.execute("select name from sqlite_master where type='table'")]
    print('tables:', tables)
    for t in tables:
        try:
            rows = c.execute(f'select * from "{t}" limit 50').fetchall()
            print(f'-- {t} ({len(rows)} shown)')
            for r in rows:
                print('   ', r)
        except Exception as e:
            print(t, 'ERR', e)
except Exception as e:
    print('ERR', e)

print('\n== 3) ChatTrace keyinfo 用 DPAPI 解密（只打印前缀/结构） ==')
kp = r'C:\Users\wardc\AppData\Local\ChatTrace\keys\wxid_zn4ozsnn8esr21_db45@4.1.12.26.keyinfo'
try:
    blob = open(kp, 'rb').read()
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_char))]
    def blob_of(b):
        buf = ctypes.create_string_buffer(b, len(b))
        return DATA_BLOB(len(b), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))), buf
    inb, keep = blob_of(blob)
    outb = DATA_BLOB()
    ok = ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(inb), None, None, None, None, 0, ctypes.byref(outb))
    print('CryptUnprotectData ok =', bool(ok), 'err =', ctypes.GetLastError())
    if ok:
        dec = ctypes.string_at(outb.pbData, outb.cbData)
        print('decrypted len =', len(dec))
        print('decrypted repr head =', dec[:200])
        try:
            print('as utf-8:', dec.decode('utf-8', 'replace')[:300])
        except Exception:
            pass
except Exception as e:
    print('ERR', e)
