# -*- coding: utf-8 -*-
"""抽样验证大表内容 + 分片规律。只读。"""
import sqlite3, os, datetime, zstandard as zstd

DEC = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\message"
T = "Msg_9fb42c97aa9bd5968bff915e17a311b2"
dctx = zstd.ZstdDecompressor()

def dec(b):
    if b is None: return ""
    if isinstance(b, str): return b
    raw = bytes(b)
    if not raw: return ""
    try: return dctx.decompress(raw, max_output_size=1 << 24).decode("utf-8", "replace")
    except Exception:
        try: return raw.decode("utf-8", "replace")
        except Exception: return ""

for dbf in ("message_0.db", "message_1.db"):
    p = os.path.join(DEC, dbf)
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    try:
        n = con.execute(f'SELECT COUNT(*) FROM "{T}"').fetchone()[0]
    except Exception:
        print(dbf, "无此表"); con.close(); continue
    cols = [r[1] for r in con.execute(f'PRAGMA table_info("{T}")')]
    print(f"=== {dbf}  行 {n}  列 {cols}")
    print("   首 2 条：")
    for r in con.execute(f'SELECT create_time, real_sender_id, local_type, local_id, message_content FROM "{T}" ORDER BY create_time LIMIT 2'):
        t = datetime.datetime.fromtimestamp(r[0]).strftime("%Y-%m-%d %H:%M:%S")
        print(f"     {t} | rsid={r[1]} lt={r[2]} lid={r[3]} | {dec(r[4])[:70]!r}")
    print("   末 2 条：")
    for r in con.execute(f'SELECT create_time, real_sender_id, local_type, local_id, message_content FROM "{T}" ORDER BY create_time DESC LIMIT 2'):
        t = datetime.datetime.fromtimestamp(r[0]).strftime("%Y-%m-%d %H:%M:%S")
        print(f"     {t} | rsid={r[1]} lt={r[2]} lid={r[3]} | {dec(r[4])[:70]!r}")
    # 按月分布（抽样）
    print("   按月行数：")
    for ym, k in con.execute(f'SELECT strftime("%Y-%m",create_time,"unixepoch","localtime"), COUNT(*) FROM "{T}" GROUP BY ym ORDER BY ym'):
        print(f"     {ym}  {k:>8}")
    con.close()
