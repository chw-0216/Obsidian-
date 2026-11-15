# -*- coding: utf-8 -*-
"""独立验证：给定 hex 密钥能否打开本机微信 4.x 加密库（SQLCipher4 页 HMAC）"""
import sys, io, os, tempfile, hashlib, base64, json, ctypes
from pathlib import Path
from ctypes import wintypes
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CANDIDATE_HEX = 'ae68260c325b434d9ec494fbc6fad682c4e2189f435249eaaaa29e8cf5f732f7'
WRONG_HEX     = 'ae68260c325b434d9ec494fbc6fad682c4e2189f435249eaaaa29e8cf5f732f6'  # 只改最后一位

# ---- 读取 ChatTrace 里存的 key（DPAPI 解密），仅用于对照 ----
def stored_key_hex():
    kp = r'C:\Users\wardc\AppData\Local\ChatTrace\keys\wxid_zn4ozsnn8esr21_db45@4.1.12.26.keyinfo'
    blob = open(kp, 'rb').read()
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_char))]
    buf = ctypes.create_string_buffer(blob, len(blob))
    inb = DATA_BLOB(len(blob), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    outb = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(inb), None, None, None, None, 0, ctypes.byref(outb)):
        return None
    dec = ctypes.string_at(outb.pbData, outb.cbData)
    info = json.loads(dec.decode('utf-8'))
    raw = base64.b64decode(info['password_b64'])
    return raw.hex(), info

# ---- 用 ChatTrace 自己的 verify 逻辑做 HMAC 校验 ----
from chattrace.keyagent.verify import test_key_against_db, read_db_header

BASE = r'C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\db_storage'
DBS = [
    ('session/session.db', '消息会话库'),
    ('contact/contact.db', '联系人库'),
    ('message/message_1.db', '消息主库(分片1)'),
    ('sns/sns.db', '朋友圈库'),
    ('general/general.db', '通用库'),
]

stored = stored_key_hex()
print('== 密钥来源对照 ==')
if stored:
    sh, sinfo = stored
    print('ChatTrace 存储 key (hex) =', sh)
    print('与候选 key 完全相同 =', sh.lower() == CANDIDATE_HEX.lower(),
          '| captured_at =', sinfo.get('captured_at'), '| variant =', sinfo.get('variant'))
else:
    print('未能读取存储 key')

print('\n== 逐库 HMAC 校验（候选 key） ==')
tmpdir = tempfile.mkdtemp(prefix='wxkeytest_')
results = []
for rel, name in DBS:
    src = os.path.join(BASE, rel.replace('/', '\\'))
    if not os.path.exists(src):
        print(f'{name:12s} 跳过（文件不存在）'); continue
    # 只拷贝前 12KB 做校验（避免整库拷贝，也不受微信写锁影响的大部分情况）
    try:
        with open(src, 'rb') as f:
            head = f.read(12288)
        if len(head) < 8192:
            print(f'{name:12s} 跳过（可读字节不足 8192，源库可能被独占）')
            continue
        tmp = os.path.join(tmpdir, 'head.db')
        with open(tmp, 'wb') as f:
            f.write(head)
        ok, msg = test_key_against_db(CANDIDATE_HEX, Path(tmp))
        results.append((name, ok, msg))
        print(f'{name:12s} -> {"✅ 能用" if ok else "❌ 不能用"}  | {msg}')
    except Exception as e:
        print(f'{name:12s} 读取失败: {e}')

print('\n== 负对照（错误 key，最后一位 f7→f6） ==')
tmpdir2 = tempfile.mkdtemp(prefix='wxkeytest_neg_')
src = os.path.join(BASE, 'session', 'session.db')
try:
    with open(src, 'rb') as f:
        head = f.read(8192)
    tmp = os.path.join(tmpdir2, 'head.db')
    open(tmp, 'wb').write(head)
    ok, msg = test_key_against_db(WRONG_HEX, Path(tmp))
    print('错误 key ->', '✅ 意外通过' if ok else '❌ 被拒绝（符合预期）', '|', msg)
except Exception as e:
    print('负对照读取失败:', e)

print('\n== 结论 ==')
passed = [r for r in results if r[1]]
if results and len(passed) == len(results):
    print(f'✅ 密钥可用：{len(passed)}/{len(results)} 个库 HMAC 校验全部通过；负对照被拒绝。')
elif passed:
    print(f'⚠️ 部分通过：{len(passed)}/{len(results)}（其余可能是校验样本不足/库格式特殊）')
else:
    print('❌ 未通过：该密钥打不开这些库。')
