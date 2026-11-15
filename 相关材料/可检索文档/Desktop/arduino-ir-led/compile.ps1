# 用本地已安装的 avr-gcc 工具链编译 .ino，产出 .hex（等价于 Arduino IDE 的"验证/编译"）
# 用法: pwsh -File compile.ps1 -Sketch "C:\...\rgb_led\rgb_led.ino" -OutDir "C:\...\build"
param(
  [Parameter(Mandatory=$true)][string]$Sketch,
  [Parameter(Mandatory=$true)][string]$OutDir
)

$ErrorActionPreference = 'Stop'

$Arduino15 = "$env:LOCALAPPDATA\Arduino15"
$GccBin    = "$Arduino15\packages\arduino\tools\avr-gcc\7.3.0-atmel3.6.1-arduino7\bin"
$Core      = "$Arduino15\packages\arduino\hardware\avr\1.8.8\cores\arduino"
$Variant   = "$Arduino15\packages\arduino\hardware\avr\1.8.8\variants\standard"

foreach ($p in $GccBin, $Core, $Variant) { if (-not (Test-Path $p)) { throw "缺少路径: $p" } }

$gcc  = "$GccBin\avr-gcc.exe"
$objcopy = "$GccBin\avr-objcopy.exe"
$size = "$GccBin\avr-size.exe"

New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
$name = [IO.Path]::GetFileNameWithoutExtension($Sketch)
$cpp  = Join-Path $OutDir "$name.ino.cpp"

# ---- 1) .ino -> .cpp：只用 C 预处理器，把 #include 展开，避免手写函数顺序问题
& $gcc -E -CC -x c++ -mmcu=atmega328p -DF_CPU=16000000L -DARDUINO=10819 `
      -DARDUINO_AVR_UNO -DARDUINO_ARCH_AVR `
      "-I$Core" "-I$Variant" $Sketch -o $cpp
if ($LASTEXITCODE -ne 0) { throw "预处理失败" }
# 去掉 #line 指令，让报错行号对得上原 .ino
# 再补上 Arduino.h —— 对应 Arduino IDE 自动给 .ino 加的那一行
$clean = (Get-Content $cpp) | Where-Object { $_ -notmatch '^#\s*line\s' }
Set-Content -Path $cpp -Value (@('#include <Arduino.h>') + $clean) -Encoding UTF8

# ---- 2) 编译
$cflags = @(
  '-c','-g','-Os','-w','-std=gnu++11','-fpermissive','-fno-exceptions','-ffunction-sections',
  '-fdata-sections','-fno-threadsafe-statics','-flto','-mmcu=atmega328p','-DF_CPU=16000000L',
  '-DARDUINO=10819','-DARDUINO_AVR_UNO','-DARDUINO_ARCH_AVR',
  "-I$Core","-I$Variant"
)
& $gcc @cflags $cpp -o (Join-Path $OutDir "$name.ino.o")
if ($LASTEXITCODE -ne 0) { throw "编译 .ino 失败" }

$coreObjs = @()
foreach ($src in Get-ChildItem "$Core\*.c","$Core\*.cpp" -ErrorAction SilentlyContinue) {
  $o = Join-Path $OutDir ("core_" + $src.BaseName + ".o")
  if ($src.Extension -eq '.c') { & $gcc @cflags -x c $src.FullName -o $o } else { & $gcc @cflags $src.FullName -o $o }
  if ($LASTEXITCODE -ne 0) { throw "编译 core 失败: $($src.Name)" }
  $coreObjs += $o
}

# ---- 3) 链接
$elf = Join-Path $OutDir "$name.ino.elf"
$ldflags = @(
  '-w','-Os','-flto','-fuse-linker-plugin','-Wl,--gc-sections','-mmcu=atmega328p',
  '-o', $elf, (Join-Path $OutDir "$name.ino.o")
) + $coreObjs + @('-lm')
& $gcc @ldflags
if ($LASTEXITCODE -ne 0) { throw "链接失败" }

# ---- 4) 生成 hex
& $objcopy -O ihex -j .text -j .data $elf (Join-Path $OutDir "$name.ino.hex")
& $objcopy -O ihex -j .eeprom --set-section-flags=.eeprom=alloc,load --no-change-warnings `
           --change-section-lma .eeprom=0 $elf (Join-Path $OutDir "$name.ino.eep")
if ($LASTEXITCODE -ne 0) { throw "生成 hex 失败" }

Write-Host "`n===== 编译成功 =====" -ForegroundColor Green
& $size -C --mcu=atmega328p $elf
Write-Host "`n产物:"
Get-ChildItem $OutDir -Include "$name.ino.hex","$name.ino.elf","$name.ino.eep" -ErrorAction SilentlyContinue |
  Select-Object Name, Length | Format-Table -AutoSize
