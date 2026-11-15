# -*- coding: utf-8 -*-
import sqlite3, os, datetime, hashlib
BASE = r"C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted"
T = "Msg_" + hashlib.md5(b"filehelper").hexdigest()
for f in sorted(os.listdir(os.path.join(BASE, "message"))):
    if not f.startswith("message_"): continue
    p = os.path.join(BASE, "message", f)
    try:
        c = sqlite3.connect("file:" + p + "?mode=ro", uri=True)
        names = [r[0] for r in c.execute("select name from sqlite_master where type='table'")]
        if T in names:
            n = c.execute('select count(*) from "%s"' % T).fetchone()[0]
            last = c.execute('select create_time, local_type from "%s" order by create_time desc limit 3' % T).fetchall()
            print("%s  count=%d" % (f, n))
            for ts, lt in last:
                print("   ", datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"), "local_type=", lt)
        c.close()
    except Exception as e:
        print(f, "ERR", e)
# session 表看未读
for sub in ("session", "contact"):
    d = os.path.join(BASE, sub)
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if not f.endswith(".db"): continue
            try:
                c = sqlite3.connect("file:" + os.path.join(d, f) + "?mode=ro", uri=True)
                for (u, ts, un, sm) in c.execute("select username,last_timestamp,unread_count,summary from SessionTable where username='filehelper'"):
                    print("SESSION filehelper:", datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"), "unread=", un)
                c.close()
            except Exception as e:
                pass
