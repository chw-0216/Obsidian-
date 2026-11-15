# 导出「jt（姜涛老师）」的微信聊天记录
# 用法：pwsh -File "C:\Users\wardc\Desktop\07_聊天记录分析\导出jt姜涛老师.ps1"
# 原理：读取 WeFlow 配置中的 API Token → 分页拉取该联系人全部消息 → 写入 json / md / txt
# 前置条件：WeFlow 正在运行且「设置 → API 服务」已启用（本机 http://127.0.0.1:5031）

$ErrorActionPreference = 'Stop'

$cfg     = 'C:\Users\wardc\AppData\Roaming\WeFlow\WeFlow-config.json'
$outDir  = 'C:\Users\wardc\Desktop\07_聊天记录分析\jt导出_2026-09-10'
$talker  = 'wxid_6lxct8lknfzt21'          # jt（姜涛老师），地区：云南 普洱
$display = 'jt（姜涛老师）'
$myWxid  = 'wxid_zn4ozsnn8esr21'          # 自己
$port    = 5031

$typeMap = @{1='文本';3='图片';34='语音';42='名片';43='视频';47='表情';48='位置';49='链接/卡片/文件';50='语音通话';51='视频通话';10000='系统'}

# 1) 读取 Token
$raw = [System.IO.File]::ReadAllText($cfg)
$token = [regex]::Match($raw, '"httpApiToken"\s*:\s*"([^"]*)"').Groups[1].Value
if (-not $token) { throw '未在 WeFlow 配置中找到 httpApiToken，请先在 WeFlow 设置中启用 API 服务。' }
$headers = @{ Authorization = "Bearer $token" }

function Get-BaseType($t) { $v = [int64]$t; if ($v -gt 4294967295) { return $v % 4294967296 } else { return $v } }
function Get-TypeLabel($t) {
  $b = Get-BaseType $t
  $name = $typeMap[[int]$b]
  if (-not $name) { $name = '类型' + [int]$b }
  if ([int64]$t -gt 4294967295) { $name = '引用·' + $name }
  return $name
}
function Get-Fmt($ts) { return ([DateTimeOffset]::FromUnixTimeSeconds([int64]$ts)).LocalDateTime.ToString('yyyy-MM-dd HH:mm:ss') }

# 2) 分页拉取
Write-Host '[1/3] 拉取消息 ...' -ForegroundColor Yellow
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

[array]::Reverse($all)   # 时间正序
Write-Host ("      共 {0} 条消息" -f $all.Count) -ForegroundColor Green

# 3) 写文件
Write-Host '[2/3] 写入 json / md / txt ...' -ForegroundColor Yellow
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }

$jsonObj = [ordered]@{
  talker = $talker; displayName = $display; region = '云南 普洱'; myWxid = $myWxid
  exportedAt = (Get-Date).ToString('o'); totalCount = $all.Count; messages = $all
}
$jsonObj | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $outDir 'jt_姜涛老师_聊天记录.json') -Encoding UTF8

$sbMd  = New-Object System.Text.StringBuilder
$sbTxt = New-Object System.Text.StringBuilder
[void]$sbMd.AppendLine("# 与「$display」的聊天记录")
[void]$sbMd.AppendLine("")
[void]$sbMd.AppendLine("- 对方 wxid：``$talker``")
[void]$sbMd.AppendLine("- 地区：云南 普洱")
[void]$sbMd.AppendLine("- 消息总数：$($all.Count)")
[void]$sbMd.AppendLine("- 导出时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
if ($all.Count -gt 0) {
  [void]$sbMd.AppendLine("- 时间范围：$(Get-Fmt $all[0].createTime) ~ $(Get-Fmt $all[-1].createTime)")
}
[void]$sbMd.AppendLine("")
[void]$sbMd.AppendLine("---")
[void]$sbMd.AppendLine("")

[void]$sbTxt.AppendLine("与「$display」的聊天记录（共 $($all.Count) 条）")
if ($all.Count -gt 0) { [void]$sbTxt.AppendLine("时间范围：$(Get-Fmt $all[0].createTime) ~ $(Get-Fmt $all[-1].createTime)") }
[void]$sbTxt.AppendLine(('=' * 50))
[void]$sbTxt.AppendLine("")

foreach ($m in $all) {
  $who = if ($m.isSend -eq 1) { '我' } else { $display }
  $base = Get-BaseType $m.localType
  $content = [string]$m.content
  if ($base -eq 49) {
    $title = [regex]::Match($content, '<title>(.*?)</title>').Groups[1].Value
    $content = '[文件/卡片]' + $(if ($title) { ' ' + $title } else { '' })
  } elseif ($base -ne 1) {
    $label = Get-TypeLabel $m.localType
    $content = "[$label]" + $(if ($content.Trim()) { ' ' + $content.Trim() } else { '' })
    if ($base -eq 50) {
      $voip = [regex]::Match($content, 'CDATA\[(.*?)\]\]').Groups[1].Value
      if ($voip) { $content = "[语音通话] $voip" }
    }
  }
  $time = Get-Fmt $m.createTime
  [void]$sbMd.AppendLine("**[$time] $who：** $($content.Trim())")
  [void]$sbMd.AppendLine("")
  [void]$sbTxt.AppendLine("[$time] $who：$($content.Trim())")
}

[System.IO.File]::WriteAllText((Join-Path $outDir 'jt_姜涛老师_聊天记录.md'),  $sbMd.ToString(),  (New-Object System.Text.UTF8Encoding($false)))
[System.IO.File]::WriteAllText((Join-Path $outDir 'jt_姜涛老师_聊天记录.txt'), $sbTxt.ToString(), (New-Object System.Text.UTF8Encoding($false)))

Write-Host '[3/3] 完成。' -ForegroundColor Green
Write-Host ("  输出目录：{0}" -f $outDir) -ForegroundColor Green
Write-Host ("  消息总数：{0} 条" -f $all.Count) -ForegroundColor Green
if ($all.Count -gt 0) { Write-Host ("  时间范围：{0} ~ {1}" -f (Get-Fmt $all[0].createTime), (Get-Fmt $all[-1].createTime)) -ForegroundColor Green }
