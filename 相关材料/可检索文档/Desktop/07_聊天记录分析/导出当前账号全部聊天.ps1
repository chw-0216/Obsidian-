# 导出「当前登录的微信账号」的全部聊天记录（WeFlow HTTP API）
# 说明：请先在电脑微信（Weixin 4.x）里登录好要导出的账号，并确认想导出的聊天已同步/迁移到电脑。
#
# 用法：
#   pwsh -File 导出当前账号全部聊天.ps1
#   pwsh -File 导出当前账号全部聊天.ps1 -Media                  # 同时导出图片/视频/语音/表情
#   pwsh -File 导出当前账号全部聊天.ps1 -Talkers 'wxid_xxx,123@chatroom'  # 只导出指定会话（逗号分隔）
#   pwsh -File 导出当前账号全部聊天.ps1 -Keyword '项目'          # 只导出名称含关键词的会话
#   pwsh -File 导出当前账号全部聊天.ps1 -KeepApiOn               # 结束后保持 HTTP API 开启（不恢复原状态）
param(
  [switch]$Media,
  [string]$Talkers = '',
  [string]$Keyword = '',
  [switch]$KeepApiOn,
  [string]$OutDir = ''
)

$ErrorActionPreference = 'Stop'

$exe     = 'C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeFlow\app\WeFlow.exe'
$cfgPath = 'C:\Users\wardc\AppData\Roaming\WeFlow\WeFlow-config.json'
$port    = 5031

if (-not (Test-Path $exe))     { throw "找不到 WeFlow.exe：$exe" }
if (-not (Test-Path $cfgPath)) { throw "找不到配置：$cfgPath" }

$typeMap = @{1='文本';3='图片';34='语音';42='名片';43='视频';47='表情';48='位置';49='链接/卡片';50='语音通话';51='视频通话';10000='系统'}

function Get-BaseType($t) { $v=[int64]$t; if($v -gt 4294967295){ return $v % 4294967296 } else { return $v } }
function Get-HiPart($t)   { $v=[int64]$t; if($v -gt 4294967295){ return [math]::Floor($v / 4294967296) } else { return 0 } }
function Get-TypeLabel($t) {
  $b  = Get-BaseType $t
  $hi = Get-HiPart $t
  if ($hi -eq 5  -and $b -eq 49) { return '链接消息' }
  if ($hi -eq 57 -and $b -eq 49) { return '引用消息' }
  $n = $typeMap[[int]$b]
  if (-not $n) { $n = '类型' + [int]$b }
  if ($hi -gt 0) { $n = '引用·' + $n }
  return $n
}
function Get-Fmt($ts) { if($ts){ return ([DateTimeOffset]::FromUnixTimeSeconds([int64]$ts)).LocalDateTime.ToString('yyyy-MM-dd HH:mm:ss') } else { return '' } }
function Safe-Name($s) {
  $s = [string]$s
  foreach($c in [IO.Path]::GetInvalidFileNameChars()){ $s = $s -replace [regex]::Escape([string]$c), '_' }
  if($s.Length -gt 60){ $s = $s.Substring(0,60) }
  return $s.Trim()
}

function Read-Cfg  { return Get-Content $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json }
function Write-Cfg($obj) {
  $json = $obj | ConvertTo-Json -Depth 100
  $enc  = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($cfgPath, $json, $enc)
}
function Stop-WeFlow  { Get-Process -Name WeFlow -ErrorAction SilentlyContinue | Stop-Process -Force; Start-Sleep -Seconds 2 }
function Start-WeFlow {
  Stop-WeFlow
  Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe)
}
function Wait-Api {
  for($i=0; $i -lt 45; $i++){
    Start-Sleep -Seconds 2
    try { $h = Invoke-RestMethod -Uri "http://127.0.0.1:$port/health" -TimeoutSec 3; if($h.status -eq 'ok'){ return $true } } catch { }
  }
  return $false
}

