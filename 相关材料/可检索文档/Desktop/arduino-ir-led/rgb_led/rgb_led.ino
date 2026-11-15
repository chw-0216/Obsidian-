/* ============================================================================
 *  rgb_led —— RGB 三色灯高低电平循环
 *  ---------------------------------------------------------------------------
 *  板子: Arduino UNO / Nano (ATmega328P)
 *  日期: 2026-10-16
 * ---------------------------------------------------------------------------
 *  【接线】RGB 灯珠 4 个脚：R、G、B、GND
 *
 *      RGB 灯珠脚位          接哪里
 *      ------------------    ----------------------------------
 *      R  (红)   ---------   D9   （中间串 220Ω 电阻）
 *      G  (绿)   ---------   D10  （中间串 220Ω 电阻）
 *      B  (蓝)   ---------   D11  （中间串 220Ω 电阻）
 *      GND(公共) ---------   Arduino 的 GND
 *
 *  ★ 三个颜色各要一个电阻，不共用。不加电阻会烧灯、也可能烧引脚。
 *    没有 220Ω 就用 330Ω / 470Ω，只是暗一点。
 *
 * ---------------------------------------------------------------------------
 *  【运行顺序】就是你说的那种：
 *
 *      D9  HIGH  红亮
 *      D9  LOW   红灭
 *      D10 HIGH  绿亮
 *      D10 LOW   绿灭
 *      D11 HIGH  蓝亮
 *      D11 LOW   蓝灭
 *      （循环）
 *
 *  全部用 digitalWrite()，只有"高"和"低"两种状态，没有 PWM、没有渐变。
 *
 *  【改顺序】把 loop() 里那 6 个 step() 调换位置就行，比如蓝->绿->红。
 *  【改时长】ON_MS 是"亮多久"，OFF_MS 是"灭多久"，单位毫秒。
 *  【共阳灯珠】如果公共脚接的是 5V（不是 GND），把 COMMON_ANODE 改成 1。
 *             接好后发现"该亮时灭、该灭时亮"，就是选错了这个值。
 * ==========================================================================*/

// ----------------------------- 可调参数 -----------------------------------

// 1 = 共阳（公共脚接 5V，低电平点亮）；0 = 共阴（公共脚接 GND，高电平点亮）
#define COMMON_ANODE     0

const uint16_t ON_MS  = 500;    // 每个颜色亮多久
const uint16_t OFF_MS = 300;    // 每个颜色灭多久 —— 想均匀就改成和 ON_MS 一样

// 只做展示、不接灯也能跑（串口照样打印）。1 = 打开
#define DEMO_MODE        0

// ----------------------------- 引脚定义 -----------------------------------

const uint8_t PIN_R = 9;    // 红
const uint8_t PIN_G = 10;   // 绿
const uint8_t PIN_B = 11;   // 蓝

// ----------------------------- 内部逻辑 -----------------------------------

// "亮"对应的高/低电平。共阳是反的，所以这里换算一次，后面都不管极性问题。
#if COMMON_ANODE
  const uint8_t LEVEL_ON  = LOW;
  const uint8_t LEVEL_OFF = HIGH;
#else
  const uint8_t LEVEL_ON  = HIGH;
  const uint8_t LEVEL_OFF = LOW;
#endif

// 一步：把某个引脚置成指定电平，等一段时间，并在串口报一次
void step(uint8_t pin, uint8_t level, uint16_t waitMs) {
  digitalWrite(pin, level);

  if (DEMO_MODE == 0) {
    Serial.print(F("D"));
    Serial.print(pin);
    Serial.print(level == LEVEL_ON ? F(" HIGH  亮") : F(" LOW   灭"));
    Serial.print(F("   "));
    Serial.print(waitMs);
    Serial.println(F(" ms"));
  }

  delay(waitMs);
}

// 整组三个引脚全灭
void allOff() {
  digitalWrite(PIN_R, LEVEL_OFF);
  digitalWrite(PIN_G, LEVEL_OFF);
  digitalWrite(PIN_B, LEVEL_OFF);
}

// ----------------------------- 初始化 -------------------------------------

void setup() {
  pinMode(PIN_R, OUTPUT);
  pinMode(PIN_G, OUTPUT);
  pinMode(PIN_B, OUTPUT);
  allOff();                      // 上电先全灭，避免乱亮

  Serial.begin(9600);
  Serial.println(F("====================================="));
  Serial.println(F(" RGB LED: R=D9  G=D10  B=D11  GND"));
  Serial.println(COMMON_ANODE ? F(" 类型: 共阳 (公共脚接 5V)") : F(" 类型: 共阴 (公共脚接 GND)"));
  Serial.print(F(" 亮 "));
  Serial.print(ON_MS);
  Serial.print(F(" ms / 灭 "));
  Serial.print(OFF_MS);
  Serial.println(F(" ms"));
  Serial.println(F("====================================="));
}

// ----------------------------- 主循环 -------------------------------------

void loop() {
  // 想改顺序就调换下面 6 行的位置
  step(PIN_R, LEVEL_ON,  ON_MS);    // D9  HIGH  红亮
  step(PIN_R, LEVEL_OFF, OFF_MS);   // D9  LOW   红灭

  step(PIN_G, LEVEL_ON,  ON_MS);    // D10 HIGH  绿亮
  step(PIN_G, LEVEL_OFF, OFF_MS);   // D10 LOW   绿灭

  step(PIN_B, LEVEL_ON,  ON_MS);    // D11 HIGH  蓝亮
  step(PIN_B, LEVEL_OFF, OFF_MS);   // D11 LOW   蓝灭
}

/* ----------------------------------------------------------------------------
 *  串口监视器预期输出（9600 波特率）：
 *
 *  =====================================
 *   RGB LED: R=D9  G=D10  B=D11  GND
 *   类型: 共阴 (公共脚接 GND)
 *   亮 500 ms / 灭 300 ms
 *  =====================================
 *  D9 HIGH  亮   500 ms
 *  D9 LOW   灭   300 ms
 *  D10 HIGH  亮   500 ms
 *  D10 LOW   灭   300 ms
 *  D11 HIGH  亮   500 ms
 *  D11 LOW   灭   300 ms
 *  D9 HIGH  亮   500 ms
 *  ...
 * --------------------------------------------------------------------------*/
