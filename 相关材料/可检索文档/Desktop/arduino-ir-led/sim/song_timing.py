# -*- coding: utf-8 -*-
"""看清「时长」到底是写在哪儿、又是怎么算出来的。

代码里没有直接写毫秒，只有一长串节拍数（1、0.5+0.5 之类）。
真正的毫秒是 loop() 里用 delay(400 * duration[x]) 现算的。
"""

import re

INO = (r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45"
       r"\msg\file\2026-10\buzzer-song-___-__.ino")

with open(INO, encoding="utf-8", errors="replace") as f:
    src = f.read()

def raw(name):
    m = re.search(r"\b" + name + r"\s*\[\s*\]\s*=\s*\{(.*?)\};", src, re.S)
    return re.sub(r"//[^\n]*", "", m.group(1))

tune = [x.strip() for x in raw("tune").split(",") if x.strip()]
dur  = [x.strip() for x in raw("duration").split(",") if x.strip()]

BASE = 400          # delay(400 * duration[x]) 里的那个 400

print("=" * 62)
print("前 12 个音符：代码里只存了「节拍」，毫秒是算出来的")
print("=" * 62)
print(f"{'序号':<5}{'音符(tune)':<14}{'节拍(duration)':<18}{'400 x 节拍':<12}{'实际'}")
print("-" * 62)

for x in range(min(12, len(tune))):
    d_str = dur[x] if x < len(dur) else "(越界)"
    d_val = eval(dur[x]) if x < len(dur) else 0.0
    ms    = BASE * d_val
    print(f"{x:<5}{tune[x]:<14}{d_str:<18}{'400 x ' + str(d_val):<12}{ms:.0f} ms")

print()
print("=" * 62)
print("如果节拍真的有不同的值，会是这样")
print("=" * 62)
for d, name in [(2.0, "二分音符"), (1.0, "四分音符"),
                (0.5, "八分音符"), (0.25, "十六分音符")]:
    print(f"  duration[x] = {d:<6} -> 400 x {d:<5} = {BASE*d:>4.0f} ms   ({name})")

print()
print("=" * 62)
print("原版的实际节拍值分布（所以它其实没有节奏变化）")
print("=" * 62)
from collections import Counter
for v, n in Counter(dur).most_common():
    print(f"  {v:<22} x {n:<4} = {eval(v)} 拍  = {BASE*eval(v):.0f} ms")

print()
print("=" * 62)
print("整首曲子的时间")
print("=" * 62)
total_beats = sum(eval(v) for v in dur)
print(f"duration[] 里节拍总和      : {total_beats:.0f} 拍")
print(f"按 400ms/拍 算              : {total_beats * BASE / 1000:.1f} 秒")
print(f"若 245 个音符都算 1 拍      : {len(tune) * BASE / 1000:.1f} 秒")
print(f"但实际只用到 148 个（越界前）: {len(dur) * BASE / 1000:.1f} 秒")
print()
print(f"参考：400 ms/拍 相当于 {60000 / BASE:.0f} BPM（每分钟拍数）")
print(f"      想快点就把 400 改小，比如 300 -> {60000/300:.0f} BPM")
