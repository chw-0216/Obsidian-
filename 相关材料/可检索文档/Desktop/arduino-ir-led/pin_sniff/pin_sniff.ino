/* ============================================================================
 *  pin_sniff —— 引脚嗅探器
 *  ---------------------------------------------------------------------------
 *  用途：板子连上电脑之后，把每个引脚当前的状态打到串口，
 *        用来【推断】你接了什么、接在哪、有没有接触不良。
 *
 *  ★ 先说清楚一件事：
 *    Arduino 无法自动"识别"传感器。引脚是通用的，传感器不会自报身份。
 *    这个程序能做的，是把引脚的电平状态念给你听，由你对照判断。
 *
 *  【怎么用】
 *    1. 拔掉 D0/D1 上接的任何东西（那是串口，占用了就传不了数据）
 *    2. 烧录后打开串口监视器，波特率 9600
 *    3. 每 2 秒打一次表；用手或物体触发传感器，看哪一行跳变
 *       跳变的那一行，就是传感器接的引脚
 *
 *  板子: Arduino UNO / Nano
 * ==========================================================================*/

/* D0/D1 是串口收发，绝对不能碰，否则串口就断了 */
const uint8_t DIGITAL_PINS[] = { 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 };
const uint8_t NUM_DIGITAL    = sizeof(DIGITAL_PINS) / sizeof(DIGITAL_PINS[0]);

const uint8_t ANALOG_PINS[]  = { A0, A1, A2, A3, A4, A5 };
const uint8_t NUM_ANALOG     = sizeof(ANALOG_PINS) / sizeof(ANALOG_PINS[0]);

/* 记下上一轮的值，用来发现"跳变" */
int  lastDigital[12];
int  lastAnalog[6];
bool firstRun = true;

const unsigned long SCAN_MS = 2000;
unsigned long lastScan = 0;

void setup() {
  Serial.begin(9600);
  Serial.println();
  Serial.println(F("============================================"));
  Serial.println(F("  pin_sniff  |  引脚嗅探器"));
  Serial.println(F("============================================"));
  Serial.println(F("  D0/D1 已跳过（串口占用）"));
  Serial.println(F("  触发传感器，看哪一行跳变"));
  Serial.println();
}

void scanOnce() {
  Serial.println(F("---------------- 数字脚 ----------------"));
  Serial.println(F("脚    电平   说明"));

  for (uint8_t i = 0; i < NUM_DIGITAL; i++) {
    /* 开内部上拉：引脚悬空时会读到 HIGH，被外部拉低就读到 LOW */
    pinMode(DIGITAL_PINS[i], INPUT_PULLUP);
    delayMicroseconds(100);
    int v = digitalRead(DIGITAL_PINS[i]);

    Serial.print(F("D"));
    if (DIGITAL_PINS[i] < 10) Serial.print(' ');
    Serial.print(DIGITAL_PINS[i]);
    Serial.print(F("    "));
    Serial.print(v ? F("HIGH") : F("LOW "));
    Serial.print(F("   "));

    if (v == LOW) {
      Serial.print(F("被拉低（有东西接着）"));
    } else {
      Serial.print(F("悬空或高电平"));
    }

    if (!firstRun && v != lastDigital[i]) {
      Serial.print(F("   ** 跳变！"));
    }
    lastDigital[i] = v;
    Serial.println();
  }

  Serial.println();
  Serial.println(F("---------------- 模拟脚 ----------------"));
  Serial.println(F("脚    读数       电压"));

  for (uint8_t i = 0; i < NUM_ANALOG; i++) {
    int a = analogRead(ANALOG_PINS[i]);

    Serial.print(F("A"));
    Serial.print(i);
    Serial.print(F("    "));
    Serial.print(a);
    Serial.print(F("        "));
    Serial.print(a * 5.0 / 1023.0, 2);
    Serial.print(F(" V"));

    if (!firstRun && abs(a - lastAnalog[i]) > 8) {
      Serial.print(F("   ** 跳变！"));
    }
    lastAnalog[i] = a;
    Serial.println();
  }

  Serial.println();
  firstRun = false;
}

void loop() {
  unsigned long now = millis();
  if (now - lastScan >= SCAN_MS) {
    lastScan = now;
    scanOnce();
  }
}

/* ----------------------------------------------------------------------------
 *  怎么读这张表
 *
 *  数字脚（开了内部上拉）：
 *    HIGH   = 脚上没东西，或接的是不拉低的输出
 *    LOW    = 有东西把它拉到地（传感器输出低，或直接接了 GND）
 *    跳变   = 有信号在动  <-- 这就是你要找的脚
 *
 *  模拟脚：
 *    0 或 1023 附近 = 被拉到地 / 拉到 5V，可能是上下拉电阻
 *    中间值且会变   = 典型的模拟传感器（光敏、温度、电位器）
 *    一直乱跳       = 悬空，没接东西
 *
 *  常见传感器接法对照：
 *    红外避障 / 循迹   -> OUT 接数字脚，遮挡时电平翻转
 *    PIR 人体红外      -> OUT 接数字脚，有人时变 HIGH
 *    超声波测距        -> 两个脚（Trig 发、Echo 收）
 *    光敏 / 电位器     -> 模拟脚，数值随环境变
 *    声音传感器        -> 模拟脚，读数会跳
 * --------------------------------------------------------------------------*/
