# 恢复脚本（仅复制，不删除任何东西）：把被迁移到 D 盘备份的文件复制回 C 盘原位
# D 盘副本全部保留作为备份（符合"D盘=外接备份盘"的要求）
$ErrorActionPreference = 'Continue'
. 'C:\Users\wardc\Desktop\_迁移工具\mapping_disabled.ps1'
$root = 'D:\资料整理_2026-08-17'
$log = 'C:\Users\wardc\Desktop\_迁移工具\恢复复制日志.txt'
function Log([string]$m) {
  "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | $m" | Out-File -LiteralPath $log -Append -Encoding utf8
  Write-Output $m
}
Log "===== 恢复开始（仅复制；D盘备份保留） ====="
$restored = 0; $already = 0; $noop = 0
foreach ($e in $map) {
  if ($e.action -eq 'delete') { continue }
  $dstFull = if ($e.dst -match '^[A-Za-z]:') { $e.dst } else { Join-Path $root $e.dst }
  if ($e.wildcard) {
    $parent = Split-Path -Parent $e.src
    if (-not (Test-Path -LiteralPath $dstFull)) { $noop++; continue }
    $files = @(Get-ChildItem -LiteralPath $dstFull -Recurse -Force -File -ErrorAction SilentlyContinue)
    if ($files.Count -eq 0) { $noop++; continue }
    foreach ($f in $files) {
      $rel = $f.FullName.Substring($dstFull.Length).TrimStart('\')
      $target = Join-Path $parent $rel
      if (Test-Path -LiteralPath $target) { $already++; continue }
      New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force | Out-Null
      Copy-Item -LiteralPath $f.FullName -Destination $target -Force
      Log ("RESTORED: {0} -> {1}" -f $f.Name, $target)
      $restored++
    }
  }
  else {
    if (Test-Path -LiteralPath $e.src) { $already++; continue }
    if (-not (Test-Path -LiteralPath $dstFull)) { $noop++; continue }
    New-Item -ItemType Directory -Path (Split-Path $e.src -Parent) -Force | Out-Null
    Copy-Item -LiteralPath $dstFull -Destination $e.src -Recurse -Force
    Log ("RESTORED: {0} -> {1}" -f $dstFull, $e.src)
    $restored++
  }
}
Log ("===== 完成：恢复 {0} 项，C盘已存在跳过 {1} 项，无对应备份跳过 {2} 项 =====" -f $restored, $already, $noop)
