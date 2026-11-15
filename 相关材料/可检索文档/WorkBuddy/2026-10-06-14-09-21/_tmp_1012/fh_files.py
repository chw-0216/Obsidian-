# -*- coding: utf-8 -*-
"""从解密原始库读 filehelper 的「文件」类消息（appmsg type=6），输出清单。"""
import sqlite3, glob, os, re, json, datetime, sys

DEC = os.path.expandvars(r"%LOCALAPPDATA%\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted")
TABLE = "Msg_9e20f478899dc29eb19741386f9343c8"   # filehelper
SINCE = int(datetime.datetime(2026, 9, 1).timestamp())

try:
    import zstandard as zstd
    D = zstd.ZstdDecompressor()
except ImportError:
    D = None

def decode(blob, ctype):
    if blob is None:
        return ""
    if isinstance(blob, str):
        return blob
    raw = bytes(blob)
    if not raw:
        return ""
    if ctype == 4 and D is not None:
        try:
            return D.decompress(raw, max_output_size=1 << 26).decode("utf-8", "replace")
        except Exception:
            pass
    try:
        return raw.decode("utf-8")
    except Exception:
        if D is not None:
            try:
                return D.decompress(raw, max_output_size=1 << 26).decode("utf-8", "replace")
            except Exception:
                return ""
        return ""

rows = []
for p in sorted(glob.glob(os.path.join(DEC, "message", "message_*.db"))):
    c = sqlite3.connect(p)
    try:
        cur = c.execute(
            f"select create_time, local_type, message_content, compress_content, "
            f"WCDB_CT_message_content from {TABLE} where create_time>=? order by create_time", (SINCE,))
    except sqlite3.OperationalError:
        continue
    for ts, lt, mc, cc, ctype in cur:
        s = decode(mc, ctype)
        if not s:
            s = decode(cc, 4)
        if "<appmsg" not in s:
            continue
        m = re.search(r"<appmsg[^>]*>\s*<type>(\d+)</type>", s)
        atype = m.group(1) if m else "?"
        t = re.search(r"<title>(.*?)</title>", s, re.S)
        title = t.group(1).strip() if t else ""
        ta = re.search(r"<totallen>(\d+)</totallen>", s)
        tot = int(ta.group(1)) if ta else 0
        fe = re.search(r"<fileext>(.*?)</fileext>", s, re.S)
        ext = fe.group(1).strip() if fe else ""
        ak = re.search(r'<aeskey>(.*?)</aeskey>', s, re.S)
        aeskey = ak.group(1).strip() if ak else ""
        rows.append((ts, atype, title, tot, ext, aeskey, len(s)))
    c.close()

rows.sort()
print(f"近 30 天 filehelper appmsg 消息: {len(rows)}")
print()
from collections import Counter
print("appmsg type 分布:", dict(Counter(r[1] for r in rows)))
print()
print("=== type=6（文件）明细 ===")
n = 0
for ts, atype, title, tot, ext, aeskey, ln in rows:
    if atype != "6":
        continue
    n += 1
    print(f"[{datetime.datetime.fromtimestamp(ts):%Y-%m-%d %H:%M}] {tot:>12,} B  {ext:6} {title}")
print(f"\n文件类共 {n} 条")

# 导出完整清单
out = []
for ts, atype, title, tot, ext, aeskey, ln in rows:
    out.append({
        "time": datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"),
        "appmsg_type": atype, "title": title, "totallen": tot,
        "fileext": ext, "aeskey": aeskey,
    })
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fh_appmsg.json"), "w", encoding="utf-8").write(
    json.dumps(out, ensure_ascii=False, indent=1))
print("已导出 fh_appmsg.json")
