# -*- coding: utf-8 -*-
"""端到端验证：用候选 key 完整解密真实加密库，再做 SQLite smoke test"""
import sys, io, os, tempfile, sqlite3
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from chattrace.service.decryptor import decrypt_file, smoke_test, DecryptError

KEY_HEX = 'ae68260c325b434d9ec494fbc6fad682c4e2189f435249eaaaa29e8cf5f732f7'
WRONG_HEX = 'ae68260c325b434d9ec494fbc6fad682c4e2189f435249eaaaa29e8cf5f732f6'
BASE = r'C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\db_storage'
DBS = [('session/session.db', '消息会话库'), ('contact/contact.db', '联系人库'),
       ('message/message_1.db', '消息主库(分片1)'), ('sns/sns.db', '朋友圈库'), ('general/general.db', '通用库')]

def run(key_hex, label):
    print(f'\n=== {label} ===')
    key = bytes.fromhex(key_hex)
    tmpdir = tempfile.mkdtemp(prefix='wxfull_')
    oks = 0
    for rel, name in DBS:
        src = Path(BASE) / rel.replace('/', '\\')
        dst = Path(tmpdir) / (name.replace('/', '_') + '.db')
        try:
            decrypt_file(src, dst, key)
            n = smoke_test(dst)
            with open(dst, 'rb') as f:
                head = f.read(16)
            print(f'{name:12s} ✅ 解密+打开成功 | sqlite_master 对象数={n} | 明文头={head!r}')
            oks += 1
        except DecryptError as e:
            print(f'{name:12s} ❌ {e}')
        except Exception as e:
            print(f'{name:12s} ❌ 失败: {type(e).__name__}: {e}')
    return oks, len(DBS)

ok_good, total = run(KEY_HEX, '候选 key（你给的那条）')
ok_bad, _ = run(WRONG_HEX, '负对照：错误 key（末位 f6）')

print('\n== 结论 ==')
if ok_good == total and ok_bad == 0:
    print(f'✅ 密钥可用：{ok_good}/{total} 个库完整解密并通过 SQLite 打开测试；错误 key {ok_bad}/{total} 通过（0 应为正确）。')
elif ok_good > 0:
    print(f'⚠️ 部分可用：{ok_good}/{total}；错误 key 通过 {ok_bad}/{total}。')
else:
    print('❌ 不可用：候选 key 未能打开任何库。')
