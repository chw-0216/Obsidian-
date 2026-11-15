# 导出「知行计划立项群」聊天记录（通过 WeFlow HTTP API）v2
# 群：立项2群-第三届Movers4Climate绿色乡村青年行动  wxid: 49882411489@chatroom
$ErrorActionPreference = 'Stop'

# ---- 配置 ----
$talker   = '49882411489@chatroom'
$display  = '立项2群-第三届Movers4Climate绿色乡村青年行动'
$myWxid   = 'wxid_zn4ozsnn8esr21'
$port     = 5031
$token    = 'wf-b5ed26ca23f04980bca34f39e81a2adf'   # WeFlow-config.json 里 httpApiToken（2026-09-18 更新）
$outDir   = 'C:\Users\wardc\Desktop\07_聊天记录分析\知行计划立项群导出_' + (Get-Date -Format 'yyyy-MM-dd')
$oldExport = 'C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出\群聊_立项2群-第三届Movers4Climate绿色乡村青年行动\群聊_立项2群-第三届Movers4Climate绿色乡村青年行动.json'

$typeMap = @{1='文本';3='图片';34='语音';42='名片';43='视频';47='表情';48='位置';49='链接/卡片';50='语音通话';51='视频通话';10000='系统'}

function Get-BaseType($t){ $v=[int64]$t; if($v -gt 4294967295){ return $v % 4294967296 } else { return $v } }
function Get-HiPart($t){ $v=[int64]$t; if($v -gt 4294967295){ return [math]::Floor($v / 4294967296) } else { return 0 } }

function Get-TypeLabel($t) {
  $b = Get-BaseType $t
  $hi = Get-HiPart $t
  if ($hi -eq 5  -and $b -eq 49) { return '链接消息' }
  if ($hi -eq 57 -and $b -eq 49) { return '引用消息' }
  if ($hi -eq 51 -and $b -eq 49) { return '其他消息' }
  $n = $typeMap[[int]$b]
  if (-not $n) { $n = '类型'+[int]$b }
  if ($hi -gt 0) { $n = '引用·'+$n }
  return $n
}

function Get-Fmt($ts){ return ([DateTimeOffset]::FromUnixTimeSeconds([int64]$ts)).LocalDateTime.ToString('yyyy-MM-dd HH:mm:ss') }

# 清理系统消息 XML / 微信富文本标签
function Get-CleanContent($m) {
  $c = [string]$m.content
  if (-not $c) { return '' }
  $base = Get-BaseType $m.localType
  if ($base -eq 10000 -and $c -match '<sysmsg') {
    $tpl = ''
    if ($c -match '<template><!\[CDATA\[(.*?)\]\]></template>') { $tpl = $Matches[1] }
    elseif ($c -match '<template>(.*?)</template>') { $tpl = $Matches[1] }
    if ($tpl) {
      $linkMap = @{}
      $linkRegex = [regex]'(?s)<link name="([^"]+)"[^>]*>(.*?)</link>'
      $memberRegex = [regex]'(?s)<nickname><!\[CDATA\[(.*?)\]\]></nickname>|<nickname>(.*?)</nickname>'
      $sepRegex = [regex]'(?s)<separator><!\[CDATA\[(.*?)\]\]></separator>|<separator>(.*?)</separator>'
      foreach ($lm in $linkRegex.Matches($c)) {
        $ln = $lm.Groups[1].Value
        $block = $lm.Groups[2].Value
        # link_plain 形式：直接用 <plain> 文本
        $pm = [regex]::Match($block, '(?s)<plain><!\[CDATA\[(.*?)\]\]></plain>|<plain>(.*?)</plain>')
        if ($pm.Success) {
          $linkMap[$ln] = if ($pm.Groups[1].Value) { $pm.Groups[1].Value } else { $pm.Groups[2].Value }
          continue
        }
        # memberlist 形式
        $names = @()
        foreach ($mm in $memberRegex.Matches($block)) {
          $nm = $mm.Groups[1].Value
          if (-not $nm) { $nm = $mm.Groups[2].Value }
          $names += $nm
        }
        $sep = '、'
        $sm = $sepRegex.Match($block)
        if ($sm.Success) { $sep = if ($sm.Groups[1].Value) { $sm.Groups[1].Value } else { $sm.Groups[2].Value } }
        $linkMap[$ln] = ($names -join $sep)
      }
      $out = $tpl
      foreach ($k in $linkMap.Keys) { $out = $out.Replace('$' + $k + '$', $linkMap[$k]) }
      $out = $out -replace '\s+', ' '
      return $out.Trim()
    }
    $c = $c -replace '<[^>]+>', ''
    return $c.Trim()
  }
  # 微信公众号/链接卡片 appmsg XML：提取 title/des/url
  if ($c -match '^<msg>') {
    $title = ''; $des = ''; $url = ''
    $tm = [regex]::Match($c, '(?s)<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>')
    if ($tm.Success) { $title = if ($tm.Groups[1].Value) { $tm.Groups[1].Value } else { $tm.Groups[2].Value } }
    $dm = [regex]::Match($c, '(?s)<des><!\[CDATA\[(.*?)\]\]></des>|<des>(.*?)</des>')
    if ($dm.Success) { $des = if ($dm.Groups[1].Value) { $dm.Groups[1].Value } else { $dm.Groups[2].Value } }
    $um = [regex]::Match($c, '(?s)<url><!\[CDATA\[(.*?)\]\]></url>|<url>(.*?)</url>')
    if ($um.Success) { $url = if ($um.Groups[1].Value) { $um.Groups[1].Value } else { $um.Groups[2].Value } }
    $parts = @()
    if ($title) { $parts += $title }
    if ($des) { $parts += $des }
    if ($url) { $parts += $url }
    if ($parts.Count -gt 0) { return ($parts -join "`n") }
    return '[链接]'
  }
  # 微信链接标签 <_wc_custom_link_ href="...">文字</...> -> [文字](链接)
  $c = [regex]::Replace($c, '<[^>]+href="([^"]+)"[^>]*>(.*?)</[^>]+>', '[ $2 ]( $1 )')
  return $c.Trim()
}

