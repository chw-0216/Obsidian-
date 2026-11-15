# 一键更新「笑一」聊天记录
# 用法：双击同目录的 一键更新聊天记录.bat，或 PowerShell 运行本脚本。
# 原理：临时开启 WeFlow HTTP API → 分页拉取全部消息 → 覆盖写入 01_最新聊天记录 → 关闭 API。
# 输出目录自动定位到本脚本所在文件夹，移动整个「笑一」文件夹也不受影响。

$ErrorActionPreference = 'Stop'
$exe      = 'C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeFlow\app\WeFlow.exe'
$cfg      = 'C:\Users\wardc\AppData\Roaming\WeFlow\WeFlow-config.json'
$outDir   = Join-Path $PSScriptRoot '01_最新聊天记录'
$talker   = 'wxid_wdnk6ue9kiyn22'   # 笑一
$display  = '笑一'
$myWxid   = 'wxid_zn4ozsnn8esr21'   # 你自己
$port     = 5031

$typeMap = @{1='文本';3='图片';34='语音';42='名片';43='视频';47='表情';48='位置';49='链接/卡片';50='语音通话';51='视频通话';10000='系统'}

function Read-Config { return [System.IO.File]::ReadAllText($cfg) }
function Write-Config($text) { $utf8 = New-Object System.Text.UTF8Encoding($false); [System.IO.File]::WriteAllText($cfg, $text, $utf8) }

function Edit-Config($enabled, $token) {
  $raw = Read-Config
  $raw = $raw -replace '"httpApiEnabled"\s*:\s*(true|false)', ('"httpApiEnabled": ' + $(if($enabled){'true'}else{'false'}))
  $raw = $raw -replace '"httpApiToken"\s*:\s*"[^"]*"', ('"httpApiToken": "' + $token + '"')
  Write-Config $raw
}

function Start-WeFlow {
  Get-Process -Name WeFlow -ErrorAction SilentlyContinue | Stop-Process -Force
  Start-Sleep -Seconds 2
  Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe)
  Start-Sleep -Seconds 22
}

function Get-BaseType($t) { $v = [int64]$t; if ($v -gt 4294967295) { return $v % 4294967296 } else { return $v } }
function Get-TypeLabel($t) {
  $b = Get-BaseType $t
  $name = $typeMap[[int]$b]
  if (-not $name) { $name = ('类型' + [int]$b) }
  if ([int64]$t -gt 4294967295) { $name = '引用·' + $name }
  return $name
}
function Get-Fmt($ts) { return ([DateTimeOffset]::FromUnixTimeSeconds([int64]$ts)).LocalDateTime.ToString('yyyy-MM-dd HH:mm:ss') }

Write-Host '============================================' -ForegroundColor Cyan
Write-Host '  一键更新笑一聊天记录' -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan

# 1) 保存原 API 状态，启用
$orig = Read-Config
$origEnabled = if ($orig -match '"httpApiEnabled"\s*:\s*true') { $true } else { $false }
$token = 'wf-' + [guid]::NewGuid().ToString('N')
Write-Host '[1/5] 启用 HTTP API ...' -ForegroundColor Yellow
Edit-Config $true $token

# 2) 重启 WeFlow
Write-Host '[2/5] 重启 WeFlow，等待 22s ...' -ForegroundColor Yellow
Start-WeFlow

# 3) 分页拉取
Write-Host '[3/5] 分页拉取消息 ...' -ForegroundColor Yellow
$headers = @{ Authorization = "Bearer $token" }
$all = @()
$offset = 0
do {
  $url = "http://127.0.0.1:$port/api/v1/messages?talker=$talker&limit=10000&offset=$offset&format=json"
  $j = Invoke-RestMethod -Uri $url -Headers $headers -TimeoutSec 120
  $msgs = @($j.messages)
  $all += $msgs
  Write-Host ("      offset={0}: +{1}, hasMore={2}" -f $offset, $msgs.Count, $j.hasMore)
  $offset += $msgs.Count
  if (-not $j.hasMore -or $msgs.Count -eq 0) { break }
} while ($true)

