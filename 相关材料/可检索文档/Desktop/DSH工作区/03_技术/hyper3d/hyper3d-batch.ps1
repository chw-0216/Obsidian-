# Hyper3D 批量生成（清单驱动）
#
# 设计要点：
#   - 清单在文件顶部 batch 数组里，一项 = 一次计费提交
#   - 每项独立子目录，保存 generate/poll/result 原始输出 + 下载产物
#   - 每项只提交一次，失败即停并继续下一项（不重试，防止重复扣额度）
#   - 支持 --only 名称过滤，便于分批执行
#   - 结束时打印额度消耗与逐项结构核对
#
# 用法:
#   pwsh -File hyper3d-batch.ps1
#   pwsh -File hyper3d-batch.ps1 -Only w1-01,w1-02
#   pwsh -File hyper3d-batch.ps1 -DryRun          # 只打印计划，不提交

param(
  [string[]]$Only = @(),
  [switch]$DryRun,
  [int]$PollTimeoutSeconds = 1200
)

$ErrorActionPreference = 'Continue'
$cli = 'C:\Users\wardc\Documents\New project gpt\AI-archive\apps\hyper3d-cli\hyper3d.cmd'
$projectDir = 'C:\Users\wardc\Documents\Codex\2026-09-22\digital-human-design'

# 已实测无"合面"缺陷的单人正面参考图
$singleView = Join-Path $projectDir 'assets\layered-witness-single-view-v2.png'

# 与项目既有产物完全一致的角色提示词
$bustPrompt = 'Create one standalone stylized human bust sculpture based on the uploaded reference image; exactly one head, do not reproduce multiple faces or multiple views. Bust only, head, neck and upper shoulders, centered, with a coherent androgynous feminine face, calm neutral expression, simplified sculptural features and a bald head. Wrap the skull, neck and shoulders in irregular torn layers of warm ivory paper and plaster, with visible charcoal-black strata and one narrow cinnabar-red inner seam along the viewer-left temple/ear continuing down the neck. Matte tactile fibrous surfaces, layered cut edges, refined art-object finish. Preserve the design language and overall proportions of the reference. Single object, no props, no text, no extra heads or duplicate views.'

# ============================ 批次清单 ============================
# 字段: name, mode(image|text), 参数, note
$batch = @(
  # ---- 波次 1：角色资产矩阵（同一参考图，覆盖绑定/展示/轻量三种用途）----
  @{ name='w1-01-raw-40k';    mode='image'; tier='Gen-2.5-Medium'; mesh='Raw';  quality=40000;  note='绑定用低面底模，目标 4 万三角面' }
  @{ name='w1-02-raw-100k';   mode='image'; tier='Gen-2.5-Medium'; mesh='Raw';  quality=100000; note='绑定底模基线，与既有 bind-100k 对照' }
  @{ name='w1-03-raw-300k';   mode='image'; tier='Gen-2.5-Medium'; mesh='Raw';  quality=300000; note='高保真展示底模' }
  @{ name='w1-04-quad-6k';    mode='image'; tier='Gen-2.5-Medium'; mesh='Quad'; quality=6000;   note='四边形超低面，测 Quad 下限' }
  @{ name='w1-05-quad-12k';   mode='image'; tier='Gen-2.5-Medium'; mesh='Quad'; quality=12000;  note='四边形低面，绑定候选' }
  @{ name='w1-06-quad-30k';   mode='image'; tier='Gen-2.5-Medium'; mesh='Quad'; quality=30000;  note='四边形中面' }
  @{ name='w1-07-quad-50k';   mode='image'; tier='Gen-2.5-Medium'; mesh='Quad'; quality=50000;  note='四边形上限' }
  @{ name='w1-08-high-raw-100k'; mode='image'; tier='Gen-2.5-High'; mesh='Raw'; quality=100000; note='High 档在同面数下的细节密度' }
)
# ==================================================================

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

$targets = if ($Only.Count -gt 0) { $batch | Where-Object { $Only -contains $_.name } } else { $batch }

Write-Host "=== 批次计划（$($targets.Count) 项，预计消耗 $($targets.Count * 0.5) 额度） ==="
foreach ($t in $targets) {
  Write-Host ("  {0,-22} {1,-9} {2,-5} quality={3,-7}  {4}" -f $t.name, $t.tier, $t.mesh, $t.quality, $t.note)
}

if ($DryRun) { Write-Host "`n[DryRun] 未提交任何任务。" ; exit 0 }

if (-not (Test-Path $singleView)) { Write-Host "找不到参考图: $singleView" -ForegroundColor Red; exit 1 }
$auth = Invoke-H3d @('auth','status','--output','json')
if ($auth.text -notmatch '"authenticated"\s*:\s*true') { Write-Host "未授权，停止。" -ForegroundColor Red; Write-Host $auth.text; exit 1 }

$before = [regex]::Match($auth.text, '"subscription_balance"\s*:\s*([0-9.]+)')
$startBalance = if ($before.Success) { [double]$before.Groups[1].Value } else { -1 }
Write-Host "`n=== 开始前额度: $startBalance ==="