Write-Host '============================================' -ForegroundColor Cyan
Write-Host '  导出知行计划立项群聊天记录 v2' -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan

# ---- 1) 构建成员姓名映射（来自既有 WeFlow GUI 导出）----
Write-Host '[1/4] 构建成员姓名映射 ...' -ForegroundColor Yellow
$nameMap = @{}
if (Test-Path $oldExport) {
    $old = Get-Content $oldExport -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($m in $old.messages) {
        $u = [string]$m.senderUsername
        $d = [string]$m.senderDisplayName
        if ($u -and $u -ne $talker -and $d -and -not $nameMap.ContainsKey($u)) {
            $nameMap[$u] = $d
        }
    }
}
Write-Host ("      映射到 {0} 个群成员/发送者" -f $nameMap.Count) -ForegroundColor Green

# ---- 2) 分页拉取全部消息 ----
Write-Host '[2/4] 通过 WeFlow API 分页拉取消息 ...' -ForegroundColor Yellow
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

[array]::Reverse($all)   # 转为时间正序
$total = $all.Count
Write-Host ("      共 {0} 条消息" -f $total) -ForegroundColor Green
if ($total -gt 0) {
    Write-Host ("      时间范围：{0} ~ {1}" -f (Get-Fmt $all[0].createTime), (Get-Fmt $all[-1].createTime)) -ForegroundColor Green
}

# ---- 3) 生成输出 ----
Write-Host '[3/4] 写入 json / md / txt ...' -ForegroundColor Yellow
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }

function Get-Who($m) {
    if ($m.isSend -eq 1) { return '我' }
    if ((Get-BaseType $m.localType) -eq 10000) { return '系统' }
    $u = [string]$m.senderUsername
    if ($u -and $nameMap.ContainsKey($u)) { return $nameMap[$u] }
    if ($u) { return $u }
    return '未知'
}

# 完整 JSON（兼容 WeFlow 结构，含姓名解析）
$resolved = @()
foreach ($m in $all) {
    $u = [string]$m.senderUsername
    $d = $u
    if ($m.isSend -eq 1) { $d = $myWxid }
    elseif ($nameMap.ContainsKey($u)) { $d = $nameMap[$u] }
    $resolved += [ordered]@{
        localId           = $m.localId
        createTime        = $m.createTime
        formattedTime     = Get-Fmt $m.createTime
        type              = Get-TypeLabel $m.localType
        localType         = $m.localType
        content           = [string]$m.content
        cleanedContent    = Get-CleanContent $m
        isSend            = $m.isSend
        senderUsername    = $u
        senderDisplayName = $d
        platformMessageId = $m.serverId
    }
}
$jsonObj = [ordered]@{
    weflow   = [ordered]@{ version = '6.1.0-api'; exportedAt = ([DateTimeOffset]::Now.ToUnixTimeSeconds()); generator = 'WeFlow HTTP API (DeepSeek 导出脚本 v2)' }
    session  = [ordered]@{ wxid = $talker; nickname = $display; remark = ''; displayName = $display; type = '群聊'; lastTimestamp = if($total){$all[-1].createTime}else{0}; messageCount = $total }
    messages = $resolved
}
$jsonObj | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $outDir ($display + '.json')) -Encoding UTF8

