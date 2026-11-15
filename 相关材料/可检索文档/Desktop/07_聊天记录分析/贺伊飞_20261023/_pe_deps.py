# -*- coding: utf-8 -*-
"""解析 wcdb_api.dll 的 PE 导入依赖，并检查每个依赖能否解析到"""
import struct, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DLL = r'C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeFlow\app\resources\resources\wcdb\win32\x64\wcdb_api.dll'
APP = r'C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeFlow\app'
DLLDIR = os.path.dirname(DLL)

def rva2off(secs, rva):
    for va, vs, raw, rsz in secs:
        if va <= rva < va + max(vs, rsz):
            return rva - va + raw
    return None

def pe_imports(path):
    data = open(path, 'rb').read()
    if data[:2] != b'MZ':
        raise ValueError('not MZ')
    e_lfanew = struct.unpack_from('<I', data, 0x3C)[0]
    assert data[e_lfanew:e_lfanew+4] == b'PE\0\0', 'not PE'
    coff = e_lfanew + 4
    nsections = struct.unpack_from('<H', data, coff + 2)[0]
    optsize = struct.unpack_from('<H', data, coff + 16)[0]
    opt = coff + 20
    magic = struct.unpack_from('<H', data, opt)[0]
    pe32plus = magic == 0x20b
    # data dirs start at opt+112 (PE32+) or opt+96 (PE32)
    dd = opt + (112 if pe32plus else 96)
    imp_rva, imp_sz = struct.unpack_from('<II', data, dd + 8)   # dir[1]
    delay_rva, delay_sz = struct.unpack_from('<II', data, dd + 13*8)  # dir[13]
    sec_off = opt + optsize
    secs = []
    for i in range(nsections):
        s = sec_off + i*40
        vs, va, rsz, raw = struct.unpack_from('<IIII', data, s + 8)[0], struct.unpack_from('<I', data, s + 12)[0], struct.unpack_from('<I', data, s + 16)[0], struct.unpack_from('<I', data, s + 20)[0]
        secs.append((va, vs, raw, rsz))
    def read_str(rva):
        off = rva2off(secs, rva)
        if off is None: return None
        end = data.find(b'\0', off)
        return data[off:end].decode('ascii', 'replace')
    names = []
    if imp_rva:
        off = rva2off(secs, imp_rva)
        while off and off + 20 <= len(data):
            desc = data[off:off+20]
            if desc == b'\0'*20: break
            name_rva = struct.unpack_from('<I', desc, 12)[0]
            nm = read_str(name_rva) if name_rva else None
            if nm: names.append(('import', nm))
            off += 20
    if delay_rva:
        off = rva2off(secs, delay_rva)
        while off and off + 32 <= len(data):
            desc = data[off:off+32]
            if desc == b'\0'*32: break
            name_rva = struct.unpack_from('<I', desc, 4)[0]
            nm = read_str(name_rva) if name_rva else None
            if nm: names.append(('delay', nm))
            off += 32
    return names

def find_dep(name):
    cands = [os.path.join(DLLDIR, name), os.path.join(APP, name),
             os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32', name),
             os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'SysWOW64', name)]
    for c in cands:
        if os.path.exists(c): return c
    return None

for dll in ['wcdb_api.dll', 'SDL2.dll']:
    p = os.path.join(DLLDIR, dll)
    print(f'\n== {dll} ==')
    if not os.path.exists(p):
        print('文件不存在!'); continue
    print('size=', os.path.getsize(p))
    try:
        imps = pe_imports(p)
        print('依赖数:', len(imps))
        missing = []
        for kind, nm in imps:
            hit = find_dep(nm)
            print(f'  [{kind}] {nm:32s} -> {hit if hit else "❌ 缺失"}')
            if not hit: missing.append(nm)
        print('缺失:', missing if missing else '无')
    except Exception as e:
        print('解析失败:', e)
