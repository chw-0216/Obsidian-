/* ============================================================================
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

#define NOTE_C0 0     // 休止符（原来写成 -1）
#define NOTE_CL1 131
#define NOTE_CL2 147
#define NOTE_CL3 165
#define NOTE_CL4 175
#define NOTE_CL5 196
#define NOTE_CL6 221
#define NOTE_CL7 248
#define NOTE_C1 262
#define NOTE_C2 294
#define NOTE_C3 330
#define NOTE_C4 350
#define NOTE_C5 393
#define NOTE_C6 441
#define NOTE_C7 495
#define NOTE_CH1 525
#define NOTE_CH2 589
#define NOTE_CH3 661
#define NOTE_CH4 700
#define NOTE_CH5 786
#define NOTE_CH6 882
#define NOTE_CH7 990

/* 音符表：放在 Flash 里，不占那宝贵的 2KB RAM */
const int tune[] PROGMEM =
{
NOTE_C0,NOTE_C0,NOTE_C0,NOTE_C5,NOTE_C3,
NOTE_C3,NOTE_C5,NOTE_C2,NOTE_C2,NOTE_C3,NOTE_C2,
NOTE_C2,NOTE_C1,NOTE_C1,NOTE_C0,NOTE_C1,NOTE_CL7,
NOTE_CL6,NOTE_CL7,NOTE_C1,NOTE_CL7,NOTE_C1,NOTE_C1,
NOTE_C2,NOTE_C3,
NOTE_C3,NOTE_C0,NOTE_C0,NOTE_C5,NOTE_C3,
NOTE_C3,NOTE_C5,NOTE_C2,NOTE_C2,NOTE_C3,NOTE_C2,
NOTE_C2,NOTE_C1,NOTE_C1,NOTE_C0,NOTE_C1,NOTE_CL7,
NOTE_CL6,NOTE_CL7,NOTE_C1,NOTE_CL7,NOTE_CL7,NOTE_C1,NOTE_C1,NOTE_C2,
NOTE_C1,NOTE_C0,NOTE_C0,NOTE_C5,NOTE_C6,NOTE_C7,
NOTE_C4,NOTE_C3,NOTE_C2,NOTE_C1,NOTE_C7,NOTE_C5,NOTE_C3,
NOTE_C3,NOTE_C5,NOTE_C2,NOTE_C2,NOTE_C3,NOTE_C2,
NOTE_C2,NOTE_C1,NOTE_C1,NOTE_C0,NOTE_C1,NOTE_CL7,
NOTE_CL6,NOTE_CL7,NOTE_C1,NOTE_CL7,NOTE_CL7,NOTE_C1,NOTE_C1,NOTE_C2,
NOTE_C3,NOTE_C0,NOTE_C0,NOTE_C5,NOTE_C3,
NOTE_C3,NOTE_C5,NOTE_CH2,NOTE_CH2,NOTE_CH1,NOTE_C7,
NOTE_C7,NOTE_CH6,NOTE_C0,NOTE_C0,NOTE_C1,NOTE_CL7,
NOTE_CL6,NOTE_CL7,NOTE_C1,NOTE_CL7,NOTE_CL7,NOTE_C1,NOTE_C1,NOTE_C2,
NOTE_C1,NOTE_C0,NOTE_C0,NOTE_C5,NOTE_C6,NOTE_C7,
NOTE_CH1,NOTE_C7,NOTE_CH1,NOTE_C7,NOTE_C6,NOTE_C5,NOTE_C6,
NOTE_C6,NOTE_C5,NOTE_C5,NOTE_C5,NOTE_C1,NOTE_C2,NOTE_C3,
NOTE_C4,NOTE_C3,NOTE_C4,NOTE_C5,NOTE_C1,NOTE_C2,NOTE_C3,
NOTE_C3,NOTE_C3,NOTE_C0,NOTE_C0,NOTE_C5,NOTE_C6,NOTE_C7,
NOTE_C1,NOTE_C7,NOTE_CH1,NOTE_CH3,NOTE_CH1,NOTE_CH2,NOTE_CH3,
NOTE_CH3,NOTE_C5,NOTE_C5,NOTE_C5,NOTE_C1,NOTE_C2,NOTE_C3,
NOTE_C4,NOTE_C3,NOTE_C4,NOTE_C3,NOTE_C2,NOTE_C2,NOTE_C1,
NOTE_CL7,NOTE_C1,NOTE_C1,NOTE_C0,NOTE_C5,NOTE_C6,NOTE_C7,
NOTE_CH1,NOTE_C7,NOTE_CH1,NOTE_CH2,NOTE_CH1,NOTE_C7,NOTE_C6,
NOTE_C6,NOTE_C5,NOTE_C0,NOTE_C0,NOTE_C1,NOTE_C2,NOTE_C3,
NOTE_C4,NOTE_C3,NOTE_C4,NOTE_C5,NOTE_C1,NOTE_C1,NOTE_C6,
NOTE_C6,NOTE_C5,NOTE_C5,NOTE_C0,NOTE_C5,NOTE_C6,NOTE_C7,
NOTE_CH1,NOTE_C7,NOTE_CH1,NOTE_CH2,NOTE_CH1,NOTE_CH2,NOTE_CH3,
NOTE_CH3,NOTE_C5,NOTE_C5,NOTE_C0,NOTE_C1,NOTE_C2,NOTE_C3,NOTE_C4,
NOTE_C4,NOTE_C3,NOTE_C4,NOTE_C5,NOTE_C1,NOTE_C2,
NOTE_C2,NOTE_C3,NOTE_C2,NOTE_C1,NOTE_C1,NOTE_C1,NOTE_C0,NOTE_C0,
NOTE_C0,NOTE_C0,NOTE_C0,NOTE_C5,NOTE_C6,NOTE_C7,
NOTE_CH1,NOTE_C7,NOTE_CH1,NOTE_C7,NOTE_C6,NOTE_C5,NOTE_C4,
NOTE_C4,NOTE_C5,NOTE_C5,NOTE_C0,NOTE_C0,
};

const int TUNE_LEN = sizeof(tune) / sizeof(tune[0]);

/* ---------------- 节奏 ---------------- */
const unsigned long BEAT_MS  = 400;   // 一拍多长，改这个就改整首曲子的快慢
const unsigned long GAP_MS   = 30;    // 音符之间的小间隔，免得连成一片
const unsigned long REPEAT_MS = 5000; // 放完停多久再来一遍

const int tonePin = 7;

void setup() {
  pinMode(tonePin, OUTPUT);
}

void loop() {
  for (int x = 0; x < TUNE_LEN; x++) {
    unsigned int freq = (unsigned int)pgm_read_word(&tune[x]);

    if (freq == 0) {                 // 休止符：安静地等一拍
      delay(BEAT_MS);
      continue;
    }

    tone(tonePin, freq);              // 发出这个音
    delay(BEAT_MS);                   // 持续一拍
    noTone(tonePin);                  // 停
    delay(GAP_MS);                    // 喘口气
  }

  delay(REPEAT_MS);                   // 停 5 秒，从头再来
}
