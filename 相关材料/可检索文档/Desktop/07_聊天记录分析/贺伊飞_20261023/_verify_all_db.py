# -*- coding: utf-8 -*-
"""全库覆盖：对 db_storage 下每个 .db 读首页做 SQLCipher4 HMAC 校验（只读，不整库解密）"""
import sys, io, os, tempfile
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from chattrace.keyagent.verify import test_key_against_db, read_db_header

KEY = 'ae68260c325b434d9ec494fbc6fad682c4e2189f435249eaaaa29e8cf5f732f7'
BASE = Path(r'C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\db_storage')
tmp = Path(tempfile.mkdtemp(prefix='wxall_')) / 'h.db'
ok = skip = bad = 0
badlist = []
for src in sorted(BASE.rglob('*.db')):
    try:
        with open(src, 'rb') as f:
            head = f.read(8192)
        if len(head) < 8192:
            print(f'跳过(太小) {src.relative_to(BASE)} ({len(head)}B)'); skip += 1; continue
        tmp.write_bytes(head)
        good, msg = test_key_against_db(KEY, tmp)
        rel = str(src.relative_to(BASE)).replace('\\', '/')
        if good:
            ok += 1
            print(f'✅ {rel}')
        else:
            bad += 1; badlist.append(rel)
            print(f'❌ {rel} | {msg}')
    except Exception as e:
        skip += 1
        print(f'跳过 {src.relative_to(BASE)} | {e}')
print(f'\n覆盖结果：通过 {ok} | 失败 {bad} | 跳过 {skip} | 合计 {ok+bad+skip}')
if badlist: print('失败列表:', badlist)
