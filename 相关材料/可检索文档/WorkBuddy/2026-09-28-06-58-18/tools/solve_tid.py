# -*- coding: utf-8 -*-
"""反推朋友圈 tid 解码公式：用 11 条「自己发的」帖子里嵌的 epoch 做地面真值。"""
import datetime
import os
import re
import sqlite3

D = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted"
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


c = sqlite3.connect(f"file:{os.path.join(D,'sns','sns.db')}?mode=ro", uri=True)
rows = c.execute(
    "SELECT tid, content, pack_info_buf FROM SnsTimeLine WHERE user_name LIKE 'wxid_zn4ozsnn8esr21%'"
).fetchall()

pairs = []
print("=== 每条帖：tid + 嵌的 epoch ===")
for i, (tid, ct, pk) in enumerate(rows, 1):
    s = dec(ct) + " || " + dec(pk)
    nums = sorted(set(int(n) for n in re.findall(r"(?<![0-9])(1[6-9][0-9]{8})(?![0-9])", s)))
    ds = [datetime.datetime.fromtimestamp(n).strftime("%Y-%m-%d") for n in nums]
    print(f"[{i:>2}] tid={tid}  epochs={list(zip(nums, ds))}")
    if nums:
        pairs.append((tid, nums[0]))

print()
print("=== 试公式：对每组 (tid, epoch) 看哪个 N 拟合最好 ===")
for N in range(20, 45):
    errs = []
    for t, e in pairs:
        u = t % M
        v = u >> N
        errs.append(abs(v - e))
    if max(errs) < 10_000_000:
        print(f"  N={N}: 最大误差 {max(errs)} 秒  {'★精确' if max(errs) < 100000 else ''}")

print()
print("=== 试公式2：time = (u >> 32) - K，求 K ===")
ks = [((t % M) >> 32) - e for t, e in pairs]
print("  K 列表:", ks)
print("  K 均值:", sum(ks) // len(ks), " 是否恒定:", len(set(ks)) == 1)

print()
print("=== 试公式3：time = u // D，求 D ===")
for t, e in pairs[:4]:
    u = t % M
    print(f"  u={u}  e={e}  u/e={u/e:.1f}  log2={__import__('math').log2(u/e):.3f}")