# Markdown / TXT
$sbMd = New-Object System.Text.StringBuilder
[void]$sbMd.AppendLine("# 群聊「$display」聊天记录")
[void]$sbMd.AppendLine("")
[void]$sbMd.AppendLine("- 群 wxid：``$talker``")
[void]$sbMd.AppendLine("- 消息总数：$total")
[void]$sbMd.AppendLine("- 导出时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
if ($total -gt 0) { [void]$sbMd.AppendLine("- 时间范围：$(Get-Fmt $all[0].createTime) ~ $(Get-Fmt $all[-1].createTime)") }
[void]$sbMd.AppendLine("- 成员姓名解析：基于 2026-07-24 WeFlow 导出 + API 实时数据")
[void]$sbMd.AppendLine("")
[void]$sbMd.AppendLine("---")
[void]$sbMd.AppendLine("")

$sbTxt = New-Object System.Text.StringBuilder
[void]$sbTxt.AppendLine("群聊「$display」聊天记录（共 $total 条）")
if ($total -gt 0) { [void]$sbTxt.AppendLine("时间范围：$(Get-Fmt $all[0].createTime) ~ $(Get-Fmt $all[-1].createTime)") }
[void]$sbTxt.AppendLine(('=' * 60))
[void]$sbTxt.AppendLine("")

foreach ($m in $all) {
    $who = Get-Who $m
    $base = Get-BaseType $m.localType
    $content = Get-CleanContent $m
    if ($base -ne 1 -and $base -ne 10000) {
        $label = Get-TypeLabel $m.localType
        $content = "[$label]" + $(if ($content) { ' ' + $content } else { '' })
    }
    $time = Get-Fmt $m.createTime
    [void]$sbMd.AppendLine("**[$time] $who：** $content")
    [void]$sbMd.AppendLine("")
    [void]$sbTxt.AppendLine("[$time] $who：$content")
}

$mdText = $sbMd.ToString(); $txtText = $sbTxt.ToString()
$enc = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path $outDir ($display + '.md')), $mdText, $enc)
[System.IO.File]::WriteAllText((Join-Path $outDir ($display + '.txt')), $txtText, $enc)

# 说明文件
$sbNote = New-Object System.Text.StringBuilder
[void]$sbNote.AppendLine("# 知行计划立项群 · 导出说明")
[void]$sbNote.AppendLine("")
[void]$sbNote.AppendLine("- **群名**：$display")
[void]$sbNote.AppendLine("- **群 wxid**：$talker")
[void]$sbNote.AppendLine("- **导出方式**：WeFlow 本地 HTTP API（127.0.0.1:$port），实时数据")
[void]$sbNote.AppendLine("- **导出时间**：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
[void]$sbNote.AppendLine("- **消息总数**：$total")
if ($total -gt 0) { [void]$sbNote.AppendLine("- **时间范围**：$(Get-Fmt $all[0].createTime) ~ $(Get-Fmt $all[-1].createTime)") }
[void]$sbNote.AppendLine("")
[void]$sbNote.AppendLine("## 文件说明")
[void]$sbNote.AppendLine("- `.json`：全量原始数据（含 cleanedContent、发送者 wxid、类型、时间戳），供程序分析")
[void]$sbNote.AppendLine("- `.md`：可读版（时间正序，已解析成员姓名、系统消息已翻译为可读文本）")
[void]$sbNote.AppendLine("- `.txt`：纯文本版（时间正序）")
[void]$sbNote.AppendLine("")
[void]$sbNote.AppendLine("## 说明与后续")
[void]$sbNote.AppendLine("- 成员姓名来自 2026-07-24 WeFlow GUI 导出的 senderDisplayName 映射；07-24 之后新出现的发送者若未映射到姓名，会回退显示其原始 wxid/openim id。")
[void]$sbNote.AppendLine("- 图片/文档等媒体文件未在本脚本中下载；如需媒体原件，可在 WeFlow 界面选中该群再次做 GUI 导出（导出目录含 media/ 子文件夹）。")
[void]$sbNote.AppendLine("- 若需要增量更新，重新运行本脚本即可覆盖输出。")
[System.IO.File]::WriteAllText((Join-Path $outDir '导出说明.md'), $sbNote.ToString(), $enc)

Write-Host '[4/4] 完成' -ForegroundColor Green
Write-Host ''
Write-Host ("  输出目录：{0}" -f $outDir) -ForegroundColor Green
Write-Host ("  消息总数：{0} 条" -f $total) -ForegroundColor Green
if ($total -gt 0) { Write-Host ("  时间范围：{0} ~ {1}" -f (Get-Fmt $all[0].createTime), (Get-Fmt $all[-1].createTime)) -ForegroundColor Green }
Write-Host ("  成员姓名映射：{0} 个" -f $nameMap.Count) -ForegroundColor Green
