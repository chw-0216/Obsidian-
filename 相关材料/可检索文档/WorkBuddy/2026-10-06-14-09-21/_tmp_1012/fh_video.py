# -*- coding: utf-8 -*-
"""filehelper 视频导出（按字节数精确匹配 msg/video）。"""
import os, re, sqlite3, glob, datetime, shutil, json

DEC = os.path.expandvars(r"%LOCALAPPDATA%\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\message")
MSVIDEO = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\video"
OUT = r"C:\Users\wardc\Desktop\文件传输助手_导出_2026-10-12\03_视频_2026-09至10"
TABLE = "Msg_9e20f478899dc29eb19741386f9343c8"
SINCE = int(datetime.datetime(2026, 9, 1).timestamp())

os.makedirs(OUT, exist_ok=True)

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

# 视频池：字节数 -> 路径
pool = {}
for m in sorted(os.listdir(MSVIDEO)):
    d = os.path.join(MSVIDEO, m)
    if not os.path.isdir(d):
        continue
    for f in os.listdir(d):
        if f.endswith(".mp4") and "_raw" not in f:
            p = os.path.join(d, f)
            pool.setdefault(os.path.getsize(p), []).append(p)
print(f"视频池: {len(pool)} 个不同字节数")

rows = []
for p in sorted(glob.glob(os.path.join(DEC, "message_*.db"))):
    c = sqlite3.connect(p)
    try:
        cur = c.execute(f"select create_time, message_content, compress_content, WCDB_CT_message_content "
                        f"from {TABLE} where create_time>=? and local_type=43 order by create_time", (SINCE,))
    except sqlite3.OperationalError:
        continue
    for ts, mc, cc, ct in cur:
        s = dec(mc, ct) or dec(cc, 4)
        if not s:
            continue
        ln = re.search(r'(?<![A-Za-z])length="(\d+)"', s)
        pl = re.search(r'playlength="(\d+)"', s)
        rows.append((ts, int(ln.group(1)) if ln else 0, int(pl.group(1)) if pl else 0))
    c.close()

rows.sort()
print()
ok = 0
for ts, ln, pl in rows:
    t = datetime.datetime.fromtimestamp(ts)
    src = None
    for cand in pool.get(ln, []):
        src = cand; break
    if src:
        dst = os.path.join(OUT, f"{t:%Y-%m-%d_%H%M}_{pl}秒_{os.path.basename(src)}")
        shutil.copy2(src, dst)
        ok += 1
        print(f"OK  [{t:%Y-%m-%d %H:%M}] {pl:>3}秒 {ln:>10,} B -> {os.path.basename(dst)}")
    else:
        print(f"MISS[{t:%Y-%m-%d %H:%M}] {pl:>3}秒 {ln:>10,} B  (池中无此字节数)")
print(f"\n匹配 {ok}/{len(rows)}")
