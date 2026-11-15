# 监控笑一对话：检测她停发消息后，自动导出最近对话供分析
# 用法：双击同目录的 监控笑一对话.bat；关闭窗口即停止。
# 参数可改：$silenceMin = 她停发多少分钟后触发；$pollSec = 轮询间隔(秒)

$ErrorActionPreference = 'Continue'
$token      = 'test123'
$talker     = 'wxid_wdnk6ue9kiyn22'
$base       = 'http://127.0.0.1:5031'
$outFile    = 'C:\Users\wardc\Desktop\待回复对话.txt'
$silenceMin = 15        # 她停发 15 分钟后触发
$pollSec    = 60        # 每 60 秒轮询一次

$lastId    = $null
$lastNewAt = $null
$triggered = $false

function Format-Time($ts) {
  return ([DateTimeOffset]::FromUnixTimeSeconds([int64]$ts)).LocalDateTime.ToString('MM-dd HH:mm:ss')
}

Write-Host '============================================' -ForegroundColor Cyan
Write-Host '  监控笑一对话（沉默检测 + 自动导出）' -ForegroundColor Cyan
Write-Host "  触发条件：她发消息后停发 $silenceMin 分钟" -ForegroundColor DarkGray
Write-Host "  关闭本窗口即停止" -ForegroundColor DarkGray
Write-Host '============================================' -ForegroundColor Cyan

while ($true) {
  try {
    $url = "$base/api/v1/messages?talker=$talker&limit=20&format=json"
    $j = Invoke-RestMethod -Uri $url -Headers @{ Authorization = "Bearer $token" } -TimeoutSec 30
    $msgs = @($j.messages)   # 最新在前
    if ($msgs.Count -gt 0) {
      $newest = $msgs[0]
      # 检测到新消息（用 localId 判断）
      if ($lastId -eq $null -or $newest.localId -ne $lastId) {
        $lastId = $newest.localId
        $lastNewAt = Get-Date
        $triggered = $false   # 有动静，重置触发标记
        $who = if ($newest.isSend -eq 1) { '我' } else { '她' }
        Write-Host ("[{0}] 新消息({1}): {2}" -f (Get-Date -Format 'HH:mm:ss'), $who, ([string]$newest.content).Substring(0, [Math]::Min(30, ([string]$newest.content).Length)))
      }
      # 判断沉默：最后一条是她发的，且停发超过阈值
      $lastFromHer = ($newest.isSend -eq 0)
      if ($lastNewAt -ne $null) {
        $silentFor = ((Get-Date) - $lastNewAt).TotalMinutes
        if ($lastFromHer -and $silentFor -ge $silenceMin -and -not $triggered) {
          $triggered = $true
          # 导出最近 20 条（时间正序）
          $recent = @($msgs)[0..([Math]::Min(19, $msgs.Count - 1))]
          [array]::Reverse($recent)
          $sb = New-Object System.Text.StringBuilder
          [void]$sb.AppendLine(("=== 待回复对话（她已停发 {0:N0} 分钟，{1}）===" -f $silentFor, (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')))
          foreach ($m in $recent) {
            $who = if ($m.isSend -eq 1) { '我' } else { '她' }
            [void]$sb.AppendLine("[{0}] {1}: {2}" -f (Format-Time $m.createTime), $who, ([string]$m.content))
          }
          $utf8 = New-Object System.Text.UTF8Encoding($false)
          [System.IO.File]::WriteAllText($outFile, $sb.ToString(), $utf8)
          Write-Host '' -ForegroundColor Green
          Write-Host ('>>> 她已停发 {0:N0} 分钟，最近对话已导出到：' -f $silentFor) -ForegroundColor Yellow
          Write-Host ('    {0}' -f $outFile) -ForegroundColor Yellow
          Write-Host '>>> 把该文件内容贴给 AI，索取回复方案。' -ForegroundColor Yellow
          Write-Host ''
        }
      }
    }
  } catch {
    Write-Host ('[{0}] 请求失败(可能锚点漂移 -105)：{1}' -f (Get-Date -Format 'HH:mm:ss'), $_.Exception.Message) -ForegroundColor Red
    Write-Host '     若持续失败，请先运行 WeFlow一键修复.bat' -ForegroundColor Red
  }
  Start-Sleep -Seconds $pollSec
}
