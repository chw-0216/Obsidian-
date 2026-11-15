# -*- coding: utf-8 -*-
"""额外证据：用候选 key 实际解密每个库的第 1 页，检查 SQLite 明文头"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from Cryptodome.Cipher import AES
from chattrace.keyagent.verify import read_db_header, derive_enc_key

KEY = bytes.fromhex('ae68260c325b434d9ec494fbc6fad682c4e2189f435249eaaaa29e8cf5f732f7')
BASE = r'C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\db_storage'
DBS = [('session/session.db', '消息会话库'), ('contact/contact.db', '联系人库'),
       ('message/message_1.db', '消息主库(分片1)'), ('sns/sns.db', '朋友圈库'), ('general/general.db', '通用库')]

import tempfile
tmpdir = tempfile.mkdtemp(prefix='wxplain_')
for rel, name in DBS:
    src = os.path.join(BASE, rel.replace('/', '\\'))
    try:
        with open(src, 'rb') as f:
            head = f.read(8192)
        tmp = os.path.join(tmpdir, 'h.db')
        open(tmp, 'wb').write(head)
        hdr = read_db_header(tmp)
        enc_key = derive_enc_key(KEY, hdr.salt)
        page1 = hdr.pages[0]                     # 4080 bytes (salt stripped)
        iv = page1[-96:-80]
        plain = AES.new(enc_key, AES.MODE_CBC, iv).decrypt(page1[:-80])
        magic = plain[:16]
        print(f'{name:12s} 明文头 = {magic!r}  -> {"✅ SQLite format 3" if magic.startswith(b"SQLite format 3") else "❌ 非 SQLite 头"}')
    except Exception as e:
        print(f'{name:12s} 解密失败: {e}')
