# BANG 分件实测：把 100k 底模按"层片 / 暗色地层 / 朱红内缝"拆分
#
# 目的（两条用途同时验证）：
#   1. 3D 打印分色：部件分离后可分别用不同颜色/材料打印
#   2. 视频/绑定分层：分层结构便于独立控制
#
# 计费：BANG 每次固定 0.5 额度（官方明文，与输入模式、选项无关）。
# 安全：只提交一次，失败即停，绝不自动重跑。

$ErrorActionPreference = 'Continue'
$cli = 'C:\Users\wardc\Documents\New project gpt\AI-archive\apps\hyper3d-cli\hyper3d.cmd'
$projectDir = 'C:\Users\wardc\Documents\Codex\2026-09-22\digital-human-design'
$outDir = Join-Path $projectDir 'work\bang-split'
$sourceGenId = 'cd20c16e-1bd8-47ab-8463-e7a72214ef04'   # 100k Raw 底模

$instruction = 'Separate the sculpture along its material layers: split the warm ivory paper and plaster outer layers into their own parts, separate the charcoal-black strata from the ivory layers, and isolate the narrow cinnabar-red inner seam as a single separate part. Each part must be a closed printable solid.'

function Invoke-H3d {
  param([string[]]$CliArgs)
  $out = & $cli @CliArgs 2>&1 | Out-String
  return @{ text = $out; code = $LASTEXITCODE }
}

function Get-JsonField {
  param([string]$Text, [string]$Field)
  $m = [regex]::Match($Text, '"' + [regex]::Escape($Field) + '"\s*:\s*"([^"]+)"')
  if ($m.Success) { return $m.Groups[1].Value }
  return $null
}

if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

Write-Host "=== 源模型 generation_id: $sourceGenId"
Write-Host "=== 输出目录: $outDir"
Write-Host "=== strength=5（默认）, format=glb"

$before = Invoke-H3d @('auth','status','--output','json')
Write-Host "=== 提交前额度 ==="
Write-Host $before.text
if ($before.text -notmatch '"authenticated"\s*:\s*true') { Write-Host "未授权，停止。" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "=== 提交 BANG（只提交一次） ==="
$t0 = Get-Date
$bang = Invoke-H3d @(
  'bang', $sourceGenId,
  '--instruction', $instruction,
  '--strength', '5',
  '--format', 'glb',
  '--output', 'json'
)
Set-Content -Path (Join-Path $outDir 'bang.raw.txt') -Value $bang.text -Encoding UTF8
Write-Host $bang.text
if ($bang.code -ne 0) {
  Write-Host "bang 提交失败，退出码 $($bang.code)。按设计不重试。" -ForegroundColor Red
  Write-Host "请先到 Hyper3D 工作区确认是否已创建任务，再决定下一步。" -ForegroundColor Yellow
  exit 1
}

$bangId = Get-JsonField -Text $bang.text -Field 'generation_id'
if (-not $bangId) {
  Write-Host "未解析出 BANG 的 generation_id。原始输出已存盘，请人工确认，不要重复提交。" -ForegroundColor Yellow
  exit 1
}
Write-Host "[BANG generation_id] $bangId" -ForegroundColor Green
Set-Content -Path (Join-Path $outDir 'generation-id.txt') -Value $bangId -Encoding UTF8

$poll = Invoke-H3d @('poll', $bangId, '--timeout', '1200', '--output', 'json')
Set-Content -Path (Join-Path $outDir 'poll.raw.txt') -Value $poll.text -Encoding UTF8
$t1 = Get-Date
Write-Host "=== poll 返回（耗时 $([int]($t1-$t0).TotalSeconds) 秒） ==="
Write-Host $poll.text

$res = Invoke-H3d @('result', $bangId, '--output', 'json')
Set-Content -Path (Join-Path $outDir 'result.raw.txt') -Value $res.text -Encoding UTF8
Write-Host "=== result 返回 ==="
Write-Host $res.text

# BANG 可能返回多个部件。按 JSON 条目切块解析，避免跨条目错配 name 与 url。
# 做法：以 '},' 为界切开 files 数组，每块内独立取第一个 name 与第一个 url。
$saved = @()
$chunks = ($res.text -split '\},\s*\{')
$entries = @()
foreach ($ch in $chunks) {
  $nm = [regex]::Match($ch, '"name"\s*:\s*"([^"]+\.glb)"')
  $ur = [regex]::Match($ch, '"url"\s*:\s*"(https?://[^"]+)"')
  if ($nm.Success -and $ur.Success) {
    $entries += [pscustomobject]@{ name = $nm.Groups[1].Value; url = $ur.Groups[1].Value }
  }
}

Write-Host "=== 解析到 $($entries.Count) 个部件条目 ==="
foreach ($e in $entries) { Write-Host "  - $($e.name)" }

$i = 0
foreach ($e in $entries) {
  $i++
  $dest = Join-Path $outDir ("part-{0:d2}-{1}" -f $i, $e.name)
  try {
    Invoke-WebRequest -Uri $e.url -OutFile $dest -TimeoutSec 900 -UseBasicParsing
    $len = (Get-Item $dest).Length
    Write-Host "已下载 part-$('{0:d2}' -f $i) $($e.name) ($len 字节)" -ForegroundColor Green
    $saved += [pscustomobject]@{ file=$dest; name=$e.name; bytes=$len }
  } catch {
    Write-Host "下载失败 $($e.name) -> $($_.Exception.Message)" -ForegroundColor Red
  }
}

if ($entries.Count -eq 0) {
  Write-Host "未按条目解析到部件，改用 URL 扫描作为兜底。" -ForegroundColor Yellow
  $urls = [regex]::Matches($res.text, 'https?://[^"\s\\]+?\.glb[^"\s\\]*') | ForEach-Object { $_.Value } | Select-Object -Unique
  $j = 0
  foreach ($u in $urls) {
    $j++
    $dest = Join-Path $outDir ("part-{0:d2}.glb" -f $j)
    try {
      Invoke-WebRequest -Uri $u -OutFile $dest -TimeoutSec 900 -UseBasicParsing
      $len = (Get-Item $dest).Length
      Write-Host "已下载 part-$('{0:d2}' -f $j) ($len 字节)" -ForegroundColor Green
      $saved += [pscustomobject]@{ file=$dest; name='(unnamed)'; bytes=$len }
    } catch {
      Write-Host "下载失败 -> $($_.Exception.Message)" -ForegroundColor Red
    }
  }
}

$t2 = Get-Date
[pscustomobject]@{
  source_generation_id = $sourceGenId
  bang_generation_id = $bangId
  strength = 5
  format = 'glb'
  instruction = $instruction
  bang_to_result_seconds = [int]($t1-$t0).TotalSeconds
  total_seconds = [int]($t2-$t0).TotalSeconds
  part_count = $saved.Count
  parts = $saved
} | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $outDir 'bang-manifest.json') -Encoding UTF8

Write-Host ""
Write-Host "=== 提交后额度 ==="
Write-Host (Invoke-H3d @('auth','status','--output','json')).text
Write-Host "=== 完成：取出 $($saved.Count) 个部件，用时 $([int]($t2-$t0).TotalSeconds) 秒 ===" -ForegroundColor Cyan
