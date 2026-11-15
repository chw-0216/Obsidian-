int ledPin = 3;   
int buzzer = 7;    
int val = 0;         
boolean up = true;   

unsigned long prevBreathe = 0; // 上次更新亮度的时间
unsigned long prevBeep = 0;    // 上次翻转蜂鸣器的时间
boolean beepState = LOW;       // 蜂鸣器当前电平
int breatheInterval = 20;      // 每 20ms 亮度变化一次（呼吸速度）
int halfPeriod = 10;           // 蜂鸣器方波半周期（毫秒），会随亮度改变

void setup() {
  pinMode(ledPin, OUTPUT);
  pinMode(buzzer, OUTPUT);
  Serial.begin(9600);   
}

void loop() {
  // ---- 呼吸灯部分（非阻塞定时） ----
  if (millis() - prevBreathe >= breatheInterval) {
    prevBreathe = millis();     // 刷新计时

    // 使用状态变量 up 判断方向
    if (up) {
      val++;
      if (val == 255) up = false; // 到最亮，切换方向
    } else {
      val--;
      if (val == 0) up = true;    // 到最暗，切换方向
    }

    // 亮度改变后，重新计算蜂鸣器频率（亮度越高，半周期越短，声音越尖越急促）
    halfPeriod = map(val, 0, 255, 10, 1);

    // 把亮度发到串口监视器
    Serial.println(val);
  }

  // ---- 蜂鸣器部分（根据当前 halfPeriod 翻转电平） ----
  if (millis() - prevBeep >= halfPeriod) {
    prevBeep = millis();
    beepState = !beepState;     // 翻转高/低电平
    digitalWrite(buzzer, beepState);
  }

  // ---- 输出 LED 亮度 ----
  analogWrite(ledPin, val);
}