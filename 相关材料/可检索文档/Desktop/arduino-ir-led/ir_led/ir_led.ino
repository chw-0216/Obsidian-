/* ============================================================================
 *  红外感应亮灯  |  IR Sensor -> LED
 *  板子: Arduino UNO / Nano (ATmega328P)
 *  日期: 2026-10-15
 * ----------------------------------------------------------------------------
 *  【接线】
 *
 *    红外传感器            Arduino UNO
 *      VCC  ---------------  5V
 *      GND  ---------------  GND
 *      OUT  ---------------  D2
 *
 *    LED（板载 D13 已有一颗，外接可选）
 *      长脚(+) --- 220Ω --- D13
 *      短脚(-) ----------- GND
 *
 *  【传感器类型】最常见的两种，改下面 IR_ACTIVE_HIGH 一个值就能切换：
 *    HC-SR501 人体红外(PIR)    有人时输出【高】电平  ->  IR_ACTIVE_HIGH = 1
 *    红外避障 / 循迹模块        有障碍时输出【低】电平 ->  IR_ACTIVE_HIGH = 0
 *
 *  【三种运行模式】
 *    正常模式     接好线直接烧录，人靠近 -> 灯亮，离开 3 秒后 -> 灯灭
 *    DEMO_MODE=1  不接任何传感器，灯自动每 2 秒亮一次（"假装能用"模式）
 *    串口监视器   9600 波特率，能看到每次触发/熄灭的时间戳
 * ==========================================================================*/

// ----------------------------- 可调参数 -----------------------------------

// 传感器触发电平：1 = 高电平触发(PIR)，0 = 低电平触发(避障/循迹模块)
#define IR_ACTIVE_HIGH   1

// 信号消失后延时多久关灯（毫秒）。PIR 模块本身也有旋钮可调。
#define HOLD_MS          3000UL

// 演示模式：不用接传感器，灯会自己闪，方便先看效果。要用真传感器就改成 0
#define DEMO_MODE        0

// 引脚
const uint8_t PIN_IR  = 2;    // 红外传感器 OUT
const uint8_t PIN_LED = 13;   // LED（板载 + 外接）

// ----------------------------- 内部状态 -----------------------------------

unsigned long lastTriggerMs = 0;   // 最近一次检测到信号的时间
bool          ledOn         = false;

// ----------------------------- 读传感器 -----------------------------------

bool irTriggered() {
#if DEMO_MODE
  // 没接传感器时的假信号：每 2 秒"触发"一次，触发 1 秒
  return (millis() % 2000UL) < 1000UL;
#else
  bool level = (digitalRead(PIN_IR) == HIGH);
  return IR_ACTIVE_HIGH ? level : !level;
#endif
}

// ----------------------------- 初始化 -------------------------------------

void setup() {
  pinMode(PIN_IR, INPUT);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);

  Serial.begin(9600);
  Serial.println(F("====================================="));
  Serial.println(F(" IR -> LED ready"));
#if DEMO_MODE
  Serial.println(F(" MODE: DEMO (no sensor needed)"));
#else
  Serial.print(F(" MODE: LIVE, active "));
  Serial.println(IR_ACTIVE_HIGH ? F("HIGH") : F("LOW"));
#endif
  Serial.print(F(" HOLD: "));
  Serial.print(HOLD_MS);
  Serial.println(F(" ms"));
  Serial.println(F("====================================="));
}

// ----------------------------- 主循环 -------------------------------------

void loop() {
  unsigned long now = millis();

  // 1) 检测到红外信号 -> 亮灯（并在串口报一次）
  if (irTriggered()) {
    lastTriggerMs = now;
    if (!ledOn) {
      ledOn = true;
      digitalWrite(PIN_LED, HIGH);
      Serial.print(F("["));
      Serial.print(now);
      Serial.println(F(" ms] >> IR detected  -> LED ON"));
    }
  }

  // 2) 信号消失并超过保持时间 -> 关灯
  if (ledOn && (now - lastTriggerMs >= HOLD_MS)) {
    ledOn = false;
    digitalWrite(PIN_LED, LOW);
    Serial.print(F("["));
    Serial.print(now);
    Serial.println(F(" ms] << no signal    -> LED OFF"));
  }
}

/* ----------------------------------------------------------------------------
 *  串口监视器预期输出（DEMO_MODE=1 时）：
 *
 *  =====================================
 *   IR -> LED ready
 *   MODE: DEMO (no sensor needed)
 *   HOLD: 3000 ms
 *  =====================================
 *  [1000 ms] >> IR detected  -> LED ON
 *  [4000 ms] << no signal    -> LED OFF
 *  [5000 ms] >> IR detected  -> LED ON
 *  [8000 ms] << no signal    -> LED OFF
 * --------------------------------------------------------------------------*/
