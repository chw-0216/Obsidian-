# -*- coding: utf-8 -*-
"""核对 buzzer 曲子里 tune[] 和 duration[] 的元素个数是否一致。

这类"网上抄来的曲子代码"最常见的隐患：两个数组长度不匹配，
for 循环按 tune 的长度跑，读 duration 就越界了。
"""

import re

PATH = (r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45"
        r"\msg\file\2026-10\buzzer-song-___-__.ino")

with open(PATH, encoding="utf-8", errors="replace") as f:
    src = f.read()


def extract(name):
    """抓出 `name[] = { ... };` 里的元素列表"""
    m = re.search(r"\b" + name + r"\s*\[\s*\]\s*=\s*\{(.*?)\};", src, re.S)
    if not m:
        return None
    body = re.sub(r"//[^\n]*", "", m.group(1))      # 去行注释
    items = [x.strip() for x in body.split(",")]
    return [x for x in items if x]


tune = extract("tune")
dur = extract("duration")

print("=" * 58)
print("数组长度核对")
print("=" * 58)
print(f"tune[]      : {len(tune):4d} 个音符")
print(f"duration[]  : {len(dur):4d} 个节拍")

if len(tune) == len(dur):
    print("\n-> 长度一致，没问题")
else:
    d = len(tune) - len(dur)
    print(f"\n-> !! 长度不一致，tune 比 duration 多 {d} 个")
    print(f"-> for 循环跑到 x={len(dur)} 之后，duration[x] 就读到数组外面去了")

print()
print("=" * 58)
print("内存占用估算（UNO 只有 2048 字节 RAM）")
print("=" * 58)
ram_tune = len(tune) * 2          # int  = 2 字节
ram_dur = 0
for x in dur:
    # 把 0.5+0.5 这类表达式算出来，判断能塞进什么类型
    val = eval(x)
    ram_dur += 4                  # float = 4 字节
print(f"tune[]     : {len(tune)} x 2 字节 = {ram_tune} 字节")
print(f"duration[] : {len(dur)} x 4 字节 = {ram_dur} 字节")
print(f"合计       : {ram_tune + ram_dur} 字节  "
      f"(占 RAM 的 {(ram_tune + ram_dur) / 2048 * 100:.0f}%)")

print()
print("=" * 58)
print("音符频率检查")
print("=" * 58)
freqs = []
for t in tune:
    v = int(t.replace("NOTE_", "").strip()) if t.strip().lstrip("-").isdigit() else None
    if v is None:
        m = re.match(r"NOTE_(C[LH]?\d+)", t)
        if not m:
            continue
        v = {"C0": -1}.get(m.group(1))
        if v is None:
            # 去源码里找宏定义
            mm = re.search(r"#define\s+NOTE_" + m.group(1) + r"\s+(-?\d+)", src)
            v = int(mm.group(1)) if mm else None
    if v is not None:
        freqs.append(v)

if freqs:
    real = [f for f in freqs if f > 0]
    print(f"音符总数     : {len(freqs)}")
    print(f"休止符(-1)   : {freqs.count(-1)} 个")
    print(f"实际发声     : {len(real)} 个")
    print(f"最低频率     : {min(real)} Hz")
    print(f"最高频率     : {max(real)} Hz")
    print(f"音域跨度     : {max(real) - min(real)} Hz")

print()
print("=" * 58)
print("duration 里出现的所有不同写法")
print("=" * 58)
from collections import Counter
for val, n in Counter(dur).most_common():
    print(f"  {val:22s} x {n:3d}  = {eval(val)} 拍")
