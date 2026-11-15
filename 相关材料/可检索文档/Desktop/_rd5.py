import sqlite3, hashlib, os, sys, io, glob, re
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
MY_ROOT="wxid_zn4ozsnn8esr21"; TALKER="deerluna"
DEC=os.path.expandvars(r"%LOCALAPPDATA%\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted")
import zstandard as zstd
_D=zstd.ZstdDecompressor()
def dec(b):
    if b is None: return ""
    if isinstance(b,str): return b
    try: return _D.decompress(bytes(b),max_output_size=1<<24).decode("utf-8","replace")
    except Exception:
        try: return bytes(b).decode("utf-8")
        except Exception: return ""
def render(lt,t):
    t=t or ""
    if lt==3 or t.startswith("<img"): return "【图片】"
    if lt==34: return "【语音】"
    if lt==43: return "【视频】"
    if lt==49 or "<appmsg" in t:
        m=re.search(r"<title>(.*?)</title>",t,re.S)
        return f"【引用/文件】{(m.group(1).strip() if m else '')[:60]}"
    if lt==10000: return "〔系统〕"+re.sub(r"<[^>]{0,200}>"," ",t)[:80]
    s=re.sub(r"<[^>]{0,400}>"," ",t)
    return re.sub(r"\s+"," ",s).strip()[:300]
tab="Msg_"+hashlib.md5(TALKER.encode()).hexdigest()
rows=[]
for dbf in sorted(glob.glob(os.path.join(DEC,"**","*.db"),recursive=True)):
    try:
        c=sqlite3.connect(f"file:{dbf}?mode=ro",uri=True)
        if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(tab,)).fetchone():
            c.close(); continue
        idmap={r[0]:(r[1] or "") for r in c.execute("SELECT rowid,user_name FROM Name2Id")}
        for lid,ts,rsid,lt,blob in c.execute(f'SELECT local_id,create_time,real_sender_id,local_type,message_content FROM "{tab}"'):
            who=idmap.get(rsid,"") if rsid else ""
            rows.append((int(ts),int(lid),1 if who.startswith(MY_ROOT) else 0,int(lt or 0),dec(blob)))
        c.close()
    except Exception: pass
rows.sort(key=lambda r:(r[0],r[1]))
seen=set(); out=[]
for r in rows:
    k=(r[0],r[1])
    if k in seen: continue
    seen.add(k); out.append(r)
cut = datetime(2026,10,26,18,30)
print(f"总 {len(out)} 条，最新 {datetime.fromtimestamp(out[-1][0]).strftime('%Y-%m-%d %H:%M:%S')}")
print("-"*70)
for ts,lid,isd,lt,raw in out:
    d = datetime.fromtimestamp(ts)
    if d < cut: continue
    print(f"[{d.strftime('%m-%d %H:%M')}] {'我' if isd else '她'}: {render(lt,raw)}")
