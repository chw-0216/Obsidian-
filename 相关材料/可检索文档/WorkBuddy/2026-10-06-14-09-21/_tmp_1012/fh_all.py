# -*- coding: utf-8 -*-
"""filehelper 全类型清单（含文件/视频），并导出到桌面。"""
import sqlite3, glob, os, re, json, datetime, shutil

DEC = os.path.expandvars(r"%LOCALAPPDATA%\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\message")
MSGFILE = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\file"
VIDEODIR = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\video"
TABLE = "Msg_9e20f478899dc29eb19741386f9343c8"
SINCE = int(datetime.datetime(2026, 9, 1).timestamp())

TYPES = {25769803825: "file", 21474836529: "link", 219043332145: "channel", 43: "video", 3: "image", 1: "text"}

try:
    import zstandard as zstd
    _Z = zstd.ZstdDecompressor()
except ImportError:
    _Z = None

def dec(blob, ctype):
    if blob is None: return ""
    if isinstance(blob, str): return blob
    raw = bytes(blob)
    if not raw: return ""
    if ctype == 4 and _Z is not None:
        try: return _Z.decompress(raw, max_output_size=1 << 26).decode("utf-8", "replace")
        except Exception: pass
    try: return raw.decode("utf-8")
    except Exception:
        if _Z is not None:
            try: return _Z.decompress(raw, max_output_size=1 << 26).decode("utf-8", "replace")
            except Exception: return ""
        return ""

def g(s, tag, d=""):
    m = re.search(r"<%s>(.*?)</%s>" % (tag, tag), s, re.S)
    return m.group(1).strip() if m else d

rows = []
for p in sorted(glob.glob(os.path.join(DEC, "message_*.db"))):
    c = sqlite3.connect(p)
    try:
        cur = c.execute(
            f"select create_time, local_type, message_content, compress_content, WCDB_CT_message_content "
            f"from {TABLE} where create_time>=? order by create_time", (SINCE,))
    except sqlite3.OperationalError:
        continue
    for ts, lt, mc, cc, ct in cur:
        s = dec(mc, ct) or dec(cc, 4)
        rows.append((ts, lt, s))
    c.close()

rows.sort()
print(f"filehelper 自 2026-09-01 起共 {len(rows)} 条")
from collections import Counter
print("类型分布:", {TYPES.get(k, k): v for k, v in Counter(r[1] for r in rows).items()})
print()

files, videos = [], []
for ts, lt, s in rows:
    t = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    if lt == 25769803825:
        files.append({"time": t, "title": g(s, "title"), "ext": g(s, "fileext"),
                      "size": int(g(s, "totallen", "0") or 0), "aeskey": g(s, "aeskey"), "md5": g(s, "md5")})
    elif lt == 43:
        videos.append({"time": t, "raw": s[:300]})

print("=== 文件类 ===")
for f in files:
    print(f"  [{f['time']}] {f['size']:>12,} B  .{f['ext']:5} {f['title']}")
print()
print("=== 视频类 ===")
for v in videos:
    a = re.search(r'aeskey="([0-9a-f]+)"', v["raw"])
    print(f"  [{v['time']}] aeskey={a.group(1)[:16] if a else '?'}")

json.dump({"files": files, "videos": videos},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fh_all.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n已导出 fh_all.json")
