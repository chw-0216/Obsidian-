# Hyper3D 参数对比扫描（A–E）
#
# 目的：用同一张概念图与同一段提示词，横向对比 tier / mesh-mode / quality 的产物差异。
#
# 安全设计（重要）：
#   1. 每项只调用一次 `generate`。脚本绝不重试提交，避免重复扣额度。
#   2. 提交失败或超时不会自动重跑；需人工确认后再决定。
#   3. 轮询用 poll，（按官方说明）轮询超时不等于任务取消，可再次 poll 续跟。
#   4. 产物写入项目 work/hyper3d-scan/，不动 assets/，因此既有手册与 README 仍然准确。
#
# 用法：
#   pwsh -File hyper3d-param-scan.ps1
#   pwsh -File hyper3d-param-scan.ps1 -Only A,C      # 只跑指定项

param(
  [string[]]$Only = @('A','B','C','D','E'),
  [int]$PollTimeoutSeconds = 900,
  [string]$ImagePath = 'C:\Users\wardc\Documents\Codex\2026-09-22\digital-human-design\outputs\layered-witness-concept-v1.png',
  [string]$OutDir = 'C:\Users\wardc\Documents\Codex\2026-09-22\digital-human-design\work\hyper3d-scan'
)

$ErrorActionPreference = 'Continue'
$cli = 'C:\Users\wardc\Documents\New project gpt\AI-archive\apps\hyper3d-cli\hyper3d.cmd'

# 与手册第 4 节完全一致的提示词，保证与既有产物可比
$prompt = 'Create one standalone stylized human bust sculpture based on the uploaded multi-view concept sheet; do not reproduce the collage or create multiple faces. Bust only, head, neck and upper shoulders, centered, with a coherent androgynous feminine face, calm neutral expression, simplified sculptural features and a bald head. Wrap the skull, neck and shoulders in irregular torn layers of warm ivory paper and plaster, with visible charcoal-black strata and one narrow cinnabar-red inner seam along the viewer-left temple/ear continuing down the neck. Matte tactile fibrous surfaces, layered cut edges, refined art-object finish. Preserve the design language and overall proportions of the reference. Single object, no props, no text, no extra heads or duplicate views.'

$matrix = [ordered]@{
  A = @{ tier='Gen-2.5-Medium'; mesh='Raw';  quality=500000; note='基线：应最接近现有 PBR 版' }
  B = @{ tier='Gen-2.5-Medium'; mesh='Quad'; quality=18000;  note='四边面默认量，看拓扑可用性' }
  C = @{ tier='Gen-2.5-Medium'; mesh='Quad'; quality=50000;  note='四边面高量，绑定候选' }
  D = @{ tier='Gen-2.5-High';   mesh='Raw';  quality=500000; note='同面数下的细节提升' }
  E = @{ tier='Gen-2.5-Medium'; mesh='Raw';  quality=100000; note='验证 --quality 降面是否生效' }
}

function Invoke-H3d {
  param([string[]]$CliArgs, [int]$TimeoutSec = 120)
  # stderr 与 stdout 合并捕获；不抛异常，交由调用方按退出码判断
  $out = & $cli @CliArgs 2>&1 | Out-String
  return @{ text = $out; code = $LASTEXITCODE }
}

function Get-JsonField {
  param([string]$Text, [string]$Field)
  $m = [regex]::Match($Text, '"' + [regex]::Escape($Field) + '"\s*:\s*"([^"]+)"')
  if ($m.Success) { return $m.Groups[1].Value }
  return $null
}

if (-not (Test-Path $cli))   { Write-Host "找不到 CLI: $cli" -ForegroundColor Red; exit 1 }
if (-not (Test-Path $ImagePath)) { Write-Host "找不到参考图: $ImagePath" -ForegroundColor Red; exit 1 }
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }

Write-Host "=== 参考图: $ImagePath"
Write-Host "=== 输出目录: $OutDir"

$status = Invoke-H3d @('auth','status','--output','json')
if ($status.text -notmatch '"authenticated"\s*:\s*true') {
  Write-Host "未授权或会话失效，请先运行 hyper3d auth login。当前返回：" -ForegroundColor Red
  Write-Host $status.text
  exit 1
}
Write-Host "=== 授权正常"

$runs = @()

