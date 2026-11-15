# -*- coding: utf-8 -*-
"""朋友圈最终导出：正确公式 ts_ms = (tid & 0xFFFFFFFFFFFFFFFF) >> 23
（低 23 位=序号，高 41 位=毫秒时间戳）"""
import datetime
import os
import re
import sqlite3

D = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted"
ME = "wxid_zn4ozsnn8esr21"
M = 1 << 64


def dec(b):
    if b is None:
        return ""
    if isinstance(b, str):
        return b
    raw = bytes(b)
    try:
        import zstandard as zstd
        raw = zstd.ZstdDecompressor().decompress(raw, max_output_size=1 << 24)
    except Exception:
        pass
    return raw.decode("utf-8", "ignore")


def tid_ts(tid):
    return ((tid % M) >> 23) / 1000.0


def clean(s):
    s = re.sub(r"<[^>]{0,100}>", " ", s)
    s = re.sub(r"https?://\S+", " ", s)
    s = re.sub(r"[\x00-\x1f]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


c = sqlite3.connect(f"file:{os.path.join(D,'sns','sns.db')}?mode=ro", uri=True)
rows = c.execute(
    "SELECT tid, content, pack_info_buf FROM SnsTimeLine WHERE user_name LIKE ?", (ME + "%",)
).fetchall()

recs = []
for tid, ct, pk in rows:
    ts = tid_ts(tid)
    body = clean(dec(ct))
    frags = [f.strip() for f in re.findall(r"[\u4e00-\u9fff][^<>\x00-\x1f]{1,140}", body)]
    frags = [f for f in frags if len(f) >= 2]
    recs.append((ts, frags))
recs.sort()

print("=" * 80)
print("他自己发的朋友圈（正确解码，共 %d 条）" % len(recs))
print("=" * 80)
for i, (ts, frags) in enumerate(recs, 1):
    dt = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    print(f"\n[{i:>2}] {dt}")
    # 只保留「人话」片段（过滤纯数字/协议串）
    good = [f for f in frags if len(re.sub(r"[\d\s]", "", f)) >= 3][:5]
    for f in good:
        print(f"      · {f[:130]}")
    if not good:
        print("      (无配文 · 纯图片/视频)")

print("\n" + "=" * 80)
print("按月分布")
print("=" * 80)
from collections import Counter
mm = Counter(datetime.datetime.fromtimestamp(ts).strftime("%Y-%m") for ts, _ in recs)
for k in sorted(mm):
    print(f"   {k}  {'█'*mm[k]}  {mm[k]} 条")
print("\n年份:", Counter(datetime.datetime.fromtimestamp(ts).year for ts, _ in recs))
c.close()
