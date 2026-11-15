/* ============================================================================
 *  pet_sense — 桌宠感知中枢 v2
 *  ---------------------------------------------------------------------------
 *  从「红外亮灯」升级成一只桌宠的神经系统：
 *
 *    · 多传感器      红外人体(PIR) / 光敏电阻(可选) / 超声波(可选)
 *    · 四态状态机    睡觉 -> 发呆 -> 警觉 -> 陪伴，带完整转移条件
 *    · PWM 灯效      慢呼吸 / 心跳 / 快闪 / 稳定亮，四种情绪各有灯语
 *    · 非阻塞调度    全程 millis()，没有一个 delay()，随时能响应
 *    · 串口控制台    查状态、看剩余内存、锁状态、强制测试灯效
 *    · 运行统计      触发次数、陪伴时长、开机时长
 *
 *  板子: Arduino UNO / Nano (ATmega328P)
 *  日期: 2026-10-15
 *  ---------------------------------------------------------------------------
 *  【接线】
 *    红外传感器 OUT  -> D2        信号脚
 *    LED             -> D9        ★ 必须接 PWM 脚，D13 做不出呼吸灯
 *    光敏电阻分压    -> A0        USE_LDR=1 时
 *    超声波 TRIG     -> D7        USE_ULTRASONIC=1 时
 *    超声波 ECHO     -> D8
 *    蜂鸣器          -> D13       USE_BUZZER=1 时
 *
 *  【状态与情绪】
 *    SLEEP  = 打盹   没人、环境暗、超过 45 秒 -> 微光慢呼吸
 *    IDLE   = 发呆   有人但不怎么动           -> 双脉冲心跳
 *    ALERT  = 被惊动 刚检测到人的 1.5 秒内     -> 8Hz 快闪
 *    ACTIVE = 陪伴   持续有活动               -> 稳定亮 + 轻微游走
 *
 *  【串口控制台】9600 波特率，输入单字符命令：
 *    h / ?  帮助        s  状态快照       r  重置统计
 *    1..4   强制切到 SLEEP/IDLE/ALERT/ACTIVE 并锁定
 *    a      解除锁定，恢复自动    b  蜂鸣器测试
 * ==========================================================================*/

/* =========================== 功能开关（按手上的硬件裁剪）================= */
#define USE_PIR          1     // 红外人体感应
#define USE_LDR          0     // 光敏电阻（决定"环境暗才睡觉"）
#define USE_ULTRASONIC   0     // 超声波测距（注意：pulseIn 会短暂阻塞）
#define USE_BUZZER       0     // 蜂鸣器提示音
#define VERBOSE_LOG      0     // 每秒在串口打一行状态

/* =========================== 引脚 ===========































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































提前半年 ============================ */
const uint8_t PIN_PIR  = 2;
const uint8_t PIN_LED  = 9;      // PWM 脚：3/5/6/9/10/11
const uint8_t PIN_LDR  = A0;
const uint8_t PIN_TRIG = 7;
const uint8_t PIN_ECHO = 8;
const uint8_t PIN_BUZZ = 13;

/* =========================== 时序参数（毫秒）============================ */
const uint32_t T_DEBOUNCE      = 60;      // 传感器消抖窗口
const uint32_t T_ALERT_HOLD    = 1500;    // 警觉状态持续多久
const uint32_t T_ACTIVE_HOLD   = 6000;    // 人走了以后还"陪"多久
const uint32_t T_IDLE_TO_SLEEP = 45000;   // 发呆多久后睡着

/* =========================== 灯效亮度 =================================== */
const uint8_t BR_SLEEP_PEAK = 28;    // 睡觉：只留一点微光
const uint8_t BR_IDLE_PEAK  = 120;   // 发呆：心跳峰值
const uint8_t BR_ACTIVE     = 190;   // 陪伴：底亮度

/* =========================== 状态机 ===================================== */
enum PetState : uint8_t { ST_SLEEP = 0, ST_IDLE, ST_ALERT, ST_ACTIVE };

PetState state      = ST_IDLE;
uint32_t stateSince = 0;      // 进入当前状态的时刻
uint32_t lastMotion = 0;      // 最后一次检测到人的时刻
bool     holdState  = false;  // 串口锁定时暂停自动流转

uint32_t triggers   = 0;      // 累计被触发次数
uint32_t presenceMs = 0;      // 累计陪伴时长
uint32_t lastTick   = 0;      // 统计用的上一拍

/* =========================== 工具：剩余内存 ============================= */
#ifdef __AVR__
extern int __heap_start, *__brkval;
int freeRam() {
  int v;
  return (int)&v - (__brkval == 0 ? (int)&__heap_start : (int)__brkval);
}
#else
int freeRam() { return -1; }
#endif

