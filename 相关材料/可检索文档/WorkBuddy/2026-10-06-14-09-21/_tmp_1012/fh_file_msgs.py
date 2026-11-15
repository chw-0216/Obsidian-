# -*- coding: utf-8 -*-
"""filehelper 文件类消息（local_type 子类型=6）精确提取。"""
import sqlite3, glob, os, re, json, datetime

DEC = os.path.expandvars(r"%LOCALAPPDATA%\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\message")
TABLE = "Msg_9e20f478899dc29eb19741386f9343c8"
FILE_TYPE = 25769803825          # 6<<32 | 49  = 文件
LINK_TYPE = 21474836529          # 5<<32 | 49  = 链接
SINCE = int(datetime.datetime(2026, 9, 1).timestamp())

try:
    import zstandard as zstd
    _Z = zstd.ZstdDecompressor()
except ImportError:
    _Z = None

def dec(blob, ctype):
    if blob is None:
        return ""
    if isinstance(blob, str):
        return blob
    raw = bytes(blob)
    if not raw:
        return ""
    if ctype == 4 and _Z is not None:
        try:
            return _Z.decompress(raw, max_output_size=1 << 26).decode("utf-8", "replace")
        except Exception:
            pass
    try:
        return raw.decode("utf-8")
    except Exception:
        if _Z is not None:
            try:
                return _Z.decompress(raw, max_output_size=1 << 26).decode("utf-8", "replace")
            except Exception:
                return ""
        return ""

def g(s, tag, default=""):
    m = re.search(r"<%s>(.*?)</%s>" % (tag, tag), s, re.S)
    return m.group(1).strip() if m else default

out = []
for p in sorted(glob.glob(os.path.join(DEC, "message_*.db"))):
    c = sqlite3.connect(p)
    try:
        cur = c.execute(
            f"select create_time, local_type, message_content, compress_content, WCDB_CT_message_content "
            f"from {TABLE} where create_time>=? and local_type in (?,?) order by create_time",
            (SINCE, FILE_TYPE, LINK_TYPE))
    except sqlite3.OperationalError:
        continue
    for ts, lt, mc, cc, ct in cur:
        s = dec(mc, ct) or dec(cc, 4)
        if not s:
            continue
        out.append({
            "ts": ts,
            "time": datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"),
            "kind": "file" if lt == FILE_TYPE else "link",
            "title": g(s, "title"),
            "desc": g(s, "des"),
            "url": g(s, "url")[:120],
            "appmsg_type": g(s, "type"),
            "totallen": int(g(s, "totallen", "0") or 0),
            "fileext": g(s, "fileext"),
            "aeskey": g(s, "aeskey"),
            "md5": g(s, "md5"),
        })
    c.close()

out.sort(key=lambda r: r["ts"])
files = [r for r in out if r["kind"] == "file"]
links = [r for r in out if r["kind"] == "link"]

print(f"近 30 天 filehelper：文件 {len(files)} 条 · 链接 {len(links)} 条\n")
print("=== 文件类明细 ===")
for r in files:
    print(f"[{r['time']}] {r['totallen']:>12,} B  .{r['fileext']:6} {r['title']}")

json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fh_file_msgs.json"),
                    "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n已导出 fh_file_msgs.json")
