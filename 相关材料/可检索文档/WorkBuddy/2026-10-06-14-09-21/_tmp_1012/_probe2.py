# -*- coding: utf-8 -*-
import sqlite3, glob, os, hashlib, datetime, zstandard, re
BASE = r"C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted/message"
T = "Msg_" + hashlib.md5(b"deerluna").hexdigest()
Z = zstandard.ZstdDecompressor()
def clean(s):
    s = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", s, flags=re.S)
    keep=[]
    for tag in ("title","des","url","displayname","nickname","appname","sourcedisplayname","content","plain","msg"):
        for m in re.findall(r"<%s[^>]*>(.*?)</%s>"%(tag,tag), s, flags=re.S):
            m=m.strip()
            if m and m not in keep: keep.append(m)
    if keep: return " ⟂ ".join(keep)[:300]
    return re.sub(r"<[^>]+>"," ",s).strip()[:300]
for f in sorted(glob.glob(os.path.join(BASE,"message_*.db"))):
    c=sqlite3.connect("file:"+f+"?mode=ro",uri=True)
    names=[r[0] for r in c.execute("select name from sqlite_master where type='table'")]
    if T not in names: c.close(); continue
    for ts,lt,mc,cc,ct in c.execute('select create_time,local_type,message_content,compress_content,WCDB_CT_message_content from "%s"'%T):
        main = lt & 0xFFFFFFFF
        if main not in (42,48,50): continue
        raw = mc
        if isinstance(raw,bytes):
            for cand in (raw,):
                try:
                    raw = Z.decompress(cand).decode("utf-8","ignore"); break
                except Exception:
                    try:
                        d=zstandard.ZstdDecompressor(); raw=d.decompress(cand, max_output_size=1<<22).decode("utf-8","ignore"); break
                    except Exception as e: pass
        if isinstance(raw,bytes): raw = raw.decode("utf-8","ignore")
        print("%s type=%d | %s" % (datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M"), main, clean(raw)[:200]))
    c.close()