/* =========================== 传感器 ===================================== */
#if USE_PIR
bool readPir() {
  static bool     lastRaw   = false;
  static bool     stable    = false;
  static uint32_t changedAt = 0;

  bool     raw = (digitalRead(PIN_PIR) == HIGH);
  uint32_t now = millis();

  if (raw != lastRaw) {          // 电平变了，重新计时
    lastRaw   = raw;
    changedAt = now;
  }
  if (now - changedAt >= T_DEBOUNCE) {   // 稳定够久才认
    stable = raw;
  }
  return stable;
}
#else
bool readPir() { return false; }
#endif

bool isDark() {
#if USE_LDR
  return analogRead(PIN_LDR) < 300;      // 数值越小越暗，按实际环境调
#else
  return true;                            // 没装光敏就当成"一直是暗的"
#endif
}

#if USE_ULTRASONIC
uint16_t readDistanceCm() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  uint32_t us = pulseIn(PIN_ECHO, HIGH, 25000UL);   // 25ms 超时，约 4 米
  if (us == 0) return 999;
  return (uint16_t)(us / 58UL);
}
#endif

/* =========================== 状态名 ===================================== */
const __FlashStringHelper* stateName(PetState s) {
  switch (s) {
    case ST_SLEEP:  return F("SLEEP");
    case ST_IDLE:   return F("IDLE");
    case ST_ALERT:  return F("ALERT");
    default:        return F("ACTIVE");
  }
}

/* =========================== 状态切换 =================================== */
void enterState(PetState s, uint32_t now) {
  if (s == state) return;
  state      = s;
  stateSince = now;

  Serial.print(F("[state] "));
  Serial.println(stateName(s));

#if USE_BUZZER
  switch (s) {
    case ST_ALERT:  tone(PIN_BUZZ, 1200, 80);  break;
    case ST_ACTIVE: tone(PIN_BUZZ,  880, 60);  break;
    case ST_SLEEP:  tone(PIN_BUZZ,  440, 200); break;
    default: break;
  }
#endif
}

/* =========================== 灯效（按状态算出亮度）====================== */
uint8_t computeBrightness(uint32_t now) {
  switch (state) {

    case ST_SLEEP: {                       // 4 秒一个周期的三角波呼吸
      uint32_t p   = now % 4000UL;
      uint32_t tri = (p < 2000UL) ? p : (4000UL - p);   // 0..2000
      return (uint8_t)((tri * BR_SLEEP_PEAK) / 2000UL);
    }

    case ST_IDLE: {                        // 2 秒一次"咚·咚"心跳
      uint32_t p = now % 2000UL;
      if (p < 120UL) return BR_IDLE_PEAK;
      if (p < 260UL) return 0;
      if (p < 380UL) return (uint8_t)(BR_IDLE_PEAK * 2 / 3);
      return 0;
    }

    case ST_ALERT:                         // 约 8Hz 快闪
      return ((now / 62UL) % 2UL) ? 255 : 24;

    case ST_ACTIVE:                        // 稳定亮，叠一点轻微游走
    default:
      return (uint8_t)(BR_ACTIVE + ((now / 40UL) % 16UL));
  }
}

/* =========================== 状态机推进 ================================= */
void updateStateMachine(uint32_t now) {
  bool motion = readPir();
  if (motion) lastMotion = now;

  // 陪伴时长统计：上一拍处于 ALERT/ACTIVE 就把这段时间记上
  if (state == ST_ALERT || state == ST_ACTIVE) {
    presenceMs += (now - lastTick);
  }
  lastTick = now;

  if (holdState) return;                   // 串口锁定期间不自动流转

  // 睡着或发呆时感应到人 -> 立刻警觉
  if (motion && (state == ST_SLEEP || state == ST_IDLE)) {
    triggers++;
    enterState(ST_ALERT, now);
    return;
  }

  switch (state) {
    case ST_ALERT:
      if (now - stateSince >= T_ALERT_HOLD) enterState(ST_ACTIVE, now);
      break;

    case ST_ACTIVE:
      if (now - lastMotion >= T_ACTIVE_HOLD) enterState(ST_IDLE, now);
      break;

    case ST_IDLE:
      if (isDark() && (now - lastMotion >= T_IDLE_TO_SLEEP)) {
        enterState(ST_SLEEP, now);
      }
      break;

    default: break;
  }
}