Write-Host '================ 导出当前账号全部聊天记录（WeFlow） ================' -ForegroundColor Cyan

# ---------- 1) 停 WeFlow，启用 HTTP API（新 token） ----------
$orig        = Read-Cfg
$origEnabled = [bool]$orig.httpApiEnabled
$origToken   = [string]$orig.httpApiToken
if ($orig.httpApiPort) { $port = [int]$orig.httpApiPort }
$token = 'wf-' + [guid]::NewGuid().ToString('N')

Write-Host '[1/6] 停止 WeFlow 并启用 HTTP API ...' -ForegroundColor Yellow
Stop-WeFlow
$cfg = Read-Cfg
$cfg.httpApiEnabled = $true
$cfg.httpApiToken   = $token
$cfg.httpApiPort    = $port
$cfg.httpApiHost    = '127.0.0.1'
Write-Cfg $cfg

# ---------- 2) 启动并等待 API 就绪 ----------
Write-Host '[2/6] 启动 WeFlow，等待 API 就绪 ...' -ForegroundColor Yellow
Start-WeFlow
if (-not (Wait-Api)) { throw 'WeFlow 启动超时（90 秒内 API 未就绪）' }
Write-Host '      API 已就绪' -ForegroundColor Green

$headers = @{ Authorization = "Bearer $token" }

# ---------- 3) 读取当前账号 ----------
$cfg2 = Read-Cfg
$myWxid = [string]$cfg2.myWxid
Write-Host ("[3/6] 当前账号 myWxid: {0}" -f $myWxid) -ForegroundColor Yellow
if (-not $myWxid) { Write-Warning '配置中没有 myWxid，可能尚未初始化；继续尝试读取会话。' }

# ---------- 4) 会话列表 ----------
Write-Host '[4/6] 拉取会话列表 ...' -ForegroundColor Yellow
$sessResp = Invoke-RestMethod -Uri "http://127.0.0.1:$port/api/v1/sessions?limit=10000" -Headers $headers -TimeoutSec 60
$sessions = @($sessResp.sessions)
if ($sessions.Count -eq 0) {
  Write-Warning '未读取到任何会话！'
  Write-Warning '可能原因：WeFlow 尚未加载当前登录的微信账号。'
  Write-Warning '请打开 WeFlow 界面，确认左侧能看到新账号的会话列表（必要时在设置里选择数据目录/账号），然后重跑本脚本。'
  throw '会话列表为空，导出中止'
}
Write-Host ("      共 {0} 个会话" -f $sessions.Count) -ForegroundColor Green

# 过滤
if ($Keyword)  { $sessions = @($sessions | Where-Object { ($_.displayName -like "*$Keyword*") -or ($_.username -like "*$Keyword*") }) ; Write-Host ("      关键词过滤后：{0} 个会话" -f $sessions.Count) -ForegroundColor Yellow }
if ($Talkers)  {
  $set = @{}; ($Talkers -split ',') | ForEach-Object { $set[$_.Trim()] = $true }
  $sessions = @($sessions | Where-Object { $set.ContainsKey([string]$_.username) })
  Write-Host ("      指定会话过滤后：{0} 个会话" -f $sessions.Count) -ForegroundColor Yellow
}
if ($sessions.Count -eq 0) { throw '过滤后没有会话，导出中止' }

# 输出目录
$acctTag = if ($myWxid) { ($myWxid -replace '[^A-Za-z0-9_-]', '_') } else { 'unknown-account' }
if (-not $OutDir) {
  $OutDir = Join-Path 'C:\Users\wardc\Desktop\07_聊天记录分析' ('WeFlow导出_' + $acctTag + '_' + (Get-Date -Format 'yyyy-MM-dd_HHmm'))
}
$sessDir = Join-Path $OutDir 'sessions'
New-Item -ItemType Directory -Force -Path $sessDir | Out-Null
Write-Host ("      输出目录：{0}" -f $OutDir) -ForegroundColor Green

