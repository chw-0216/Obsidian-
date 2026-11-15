# rgb_led —— RGB 三色灯高低电平循环

## 接线（就这 4 根）

| RGB 灯珠 | 接 Arduino | 中间要串什么 |
|---|---|---|
| R（红） | D9 | 220Ω 电阻 |
| G（绿） | D10 | 220Ω 电阻 |
| B（蓝） | D11 | 220Ω 电阻 |
| GND（公共脚） | GND | 无 |

- 三个颜色**各要一个电阻**，不共用。没有 220Ω 就用 330Ω / 470Ω（会暗一点）。
- **不加电阻会烧灯，也可能烧引脚。**

## 运行顺序

就是最直白的高低电平循环，全部 `digitalWrite()`，没有 PWM、没有渐变：

| 时间 | 动作 | 现象 |
|---|---|---|
| 0 ms | D9 HIGH | 红亮 500ms |
| 500 ms | D9 LOW | 红灭 300ms |
| 800 ms | D10 HIGH | 绿亮 500ms |
| 1300 ms | D10 LOW | 绿灭 300ms |
| 1600 ms | D11 HIGH | 蓝亮 500ms |
| 2100 ms | D11 LOW | 蓝灭 300ms |
| 2400 ms | 回到 D9 HIGH | 循环 |

单轮 2400ms。

- **改顺序**：调换 `loop()` 里那 6 行 `step()` 的位置。
- **改时长**：`ON_MS`（亮多久）和 `OFF_MS`（灭多久），单位毫秒。想均匀就两个值设一样。
- **共阳灯珠**：公共脚接 5V 的那种，把 `COMMON_ANODE` 改成 1。判断方法——接好后如果"该亮时灭、该灭时亮"，就是选错了。

## 文件说明

| 文件 | 作用 |
|---|---|
| `rgb_led/rgb_led.ino` | **主程序**，烧到板子里的就是它 |
| `compile.ps1` | 用本地 avr-gcc 编译，产出 hex（等价 Arduino IDE 的"验证"） |
| `upload.ps1` | 用本地 avrdude 烧录，不用开 Arduino IDE |
| `build-rgb_led/rgb_led.ino.hex` | 已编译好的固件 |
| `sim/rgb_led_sim.cpp` | PC 端逻辑模拟器，逐步验证高低电平顺序，不用接板子 |
| `sim/Arduino.h` | 模拟器用的最小 Arduino 头文件 |

## 已验证

**1) 真机工具链编译通过**（avr-gcc 7.3.0 + Arduino AVR core 1.8.8）

```
Program:    3304 bytes (10.1% Full)
Data:        207 bytes (10.1% Full)
```

**2) 逻辑模拟器全部通过**

```
==== 逐笔记录 ====
  t=     0 ms   D9  -> HIGH 亮
  t=   500 ms   D9  -> LOW  灭
  t=   800 ms   D10 -> HIGH 亮
  t=  1300 ms   D10 -> LOW  灭
  t=  1600 ms   D11 -> HIGH 亮
  t=  2100 ms   D11 -> LOW  灭
  t=  2400 ms   D9  -> HIGH 亮   （第二轮开始）

状态序列: 9h9l10h10l11h11l  (x3)

[PASS] 开头正是 D9高/D9低/D10高/D10低/D11高/D11低
[PASS] 3 轮都完整跑出了这个顺序
[PASS] 任何时刻最多只有一路是亮的
[PASS] 总时长等于 3 轮 * (亮+灭) * 3 色
[PASS] 共阴模式：LEVEL_ON=HIGH 已生效
全部通过（失败 0 项）
```

**未验证**：真机点亮效果（板子当前没插，检测不到串口）。

## 怎么烧进去（两种方式选一）

### 方式 A：Arduino IDE
1. 打开 `rgb_led/rgb_led.ino`
2. 工具 → 开发板 → Arduino Uno
3. 工具 → 端口 → 选 COM 口（拔插 USB 看哪个号变化）
4. 点"上传"

### 方式 B：用本目录的脚本
```powershell
# 1) 编译（改过程序才需要）
pwsh -File C:\Users\wardc\Desktop\arduino-ir-led\compile.ps1 `
     -Sketch C:\Users\wardc\Desktop\arduino-ir-led\rgb_led\rgb_led.ino `
     -OutDir C:\Users\wardc\Desktop\arduino-ir-led\build-rgb_led

# 2) 烧录（板子插上后）
pwsh -File C:\Users\wardc\Desktop\arduino-ir-led\upload.ps1
```

## 串口输出（9600 波特率）

```
=====================================
 RGB LED: R=D9  G=D10  B=D11  GND
 类型: 共阴 (公共脚接 GND)
 亮 500 ms / 灭 300 ms
=====================================
D9 HIGH  亮   500 ms
D9 LOW   灭   300 ms
D10 HIGH  亮   500 ms
D10 LOW   灭   300 ms
D11 HIGH  亮   500 ms
D11 LOW   灭   300 ms
```

## 上传失败怎么办

1. **串口监视器开着** → 它占用串口，关掉再传（最常见）
2. **COM 口选错** → 拔掉 USB 看哪个号消失
3. **板子型号不对** → 工具 → 开发板 选 Arduino Uno
4. **传不进去** → 按一下板子上的 RESET 键再点上传
5. **Nano 用旧 bootloader** → `upload.ps1 -Board nano`