/* =========================== 串口控制台 ================================= */
void printHelp() {
  Serial.println(F("---------- commands ----------"));
  Serial.println(F("  h / ?   this help"));
  Serial.println(F("  s       status snapshot"));
  Serial.println(F("  r       reset statistics"));
  Serial.println(F("  1..4    force SLEEP / IDLE / ALERT / ACTIVE (locked)"));
  Serial.println(F("  a       unlock, resume auto"));
  Serial.println(F("  b       buzzer test"));
  Serial.println(F("------------------------------"));
}

void printStatus() {
  Serial.println(F("-------- pet_sense --------"));
  Serial.print(F("  state     : ")); Serial.println(stateName(state));
  Serial.print(F("  locked    : ")); Serial.println(holdState ? F("yes") : F("no"));
  Serial.print(F("  triggers  : ")); Serial.println(triggers);
  Serial.print(F("  presence  : ")); Serial.print(presenceMs / 1000UL); Serial.println(F(" s"));
  Serial.print(F("  uptime    : ")); Serial.print(millis() / 1000UL); Serial.println(F(" s"));
  Serial.print(F("  state age : ")); Serial.print((millis() - stateSince) / 1000UL); Serial.println(F(" s"));
  Serial.print(F("  free RAM  : ")); Serial.print(freeRam()); Serial.println(F(" bytes"));
#if USE_ULTRASONIC
  Serial.print(F("  distance  : ")); Serial.print(readDistanceCm()); Serial.println(F(" cm"));
#endif
  Serial.println(F("---------------------------"));
}

void handleConsole() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    switch (c) {

      case 'h': case '?': printHelp();   break;
      case 's':           printStatus(); break;

      case 'r':
        triggers   = 0;
        presenceMs = 0;
        Serial.println(F("stats reset"));
        break;

      case '1': holdState = true; enterState(ST_SLEEP,  millis()); break;
      case '2': holdState = true; enterState(ST_IDLE,   millis()); break;
      case '3': holdState = true; enterState(ST_ALERT,  millis()); break;
      case '4': holdState = true; enterState(ST_ACTIVE, millis()); break;

      case 'a':
        holdState  = false;
        lastMotion = millis();       // 从"现在"重新计时，避免立刻睡着
        Serial.println(F("auto mode resumed"));
        break;

      case 'b':
#if USE_BUZZER
        tone(PIN_BUZZ, 880, 150);
#else
        Serial.println(F("buzzer disabled (USE_BUZZER=0)"));
#endif
        break;

      default: break;                // 回车、换行等一律忽略
    }
  }
}

/* =========================== 初始化 ===================================== */
void setup() {
  pinMode(PIN_PIR, INPUT);
  pinMode(PIN_LED, OUTPUT);
  analogWrite(PIN_LED, 0);

#if USE_ULTRASONIC
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
#endif
#if USE_BUZZER
  pinMode(PIN_BUZZ, OUTPUT);
#endif

  Serial.begin(9600);
  Serial.println();
  Serial.println(F("=========================================="));
  Serial.println(F("  pet_sense v2  |  desk-pet sense hub"));
  Serial.println(F("=========================================="));
  Serial.print(F("  PIR : D"));  Serial.print(PIN_PIR);
  Serial.print(F("   LED : D")); Serial.println(PIN_LED);
  Serial.print(F("  features:"));
#if USE_PIR
  Serial.print(F(" PIR"));
#endif
#if USE_LDR
  Serial.print(F(" LDR"));
#endif
#if USE_ULTRASONIC
  Serial.print(F(" US"));
#endif
#if USE_BUZZER
  Serial.print(F(" BUZZ"));
#endif
  Serial.println();
  Serial.print(F("  free RAM: ")); Serial.print(freeRam()); Serial.println(F(" bytes"));
  Serial.println(F("  type 'h' for commands"));
  Serial.println(F("=========================================="));

  uint32_t now = millis();
  stateSince = now;
  lastMotion = now;
  lastTick   = now;
  state      = ST_SLEEP;              // 让 enterState 能真正执行一次
  enterState(ST_IDLE, now);
}

/* =========================== 主循环 ===================================== */
void loop() {
  uint32_t now = millis();

  handleConsole();                    // 1. 先处理人的指令
  updateStateMachine(now);            // 2. 再推进状态
  analogWrite(PIN_LED, computeBrightness(now));   // 3. 输出灯语

#if VERBOSE_LOG
  static uint32_t lastLog = 0;
  if (now - lastLog >= 1000UL) {
    lastLog = now;
    Serial.print(F("t="));   Serial.print(now / 1000UL);
    Serial.print(F("s  "));  Serial.print(stateName(state));
    Serial.print(F("  trig=")); Serial.println(triggers);
  }
#endif
}