# 反转成时间正序
[array]::Reverse($all)
Write-Host ("      共 {0} 条消息" -f $all.Count) -ForegroundColor Green

# 4) 写文件
Write-Host '[4/5] 写入 json / md / txt ...' -ForegroundColor Yellow
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }

$jsonObj = [ordered]@{
  talker = $talker; displayName = $display; myWxid = $myWxid
  exportedAt = (Get-Date).ToString('o'); totalCount = $all.Count; messages = $all
}
$jsonObj | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $outDir '笑一-聊天记录.json') -Encoding UTF8

$sbMd = New-Object System.Text.StringBuilder
[void]$sbMd.AppendLine("# 与「$display」的聊天记录")
[void]$sbMd.AppendLine("")
[void]$sbMd.AppendLine("- 对方 wxid：``$talker``")
[void]$sbMd.AppendLine("- 消息总数：$($all.Count)")
[void]$sbMd.AppendLine("- 导出时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
if ($all.Count -gt 0) {
  [void]$sbMd.AppendLine("- 时间范围：$(Get-Fmt $all[0].createTime) ~ $(Get-Fmt $all[-1].createTime)")
}
[void]$sbMd.AppendLine("")
[void]$sbMd.AppendLine("---")
[void]$sbMd.AppendLine("")

$sbTxt = New-Object System.Text.StringBuilder
[void]$sbTxt.AppendLine("与「$display」的聊天记录（共 $($all.Count) 条）")
if ($all.Count -gt 0) { [void]$sbTxt.AppendLine("时间范围：$(Get-Fmt $all[0].createTime) ~ $(Get-Fmt $all[-1].createTime)") }
[void]$sbTxt.AppendLine(('=' * 50))
[void]$sbTxt.AppendLine("")

foreach ($m in $all) {
  $who = if ($m.isSend -eq 1) { '我' } else { $display }
  $base = Get-BaseType $m.localType
  $content = [string]$m.content
  if ($base -ne 1) {
    $label = Get-TypeLabel $m.localType
    $content = "[$label]" + $(if ($content.Trim()) { ' ' + $content.Trim() } else { '' })
  }
  $time = Get-Fmt $m.createTime
  [void]$sbMd.AppendLine("**[$time] $who：** $($content.Trim())")
  [void]$sbMd.AppendLine("")
  [void]$sbTxt.AppendLine("[$time] $who：$($content.Trim())")
}

$mdText = $sbMd.ToString(); $txtText = $sbTxt.ToString()
[System.IO.File]::WriteAllText((Join-Path $outDir '笑一-聊天记录.md'), $mdText, (New-Object System.Text.UTF8Encoding($false)))
[System.IO.File]::WriteAllText((Join-Path $outDir '笑一-聊天记录.txt'), $txtText, (New-Object System.Text.UTF8Encoding($false)))

# 5) 恢复 API 状态 + 重启
Write-Host '[5/5] 恢复 API 配置并重启 ...' -ForegroundColor Yellow
$origTokenMatch = [regex]::Match($orig, '"httpApiToken"\s*:\s*"([^"]*)"')
$origToken = if ($origTokenMatch.Success) { $origTokenMatch.Groups[1].Value } else { '' }
Edit-Config $origEnabled $origToken
Start-WeFlow

Write-Host ''
Write-Host '完成。' -ForegroundColor Green
Write-Host ("  消息总数：{0} 条" -f $all.Count) -ForegroundColor Green
if ($all.Count -gt 0) { Write-Host ("  时间范围：{0} ~ {1}" -f (Get-Fmt $all[0].createTime), (Get-Fmt $all[-1].createTime)) -ForegroundColor Green }
Write-Host ("  已保存到：{0}" -f $outDir) -ForegroundColor Green