# 联系人映射（尽力而为，失败不影响导出）
$contactMap = @{}
try {
  $cResp = Invoke-RestMethod -Uri "http://127.0.0.1:$port/api/v1/contacts" -Headers $headers -TimeoutSec 60
  foreach ($c in @($cResp.contacts)) {
    $u = [string]$c.username
    if ($u) { $contactMap[$u] = [string]($c.remark ?? $c.displayName ?? $c.nickname ?? $c.name ?? '') }
  }
  Write-Host ("      联系人映射 {0} 条" -f $contactMap.Count) -ForegroundColor Green
} catch { Write-Warning "联系人接口不可用：$_" }

# ---------- 5) 逐会话分页拉取 ----------
$mediaQs = ''
if ($Media) { $mediaQs = '&media=1&image=1&voice=1&video=1&emoji=1' }

$summary = @()
$failed  = @()
$idx = 0
foreach ($s in $sessions) {
  $idx++
  $talker = [string]$s.username
  $name   = if ($s.displayName) { [string]$s.displayName } else { $talker }
  $stype  = [string]$s.sessionType
  Write-Host ("      [{0}/{1}] {2} ({3})" -f $idx, $sessions.Count, $name, $talker) -ForegroundColor DarkGray
  try {
    $all = @(); $offset = 0
    do {
      $url = "http://127.0.0.1:$port/api/v1/messages?talker=$talker&limit=10000&offset=$offset&format=json$mediaQs"
      $j = Invoke-RestMethod -Uri $url -Headers $headers -TimeoutSec 300
      $msgs = @($j.messages)
      $all += $msgs
      $offset += $msgs.Count
      if (-not $j.hasMore -or $msgs.Count -eq 0) { break }
    } while ($true)
    [array]::Reverse($all)

    $safe = '{0:d3}_{1}' -f $idx, (Safe-Name $name)
    $jsonPath = Join-Path $sessDir ($safe + '.json')
    $mdPath   = Join-Path $sessDir ($safe + '.md')

    # 原始 JSON（时间正序）
    $env = [ordered]@{
      talker = $talker; displayName = $name; sessionType = $stype
      exportedAt = [DateTimeOffset]::Now.ToUnixTimeSeconds()
      messageCount = $all.Count
      messages = $all
    }
    $env | ConvertTo-Json -Depth 10 | Set-Content $jsonPath -Encoding UTF8

    # 可读 MD
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine("# $([string]$name)（$stype）")
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine("- 会话 ID：``$talker``")
    [void]$sb.AppendLine("- 消息总数：$($all.Count)")
    [void]$sb.AppendLine("- 导出时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
    if ($all.Count -gt 0) { [void]$sb.AppendLine("- 时间范围：$(Get-Fmt $all[0].createTime) ~ $(Get-Fmt $all[-1].createTime)") }
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('---')
    [void]$sb.AppendLine('')

    foreach ($m in $all) {
      $base = Get-BaseType $m.localType
      if ($stype -eq 'group' -or $stype -eq 'room') {
        if ($m.isSend -eq 1) { $who = '我' }
        else {
          $su = [string]$m.senderUsername
          $who = if ($contactMap.ContainsKey($su)) { $contactMap[$su] } else { $su }
        }
      } else {
        if ($m.isSend -eq 1) { $who = '我' }
        elseif ($base -eq 10000) { $who = '系统' }
        else { $who = $name }
      }
      $content = [string]$m.parsedContent
      if (-not $content) { $content = [string]$m.content }
      if ($m.quote) {
        $qc = [string]$m.quote.content; $qn = [string]($m.quote.accountName ?? $m.quote.sender ?? '')
        if ($qc) { $content = '「引用' + $(if($qn){' ' + $qn}) + '：' + $qc + '」' + $content }
      }
      if ($base -ne 1 -and $base -ne 10000) {
        $label = Get-TypeLabel $m.localType
        if (-not ($content.StartsWith('['))) { $content = "[$label]" + $(if ($content) { ' ' + $content } else { '' }) }
      }
      [void]$sb.AppendLine("**[$((Get-Fmt $m.createTime))] $who：** $content")
      [void]$sb.AppendLine('')
    }
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($mdPath, $sb.ToString(), $enc)

    $first = if($all.Count){ Get-Fmt $all[0].createTime } else { '' }
    $last  = if($all.Count){ Get-Fmt $all[-1].createTime } else { '' }
    $summary += [pscustomobject]@{ Index=$idx; 会话=$name; 类型=$stype; 会话ID=$talker; 消息数=$all.Count; 最早=$first; 最新=$last }
    Write-Host ("          -> {0} 条消息" -f $all.Count) -ForegroundColor Green
  } catch {
    Write-Host ("          !! 失败：{0}" -f $_.Exception.Message) -ForegroundColor Red
    $failed += [pscustomobject]@{ 会话=$name; 会话ID=$talker; 错误=$_.Exception.Message }
  }
}

# ---------- 6) 汇总与收尾 ----------
Write-Host '[6/6] 写汇总报告并恢复 WeFlow ...' -ForegroundColor Yellow
$totalMsgs = ($summary | Measure-Object -Property 消息数 -Sum).Sum

$sbRep = New-Object System.Text.StringBuilder
[void]$sbRep.AppendLine('# WeFlow 聊天记录导出报告')
[void]$sbRep.AppendLine('')
[void]$sbRep.AppendLine("- 账号：``$myWxid``")
[void]$sbRep.AppendLine("- 导出时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
[void]$sbRep.AppendLine("- 会话总数：$($sessions.Count)")
[void]$sbRep.AppendLine("- 消息总数：$totalMsgs")
if ($Media) { [void]$sbRep.AppendLine('- 媒体导出：已开启（图片/视频/语音/表情，路径见 WeFlow 配置的 api-media 目录）') }
[void]$sbRep.AppendLine('')
[void]$sbRep.AppendLine('## 会话明细')
[void]$sbRep.AppendLine('')
[void]$sbRep.AppendLine('| # | 会话 | 类型 | 会话ID | 消息数 | 最早 | 最新 |')
[void]$sbRep.AppendLine('|---|------|------|--------|--------|------|------|')
foreach ($r in $summary) { [void]$sbRep.AppendLine(('| {0} | {1} | {2} | {3} | {4} | {5} | {6} |' -f $r.Index, $r.会话, $r.类型, $r.会话ID, $r.消息数, $r.最早, $r.最新)) }
if ($failed.Count -gt 0) {
  [void]$sbRep.AppendLine('')
  [void]$sbRep.AppendLine('## 失败会话')
  [void]$sbRep.AppendLine('')
  foreach ($f in $failed) { [void]$sbRep.AppendLine("- $($f.会话)：$($f.错误)") }
}
$encR = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path $OutDir '导出报告.md'), $sbRep.ToString(), $encR)

$summary | Export-Csv -Path (Join-Path $OutDir '会话列表.csv') -NoTypeInformation -Encoding UTF8
$sessResp | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $OutDir 'sessions_raw.json') -Encoding UTF8

# 恢复原 API 状态并重启（除非 -KeepApiOn）
if (-not $KeepApiOn) {
  Stop-WeFlow
  $cfgR = Read-Cfg
  $cfgR.httpApiEnabled = $origEnabled
  $cfgR.httpApiToken   = $origToken
  $cfgR.httpApiPort    = $port
  Write-Cfg $cfgR
  Start-WeFlow
} else {
  Write-Host '      （按 -KeepApiOn 要求，保持 API 开启，未重启）' -ForegroundColor DarkGray
}

Write-Host ''
Write-Host '完成。' -ForegroundColor Green
Write-Host ("  输出目录：{0}" -f $OutDir) -ForegroundColor Green
Write-Host ("  会话总数：{0}，消息总数：{1}，失败会话：{2}" -f $sessions.Count, $totalMsgs, $failed.Count) -ForegroundColor Green
