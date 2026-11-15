# -*- coding: utf-8 -*-
"""只读：源库核对 v3 —— 解码 zstd 内容"""
import sqlite3, hashlib, datetime, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
BASE = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\message'
TZ = datetime.timezone(datetime.timedelta(hours=8))
def ts(t):
    try: return datetime.datetime.fromtimestamp(int(t), tz=TZ).strftime('%Y-%m-%d %H:%M:%S')
    except Exception: return str(t)
try:
    import zstandard as zstd
    dctx = zstd.ZstdDecompressor()
except Exception:
    dctx = None
    print('!! zstandard 不可用')

tbl = 'Msg_' + hashlib.md5(b'hyf782877122').hexdigest()
for db in ('message_0.db','message_1.db'):
    p = BASE + '\\' + db
    c = sqlite3.connect(f'file:{p}?mode=ro', uri=True); c.execute('PRAGMA query_only=ON')
    ex = c.execute("select name from sqlite_master where type='table' and name=?", (tbl,)).fetchone()
    if not ex:
        continue
    print(f'\n===== {db} / {tbl} =====')
    cols = [x[1] for x in c.execute(f'pragma table_info("{tbl}")')]
    rows = c.execute(f'select local_id, server_id, local_type, real_sender_id, create_time, message_content, compress_content, WCDB_CT_message_content, source from "{tbl}" order by create_time, local_id').fetchall()
    print('rows:', len(rows))
    for r in rows:
        local_id, server_id, ltype, sender, ct, content, comp, cttype, source = r
        def dec(val, ctype):
            if val is None: return ''
            if isinstance(val, bytes):
                if val[:4] == b'\x28\xb5\x2f\xfd' and dctx:
                    try: return dctx.decompress(val, max_output_size=64*1024*1024).decode('utf-8','replace')
                    except Exception as e: return f'<zstd err {e}>'
                try: return val.decode('utf-8','replace')
                except Exception: return f'<blob {len(val)}>'
            return str(val)
        txt = dec(content, cttype) or dec(comp, None)
        txt = txt.replace('\n','\\n')
        if len(txt) > 600: txt = txt[:600]+'…'
        print(f'[{ts(ct)}] local={local_id} svr={server_id} type={ltype} sender={sender} | {txt}')
