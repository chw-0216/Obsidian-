# 把 rgb_led 烧录到 Arduino UNO / Nano（用本地已装的 avrdude，不需要开 Arduino IDE）
# 用法:
#   pwsh -File upload.ps1                      # 自动找串口
#   pwsh -File upload.ps1 -Port COM5           # 指定串口
#   pwsh -File upload.ps1 -Board nano          # Nano 用旧 bootloader（你的是 2.31 老环境，多半是老的）
param(
  [string]$Port = '',
  [ValidateSet('uno','nano','nano-new')][string]$Board = 'uno'
)

$ErrorActionPreference = 'Stop'
$root      = $PSScriptRoot
$hex       = Join-Path $root 'build-rgb_led\rgb_led.ino.hex'
$Arduino15 = "$env:LOCALAPPDATA\Arduino15"
$Avrdude   = "$Arduino15\packages\arduino\tools\avrdude\8.0.0-arduino1\bin\avrdude.exe"
$Conf      = "$Arduino15\packages\arduino\tools\avrdude\8.0.0-arduino1\etc\avrdude.conf"

if (-not (Test-Path $hex))     { throw "找不到 $hex，请先跑 compile.ps1" }
if (-not (Test-Path $Avrdude)) { throw "找不到 avrdude: $Avrdude" }

# 板子参数
$prog = switch ($Board) {
  'uno'      { 'arduino' }
  'nano'     { 'arduino' }          # 老 Nano 的 bootloader
  'nano-new' { 'arduino' }          # 新 Nano(ATmega328P 新 bootloader) 的 avrdude 参数见下
}

# 自动找串口
if (-not $Port) {
  $ports = [System.IO.Ports.SerialPort]::GetPortNames()
  if (-not $ports -or $ports.Count -eq 0) {
    Write-Host "没有检测到串口 —— 请先用 USB 线把板子插上，装好驱动再运行。" -ForegroundColor Yellow
    Write-Host "（插上后可以看 设备管理器 -> 端口，或拔插一次看哪个 COM 号出现）"
    exit 1
  }
  if ($ports.Count -gt 1) {
    Write-Host "检测到多个串口: $($ports -join ', ')" -ForegroundColor Yellow
    Write-Host "请用 -Port 指定，例如: pwsh -File upload.ps1 -Port $($ports[0])"
    exit 1
  }
  $Port = $ports[0]
}

Write-Host "板子: $Board   串口: $Port" -ForegroundColor Cyan
Write-Host "固件: $hex"

# 新 bootloader 的 Nano 需要额外 -b 115200 且签名不同，这里给出提示
$extra = @()
if ($Board -eq 'nano-new') {
  Write-Host "提示: 新 bootloader Nano 需要 avrdude 使用 -b 115200 + 新版签名，若失败请改用 Arduino IDE 烧录。" -ForegroundColor Yellow
}

& $Avrdude -C $Conf -c $prog -p atmega328p -P $Port -b 115200 -D `
  -U "flash:w:$hex`:i" @extra

if ($LASTEXITCODE -eq 0) {
  Write-Host "`n烧录成功。灯应该马上开始：红 -> 绿 -> 蓝 -> 全灭，循环。" -ForegroundColor Green
  Write-Host "没亮的话按顺序查：1) 接线 R=D9 G=D10 B=D11 GND=GND  2) 电阻有没有串上"
  Write-Host "3) 如果是共阳灯珠，把 .ino 里 COMMON_ANODE 改成 1 重新编译烧录"
} else {
  Write-Host "`n烧录失败。常见原因：" -ForegroundColor Red
  Write-Host "  - 串口被 Arduino IDE 的串口监视器占用 -> 关掉再试"
  Write-Host "  - 板子选错 / bootloader 不匹配 -> 试 -Board nano"
  Write-Host "  - 上传时按一下板子上的 RESET 键"
}
