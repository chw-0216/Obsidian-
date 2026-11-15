# 一次性生成：单人正面参考图 → Raw / 100,000 三角面绑定底模
#
# 依据（均来自本项目实测）：
#   - 单人正面参考图不会触发"三面合一"缺陷（三视图拼版会）
#   - Raw 模式下 --quality 目标值与实际三角面数精确相等，单位是三角面而非索引
#   - 1 次生成同时返回 PBR 与着色两份 GLB
#
# 安全设计：只提交一次，失败即停，绝不自动重跑。1 次计费 = 0.5 额度。

$ErrorActionPreference = 'Continue'
$cli = 'C:\Users\wardc\Documents\New project gpt\AI-archive\apps\hyper3d-cli\hyper3d.cmd'
$projectDir = 'C:\Users\wardc\Documents\Codex\2026-09-22\digital-human-design'
$image = Join-Path $projectDir 'assets\layered-witness-single-view-v2.png'
$outDir = Join-Path $projectDir 'work\singlescan-bind100k'

$prompt = 'Create one standalone stylized human bust sculpture based on the uploaded reference image; exactly one head, do not reproduce multiple faces or multiple views. Bust only, head, neck and upper shoulders, centered, with a coherent androgynous feminine face, calm neutral expression, simplified sculptural features and a bald head. Wrap the skull, neck and shoulders in irregular torn layers of warm ivory paper and plaster, with visible charcoal-black strata and one narrow cinnabar-red inner seam along the viewer-left temple/ear continuing down the neck. Matte tactile fibrous surfaces, layered cut edges, refined art-object finish. Preserve the design language and overall proportions of the reference. Single object, no props, no text, no extra heads or duplicate views.'

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

if (-not (Test-Path $image)) { Write-Host "找不到参考图: $image" -ForegroundColor Red; exit 1 }
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

Write-Host "=== 参考图: $image（$((Get-Item $image).Length) 字节）"
Write-Host "=== 输出目录: $outDir"
Write-Host "=== 规格: tier=Gen-2.5-Medium mesh=Raw quality=100000 format=glb"

$before = Invoke-H3d @('auth','status','--output','json')
Write-Host "=== 生成前额度 ==="
Write-Host $before.text
if ($before.text -notmatch '"authenticated"\s*:\s*true') { Write-Host "未授权，停止。" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "=== 提交生成（只提交一次） ==="
$t0 = Get-Date
$gen = Invoke-H3d @(
  'generate',
  '--image', $image,
  '--prompt', $prompt,
  '--tier', 'Gen-2.5-Medium',
  '--mesh-mode', 'Raw',
  '--quality', '100000',
  '--format', 'glb',
  '--output', 'json'
)
Set-Content -Path (Join-Path $outDir 'generate.raw.txt') -Value $gen.text -Encoding UTF8
Write-Host $gen.text
if ($gen.code -ne 0) {
  Write-Host "generate 失败，退出码 $($gen.code)。按设计不重试。" -ForegroundColor Red
  Write-Host "请先到 Hyper3D 工作区确认是否已创建任务，再决定下一步。" -ForegroundColor Yellow
  exit 1
}

$genId = Get-JsonField -Text $gen.text -Field 'generation_id'
if (-not $genId) {
  Write-Host "未解析出 generation_id。原始输出已存盘，请人工确认，不要重复提交。" -ForegroundColor Yellow
  exit 1
}
Write-Host "[generation_id] $genId" -ForegroundColor Green
Set-Content -Path (Join-Path $outDir 'generation-id.txt') -Value $genId -Encoding UTF8

$poll = Invoke-H3d @('poll', $genId, '--timeout', '900', '--output', 'json')
Set-Content -Path (Join-Path $outDir 'poll.raw.txt') -Value $poll.text -Encoding UTF8
$t1 = Get-Date
Write-Host "=== poll 返回（耗时 $([int]($t1-$t0).TotalSeconds) 秒） ==="
Write-Host $poll.text

$res = Invoke-H3d @('result', $genId, '--output', 'json')
Set-Content -Path (Join-Path $outDir 'result.raw.txt') -Value $res.text -Encoding UTF8
Write-Host "=== result 返回 ==="
Write-Host $res.text

$urls = [regex]::Matches($res.text, 'https?://[^"\s\\]+?\.glb[^"\s\\]*') | ForEach-Object { $_.Value } | Select-Object -Unique
if ($urls.Count -eq 0) { Write-Host "未取到下载链接。" -ForegroundColor Red; exit 1 }

$n = 0
$saved = @()
foreach ($u in $urls) {
  $n++
  $name = if ($n -eq 1) { 'bind-100k-pbr.glb' } else { 'bind-100k-shaded.glb' }
  $dest = Join-Path $outDir $name
  try {
    Invoke-WebRequest -Uri $u -OutFile $dest -TimeoutSec 600 -UseBasicParsing
    $len = (Get-Item $dest).Length
    Write-Host "已下载 $name ($len 字节)" -ForegroundColor Green
    $saved += [pscustomobject]@{ file=$dest; bytes=$len }
  } catch {
    Write-Host "下载失败: $($_.Exception.Message)" -ForegroundColor Red
  }
}

$t2 = Get-Date
[pscustomobject]@{
  generation_id = $genId
  tier = 'Gen-2.5-Medium'; mesh = 'Raw'; quality = 100000; format = 'glb'
  image = $image
  generate_to_result_seconds = [int]($t1-$t0).TotalSeconds
  total_seconds = [int]($t2-$t0).TotalSeconds
  files = ($saved | ForEach-Object { $_.file }) -join ';'
  bytes = ($saved | ForEach-Object { $_.bytes }) -join ';'
} | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $outDir 'run-manifest.json') -Encoding UTF8

Write-Host ""
Write-Host "=== 生成后额度 ==="
Write-Host (Invoke-H3d @('auth','status','--output','json')).text
Write-Host "=== 完成，用时 $([int]($t2-$t0).TotalSeconds) 秒 ===" -ForegroundColor Cyan