foreach ($key in $matrix.Keys) {
  if ($Only -notcontains $key) { continue }
  $cfg = $matrix[$key]
  $runDir = Join-Path $OutDir $key
  if (-not (Test-Path $runDir)) { New-Item -ItemType Directory -Path $runDir -Force | Out-Null }

  Write-Host ""
  Write-Host "########## [$key] tier=$($cfg.tier) mesh=$($cfg.mesh) quality=$($cfg.quality) ##########" -ForegroundColor Cyan
  Write-Host "         备注: $($cfg.note)"

  $gen = Invoke-H3d @(
    'generate',
    '--image', $ImagePath,
    '--prompt', $prompt,
    '--tier', $cfg.tier,
    '--mesh-mode', $cfg.mesh,
    '--quality', "$($cfg.quality)",
    '--format', 'glb',
    '--output', 'json'
  )

  Set-Content -Path (Join-Path $runDir 'generate.raw.txt') -Value $gen.text -Encoding UTF8
  Write-Host "--- generate 原始输出 ---"
  Write-Host $gen.text

  if ($gen.code -ne 0) {
    Write-Host "[$key] generate 失败（退出码 $($gen.code)）。按安全设计不重试。" -ForegroundColor Red
    Write-Host "请先到 Hyper3D 工作区确认该请求是否已创建任务，再决定是否重跑。" -ForegroundColor Yellow
    $runs += [pscustomobject]@{ key=$key; tier=$cfg.tier; mesh=$cfg.mesh; quality=$cfg.quality; generation_id=$null; outcome='generate-failed' }
    continue
  }

  $genId = Get-JsonField -Text $gen.text -Field 'generation_id'
  if (-not $genId) { $genId = Get-JsonField -Text $gen.text -Field 'generationId' }
  if (-not $genId) { $genId = Get-JsonField -Text $gen.text -Field 'uuid' }
  if (-not $genId) { $genId = Get-JsonField -Text $gen.text -Field 'id' }

  if (-not $genId) {
    Write-Host "[$key] 未能从输出解析出 generation id，但 generate 已成功返回。" -ForegroundColor Yellow
    Write-Host "已把原始输出存到 $runDir\generate.raw.txt，请人工确认任务状态，不要重复提交。" -ForegroundColor Yellow
    $runs += [pscustomobject]@{ key=$key; tier=$cfg.tier; mesh=$cfg.mesh; quality=$cfg.quality; generation_id=$null; outcome='id-unparsed' }
    continue
  }
  Write-Host "[$key] generation_id = $genId" -ForegroundColor Green

  $poll = Invoke-H3d @('poll', $genId, '--timeout', "$PollTimeoutSeconds", '--output', 'json')
  Set-Content -Path (Join-Path $runDir 'poll.raw.txt') -Value $poll.text -Encoding UTF8
  Write-Host "--- poll 原始输出 ---"
  Write-Host $poll.text

  $res = Invoke-H3d @('result', $genId, '--output', 'json')
  Set-Content -Path (Join-Path $runDir 'result.raw.txt') -Value $res.text -Encoding UTF8
  Write-Host "--- result 原始输出 ---"
  Write-Host $res.text

  # 抓取所有以 .glb 结尾的 URL（结果 JSON 字段名未公开，按值匹配最稳）
  $urls = [regex]::Matches($res.text, 'https?://[^"\s\\]+?\.glb[^"\s\\]*') | ForEach-Object { $_.Value } | Select-Object -Unique
  $saved = @()
  $n = 0
  foreach ($u in $urls) {
    $n++
    $dest = Join-Path $runDir ("model-" + $n + ".glb")
    try {
      Invoke-WebRequest -Uri $u -OutFile $dest -TimeoutSec 600 -UseBasicParsing
      $len = (Get-Item $dest).Length
      Write-Host "[$key] 已下载 $dest ($len 字节)" -ForegroundColor Green
      $saved += [pscustomobject]@{ file=$dest; bytes=$len }
    } catch {
      Write-Host "[$key] 下载失败: $u -> $($_.Exception.Message)" -ForegroundColor Red
    }
  }

  $runs += [pscustomobject]@{
    key=$key; tier=$cfg.tier; mesh=$cfg.mesh; quality=$cfg.quality
    generation_id=$genId
    outcome=($(if ($saved.Count -gt 0) { 'ok' } else { 'no-download' }))
    files=($saved | ForEach-Object { $_.file }) -join ';'
    bytes=($saved | ForEach-Object { $_.bytes }) -join ';'
  }
}

$manifest = Join-Path $OutDir 'scan-manifest.json'
$runs | ConvertTo-Json -Depth 4 | Set-Content -Path $manifest -Encoding UTF8
Write-Host ""
Write-Host "=== 扫描结束，清单写入 $manifest" -ForegroundColor Cyan
$runs | Format-Table -AutoSize | Out-String -Width 200 | Write-Host

Write-Host "=== 结束时额度 ===" -ForegroundColor Cyan
Write-Host (Invoke-H3d @('auth','status','--output','json')).text