$batchRoot = Join-Path $projectDir 'work\batch-char'
if (-not (Test-Path $batchRoot)) { New-Item -ItemType Directory -Path $batchRoot -Force | Out-Null }

$results = @()
$globalStart = Get-Date

foreach ($t in $targets) {
  $dir = Join-Path $batchRoot $t.name
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  Write-Host ""
  Write-Host ("########## {0} ##########" -f $t.name) -ForegroundColor Cyan
  Write-Host "  $($t.note)"

  $t0 = Get-Date
  $genArgs = @(
    'generate',
    '--image', $singleView,
    '--prompt', $bustPrompt,
    '--tier', $t.tier,
    '--mesh-mode', $t.mesh,
    '--quality', "$($t.quality)",
    '--format', 'glb',
    '--output', 'json'
  )
  $gen = Invoke-H3d $genArgs
  Set-Content -Path (Join-Path $dir 'generate.raw.txt') -Value $gen.text -Encoding UTF8
  Write-Host $gen.text

  if ($gen.code -ne 0) {
    Write-Host "  提交失败（退出码 $($gen.code)）。按设计不重试，继续下一项。" -ForegroundColor Red
    Write-Host "  请到 Hyper3D 工作区确认是否已创建任务。" -ForegroundColor Yellow
    $results += [pscustomobject]@{ name=$t.name; tier=$t.tier; mesh=$t.mesh; quality=$t.quality; generation_id=$null; outcome='submit-failed'; seconds=[int]((Get-Date)-$t0).TotalSeconds; files='' }
    continue
  }

  $genId = Get-JsonField -Text $gen.text -Field 'generation_id'
  if (-not $genId) {
    Write-Host "  未解析出 generation_id，存盘待人工确认，继续下一项。" -ForegroundColor Yellow
    $results += [pscustomobject]@{ name=$t.name; tier=$t.tier; mesh=$t.mesh; quality=$t.quality; generation_id=$null; outcome='id-unparsed'; seconds=[int]((Get-Date)-$t0).TotalSeconds; files='' }
    continue
  }
  Write-Host "  generation_id = $genId" -ForegroundColor Green
  Set-Content -Path (Join-Path $dir 'generation-id.txt') -Value $genId -Encoding UTF8

  $poll = Invoke-H3d @('poll', $genId, '--timeout', "$PollTimeoutSeconds", '--output', 'json')
  Set-Content -Path (Join-Path $dir 'poll.raw.txt') -Value $poll.text -Encoding UTF8
  $res = Invoke-H3d @('result', $genId, '--output', 'json')
  Set-Content -Path (Join-Path $dir 'result.raw.txt') -Value $res.text -Encoding UTF8

  $saved = @()
  $chunks = ($res.text -split '\},\s*\{')
  foreach ($ch in $chunks) {
    $nm = [regex]::Match($ch, '"name"\s*:\s*"([^"]+\.glb)"')
    $ur = [regex]::Match($ch, '"url"\s*:\s*"(https?://[^"]+)"')
    if ($nm.Success -and $ur.Success) {
      $kind = if ($nm.Groups[1].Value -match 'shaded') { 'shaded' } else { 'pbr' }
      $dest = Join-Path $dir ("$($t.name)-$kind.glb")
      try {
        Invoke-WebRequest -Uri $ur.Groups[1].Value -OutFile $dest -TimeoutSec 1200 -UseBasicParsing
        $len = (Get-Item $dest).Length
        Write-Host "  已下载 $kind ($len 字节)" -ForegroundColor Green
        $saved += [pscustomobject]@{ kind=$kind; file=$dest; bytes=$len }
      } catch { Write-Host "  下载失败 $kind -> $($_.Exception.Message)" -ForegroundColor Red }
    }
  }

  $secs = [int]((Get-Date)-$t0).TotalSeconds
  $results += [pscustomobject]@{
    name=$t.name; tier=$t.tier; mesh=$t.mesh; quality=$t.quality
    generation_id=$genId; outcome=($(if ($saved.Count -gt 0) { 'ok' } else { 'no-download' })); seconds=$secs
    files=($saved | ForEach-Object { $_.file }) -join ';'
    bytes=($saved | ForEach-Object { $_.bytes }) -join ';'
  }
  Write-Host "  用时 $secs 秒" -ForegroundColor Cyan
}

$results | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $batchRoot 'batch-manifest.json') -Encoding UTF8

$auth2 = Invoke-H3d @('auth','status','--output','json')
$after = [regex]::Match($auth2.text, '"subscription_balance"\s*:\s*([0-9.]+)')
$endBalance = if ($after.Success) { [double]$after.Groups[1].Value } else { -1 }

Write-Host ""
Write-Host "=== 批次完成 ===" -ForegroundColor Cyan
$results | Format-Table name,tier,mesh,quality,outcome,seconds -AutoSize | Out-String -Width 140 | Write-Host
Write-Host "总用时 $([int]((Get-Date)-$globalStart).TotalSeconds) 秒"
Write-Host "额度: $startBalance -> $endBalance  消耗 $(if ($startBalance -ge 0 -and $endBalance -ge 0) { [math]::Round($startBalance-$endBalance,2) } else { '未知' })"
Write-Host "清单: $(Join-Path $batchRoot 'batch-manifest.json')"
