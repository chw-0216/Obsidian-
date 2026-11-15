# -*- coding: utf-8 -*-
import sqlite3, glob, os, hashlib, datetime, zstandard
BASE = r"C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted/message"
T = "Msg_" + hashlib.md5(b"deerluna").hexdigest()
Z = zstandard.ZstdDecompressor()
seen = {}
for f in sorted(glob.glob(os.path.join(BASE, "message_*.db"))):
    c = sqlite3.connect("file:" + f + "?mode=ro", uri=True)
    names = [r[0] for r in c.execute("select name from sqlite_master where type='table'")]
    if T not in names: c.close(); continue
    for ts, lt, mc, cc, ct in c.execute('select create_time,local_type,message_content,compress_content,WCDB_CT_message_content from "%s"' % T):
        main = lt & 0xFFFFFFFF
        if main in (42, 48, 50):
            k = (main, ct, type(mc).__name__, len(mc) if mc else 0, len(cc) if cc else 0)
            if k in seen: continue
            seen[k] = 1
            print("type=%d ct=%s mc=%s(%d) cc=%d  ts=%s" % (main, ct, type(mc).__name__, len(mc) if mc else 0, len(cc) if cc else 0, datetime.datetime.fromtimestamp(ts)))
            if cc:
                try:
                    print("   zstd →", Z.decompress(cc).decode("utf-8","ignore")[:160])
                except Exception as e:
                    print("   zstd fail:", e)
    c.close()
