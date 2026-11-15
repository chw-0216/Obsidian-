# -*- coding: utf-8 -*-
"""根据原始《遇见》代码，生成一个修正版：
   1. 音符表放 PROGMEM（Flash），不再吃 RAM
   2. 去掉越界的 duration[]，节拍改成统一的常量（与原作者意图一致）
   3. 休止符用 0 表示，显式跳过而不是靠 -1 出超声波
   4. 波形输出和静音分开，音符之间留一点间隔
"""

import os
import re

INO = (r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45"
       r"\msg\file\2026-10\buzzer-song-___-__.ino")
OUTDIR = r"C:\Users\wardc\Desktop\arduino-ir-led\buzzer_song_fixed"
OUT = os.path.join(OUTDIR, "buzzer_song_fixed.ino")

with open(INO, encoding="utf-8", errors="replace") as f:
    src = f.read()

# ---------- 音符宏：把原来的 -1 改成 0，语义更清楚 ----------
defs = re.findall(r"#define\s+(NOTE_\w+)\s+(-?\d+)", src)
lines = []
for name, val in defs:
    n = int(val)
    if n < 0:
        lines.append(f"#define {name} 0     // 休止符（原来写成 -1）")
    else:
        lines.append(f"#define {name} {n}")
defs_code = "\n".join(lines)

# ---------- 音符序列 ----------
m = re.search(r"\bint\s+tune\s*\[\s*\]\s*=\s*\{(.*?)\};", src, re.S)
tune_body = re.sub(r"//[^\n]*", "", m.group(1)).strip()
tune_body = re.sub(r"\n\s*\n", "\n", tune_body)

code = f"""/* ============================================================================
 *  蜂鸣器曲子（修正版）—— 原《遇见》代码的问题修复版
 *  ---------------------------------------------------------------------------
 *  相比原版改了四处：
 *    1. tune[] 放进 PROGMEM，音符表不再占用 RAM
 *    2. 删掉越界的 duration[]（原版只有 148 个，却有 245 个音符）
 *    3. 休止符改用 0，显式静音，不再依赖 tone(pin, -1) 发超声波
 *    4. 每段循环按 TUNE_LEN 走，永不会读越界
 *
 *  ★ 只能用【无源蜂鸣器】。有源蜂鸣器内置振荡电路，音高固定，
 *    再怎么改 tone() 的频率也只会发出同一个音。
 *
 *  接线：蜂鸣器正极 -> D7，负极 -> GND（有源的话串 100Ω 左右）
 * ==========================================================================*/

#include <avr/pgmspace.h>

{defs_code}

/* 音符表：放在 Flash 里，不占那宝贵的 2KB RAM */
const int tune[] PROGMEM =
{{
{tune_body}
}};

const int TUNE_LEN = sizeof(tune) / sizeof(tune[0]);

/* ---------------- 节奏 ---------------- */
const unsigned long BEAT_MS  = 400;   // 一拍多长，改这个就改整首曲子的快慢
const unsigned long GAP_MS   = 30;    // 音符之间的小间隔，免得连成一片
const unsigned long REPEAT_MS = 5000; // 放完停多久再来一遍

const int tonePin = 7;

void setup() {{
  pinMode(tonePin, OUTPUT);
}}

void loop() {{
  for (int x = 0; x < TUNE_LEN; x++) {{
    unsigned int freq = (unsigned int)pgm_read_word(&tune[x]);

    if (freq == 0) {{                 // 休止符：安静地等一拍
      delay(BEAT_MS);
      continue;
    }}

    tone(tonePin, freq);              // 发出这个音
    delay(BEAT_MS);                   // 持续一拍
    noTone(tonePin);                  // 停
    delay(GAP_MS);                    // 喘口气
  }}

  delay(REPEAT_MS);                   // 停 5 秒，从头再来
}}
"""

os.makedirs(OUTDIR, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(code)

n_notes = len([x for x in tune_body.split(",") if x.strip()])
print("generated :", OUT)
print("notes     :", n_notes)
print("rest(0)   :", tune_body.count("NOTE_C0"))
