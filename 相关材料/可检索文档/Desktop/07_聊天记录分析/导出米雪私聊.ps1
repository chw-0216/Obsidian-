# 导出「米雪」私聊聊天记录（通过 WeFlow HTTP API）
# 米雪 = 知行计划项目组委会老师（企业微信 openim 账号）
$ErrorActionPreference = 'Stop'

$talker  = '25984982731545183@openim'
$display = '米雪'
$myWxid  = 'wxid_zn4ozsnn8esr21'
$port    = 5031
$token   = 'wf-b5ed26ca23f04980bca34f39e81a2adf'
$outDir  = 'C:\Users\wardc\Desktop\07_聊天记录分析\米雪导出_' + (Get-Date -Format 'yyyy-MM-dd')

$typeMap = @{1='文本';3='图片';34='语音';42='名片';43='视频';47='表情';48='位置';49='链接/卡片';50='语音通话';51='视频通话';10000='系统'}

function Get-BaseType($t){ $v=[int64]$t; if($v -gt 4294967295){ return $v % 4294967296 } else { return $v } }
function Get-HiPart($t){ $v=[int64]$t; if($v -gt 4294967295){ return [math]::Floor($v / 4294967296) } else { return 0 } }
function Get-TypeLabel($t) {
  $b = Get-BaseType $t
  $hi = Get-HiPart $t
  if ($hi -eq 5  -and $b -eq 49) { return '链接消息' }
  if ($hi -eq 57 -and $b -eq 49) { return '引用消息' }
  $n = $typeMap[[int]$b]
  if (-not $n) { $n = '类型'+[int]$b }
  if ($hi -gt 0) { $n = '引用·'+$n }
  return $n
}
function Get-Fmt($ts){ return ([DateTimeOffset]::FromUnixTimeSeconds([int64]$ts)).LocalDateTime.ToString('yyyy-MM-dd HH:mm:ss') }

function Get-CleanContent($m) {
  $c = [string]$m.content
  if (-not $c) { return '' }
  $base = Get-BaseType $m.localType
  if ($c -match '^<msg>') {
    $title = ''; $des = ''
    $tm = [regex]::Match($c, '(?s)<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>')
    if ($tm.Success) { $title = if ($tm.Groups[1].Value) { $tm.Groups[1].Value } else { $tm.Groups[2].Value } }
    $dm = [regex]::Match($c, '(?s)<des><!\[CDATA\[(.*?)\]\]></des>|<des>(.*?)</des>')
    if ($dm.Success) { $des = if ($dm.Groups[1].Value) { $dm.Groups[1].Value } else { $dm.Groups[2].Value } }
    $parts = @()
    if ($title) { $parts += $title }
    if ($des) { $parts += $des }
    if ($parts.Count -gt 0) { return ($parts -join ' | ') }
    return '[链接]'
  }
  $c = [regex]::Replace($c, '<[^>]+href="([^"]+)"[^>]*>(.*?)</[^>]+>', '$2($1)')
  return $c.Trim()
}

Write-Host '============================================' -ForegroundColor Cyan
Write-Host '  导出米雪私聊聊天记录（WeFlow HTTP API）' -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan

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

[array]::Reverse($all)
$total = $all.Count
Write-Host ("      共 {0} 条消息" -f $total) -ForegroundColor Green
if ($total -gt 0) {
    Write-Host ("      时间范围：{0} ~ {1}" -f (Get-Fmt $all[0].createTime), (Get-Fmt $all[-1].createTime)) -ForegroundColor Green
}

if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }

function Get-Who($m) {
    if ($m.isSend -eq 1) { return '我' }
    if ((Get-BaseType $m.localType) -eq 10000) { return '系统' }
    return '米雪'
}

$resolved = @()
foreach ($m in $all) {
    $resolved += [ordered]@{
        localId        = $m.localId
        createTime     = $m.createTime
        formattedTime  = Get-Fmt $m.createTime
        type           = Get-TypeLabel $m.localType
        localType      = $m.localType
        content        = [string]$m.content
        cleanedContent = Get-CleanContent $m
        isSend         = $m.isSend
        senderUsername = [string]$m.senderUsername
        sender         = Get-Who $m
        serverId       = $m.serverId
    }
}
$jsonObj = [ordered]@{
    weflow   = [ordered]@{ version = '6.x-api'; exportedAt = ([DateTimeOffset]::Now.ToUnixTimeSeconds()); generator = 'WeFlow HTTP API（米雪私聊导出脚本）' }
    session  = [ordered]@{ wxid = $talker; nickname = $display; type = '私聊'; lastTimestamp = if($total){$all[-1].createTime}else{0}; messageCount = $total }
    messages = $resolved
}
$jsonObj | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $outDir ('私聊_米雪_' + (Get-Date -Format 'yyyyMMdd-HHmm') + '.json')) -Encoding UTF8

$sbMd = New-Object System.Text.StringBuilder
[void]$sbMd.AppendLine("# 私聊「$display」聊天记录")
[void]$sbMd.AppendLine("")
[void]$sbMd.AppendLine("- 对方：$display（知行计划项目组委会老师，企业微信）")
[void]$sbMd.AppendLine("- 对方账号：``$talker``")
[void]$sbMd.AppendLine("- 消息总数：$total")
[void]$sbMd.AppendLine("- 导出时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
if ($total -gt 0) { [void]$sbMd.AppendLine("- 时间范围：$(Get-Fmt $all[0].createTime) ~ $(Get-Fmt $all[-1].createTime)") }
[void]$sbMd.AppendLine("")
[void]$sbMd.AppendLine("---")
[void]$sbMd.AppendLine("")
foreach ($m in $all) {
    $who = Get-Who $m
    $base = Get-BaseType $m.localType
    $content = Get-CleanContent $m
    if ($base -ne 1 -and $base -ne 10000) {
        $label = Get-TypeLabel $m.localType
        $content = "[$label]" + $(if ($content) { ' ' + $content } else { '' })
    }
    [void]$sbMd.AppendLine("**[$((Get-Fmt $m.createTime))] $who：** $content")
    [void]$sbMd.AppendLine("")
}
$enc = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path $outDir '私聊_米雪.md'), $sbMd.ToString(), $enc)

Write-Host '[完成]' -ForegroundColor Green
Write-Host ("  输出目录：{0}" -f $outDir) -ForegroundColor Green
Write-Host ("  消息总数：{0} 条" -f $total) -ForegroundColor Green
if ($total -gt 0) { Write-Host ("  最新一条：{0} | {1}：{2}" -f (Get-Fmt $all[-1].createTime), (Get-Who $all[-1]), (Get-CleanContent $all[-1])) -ForegroundColor Green }
