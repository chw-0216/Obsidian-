# ============================================================
# 恢复脚本: 把此前"迁移模式"下已 MOVED(删原件)的条目从 D: 复制回原位
# 硬盘上的分类副本保留(它本身就是备份), 电脑原件恢复
# ============================================================
$ErrorActionPreference = 'Continue'
$csvs = Get-ChildItem 'D:\资料整理_2026-08-17\00_总清单\迁移日志*.csv' | Sort-Object Name
$rows = @()
foreach ($c in $csvs) { $rows += @(Import-Csv $c.FullName | Where-Object { $_.状态 -eq 'MOVED' }) }
$log = 'D:\资料整理_2026-08-17\00_总清单\恢复日志.txt'
function L([string]$m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Out-File -LiteralPath $log -Append -Encoding utf8 }

L "===== 恢复开始, MOVED 条目 $($rows.Count) 条 ====="
$done = 0
foreach ($r in $rows) {
  $src = $r.原路径
  $dst = $r.新路径
  try {
    if ($src -like '*\*') {
      # 通配符条目: 原路径是模式, 新路径是目录; 把目录内文件复制回原父目录
      $parent = Split-Path -Parent $src
      New-Item -ItemType Directory -Path $parent -Force | Out-Null
      $n = 0
      Get-ChildItem -LiteralPath $dst -File -Force -ErrorAction SilentlyContinue | ForEach-Object {
        $target = Join-Path $parent $_.Name
        if (-not (Test-Path -LiteralPath $target)) { Copy-Item -LiteralPath $_.FullName -Destination $target -Force; $n++ }
      }
      L "恢复(通配): [$dst] -> [$parent] 复制 $n 个"
      $done++
    }
    elseif (Test-Path -LiteralPath $src) {
      L "原路径已存在,跳过: $src"
      $done++
    }
    elseif (-not (Test-Path -LiteralPath $dst)) {
      L "目标也不存在,无法恢复: $dst"
    }
    else {
      $item = Get-Item -LiteralPath $dst -Force
      $p = Split-Path -Parent $src
      New-Item -ItemType Directory -Path $p -Force | Out-Null
      if ($item -is [System.IO.FileInfo]) {
        Copy-Item -LiteralPath $dst -Destination $src -Force
      } else {
        robocopy $dst $src /E /COPY:DAT /DCOPY:DAT /XJ /R:2 /W:3 /MT:16 /NP /NFL /NDL | Out-Null
      }
      $ok = (Test-Path -LiteralPath $src)
      L "恢复: [$dst] -> [$src] $($(if($ok){'OK'}else{'FAIL'}))"
      if ($ok) { $done++ }
    }
  } catch { L "异常: $src :: $($_.Exception.Message)" }
}
L "===== 恢复完成 $done/$($rows.Count) ====="
