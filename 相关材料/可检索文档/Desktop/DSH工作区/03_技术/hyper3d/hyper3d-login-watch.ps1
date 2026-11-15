# Hyper3D CLI 设备授权看守脚本
# 作用：在后台持续持有 hyper3d auth login 的授权窗口，直到授权完成或超时。
# 位置约定：本脚本属技术脚本，归 03_技术/hyper3d/。
#
# 用法：
#   pwsh -File hyper3d-login-watch.ps1                 # 默认 18 分钟内等待授权
#   pwsh -File hyper3d-login-watch.ps1 -MaxMinutes 5   # 自定义等待时长
#
# 安全约定：脚本只落地 CLI 自身打印的授权码与链接，不读取、不写入、不回显任何
# token 或凭据；凭据由 CLI 自己保存到工作区之外的位置。

param(
  [int]$MaxMinutes = 18,
  [int]$PollSeconds = 15
)

$ErrorActionPreference = 'Continue'
$cliDir = 'C:\Users\wardc\Documents\New project gpt\AI-archive\apps\hyper3d-cli'
$cli    = Join-Path $cliDir 'hyper3d.cmd'
$logDir = $PSScriptRoot
$outLog = Join-Path $logDir 'hyper3d-login.out.log'
$errLog = Join-Path $logDir 'hyper3d-login.err.log'

if (-not (Test-Path $cli)) { Write-Host "找不到 CLI: $cli" -ForegroundColor Red; exit 1 }
foreach ($f in @($outLog, $errLog)) { if (Test-Path $f) { Remove-Item $f -Force } }

Write-Host "[watcher] 启动 hyper3d auth login --no-browser"
$proc = Start-Process -FilePath $cli -ArgumentList 'auth','login','--no-browser' `
  -WorkingDirectory $cliDir -NoNewWindow -PassThru `
  -RedirectStandardOutput $outLog -RedirectStandardError $errLog

# 判定是否已授权。
# 注意：未授权时 `auth status --output json` 返回的是 {"authenticated": false}，
# 而非人类可读的 "Not authenticated"，所以必须解析 JSON，不能用字符串包含判断。
function Test-Hyper3dAuthed {
  param([string]$StatusText)
  try {
    $obj = $StatusText | ConvertFrom-Json -ErrorAction Stop
    if ($obj -is [System.Management.Automation.PSCustomObject]) {
      return [bool]$obj.authenticated
    }
  } catch { }
  # 解析失败时退回保守判断：只有出现明确的未授权字样才算未授权
  return ($StatusText -notmatch 'Not authenticated|"authenticated"\s*:\s*false')
}

$deadline  = (Get-Date).AddMinutes($MaxMinutes)
$announced = $false
$authed    = $false

while ((Get-Date) -lt $deadline) {
  if (-not $announced -and (Test-Path $errLog) -and (Get-Item $errLog).Length -gt 0) {
    Start-Sleep -Milliseconds 500
    Write-Host "[watcher] === 授权信息（请在浏览器输入下面的码） ===" -ForegroundColor Cyan
    Get-Content $errLog -Raw | Write-Host
    Write-Host "[watcher] ==========================================" -ForegroundColor Cyan
    $announced = $true
  }

  $status = & $cli auth status --output json 2>&1 | Out-String
  if (Test-Hyper3dAuthed -StatusText $status) {
    Write-Host "[watcher] 授权成功，auth status 返回：" -ForegroundColor Green
    Write-Host $status
    $authed = $true
    break
  }

  if ($proc.HasExited) {
    Write-Host "[watcher] login 进程已退出，退出码 $($proc.ExitCode)。" -ForegroundColor Yellow
    Write-Host "--- stdout ---"; if (Test-Path $outLog) { Get-Content $outLog -Raw | Write-Host }
    Write-Host "--- stderr ---"; if (Test-Path $errLog) { Get-Content $errLog -Raw | Write-Host }
    break
  }

  Start-Sleep -Seconds $PollSeconds
}

if (-not $authed) {
  Write-Host "[watcher] 未在时限内确认授权。若授权码已过期，请重新运行本脚本获取新码。" -ForegroundColor Red
  if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
  exit 2
}

Write-Host "[watcher] 可以开始生成任务了。" -ForegroundColor Green
exit 0
