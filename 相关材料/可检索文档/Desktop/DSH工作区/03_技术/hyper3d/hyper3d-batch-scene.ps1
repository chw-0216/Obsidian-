# Hyper3D 场景资产批量生成（纯文本 → 3D）
#
# 与 hyper3d-batch.ps1 的区别：
#   - 本脚本走"纯文本生成"，不需要参考图（已实测 CLI 支持 --prompt 单独使用）
#   - 所有道具共享同一段风格前缀，用于约束"放在一起像同一个世界"
#
# 安全设计：每项只提交一次，失败即停并继续下一项，绝不自动重跑。
# 用法:
#   pwsh -File hyper3d-batch-scene.ps1 -DryRun
#   pwsh -File hyper3d-batch-scene.ps1
#   pwsh -File hyper3d-batch-scene.ps1 -Only s1-01,s1-02

param(
  [string[]]$Only = @(),
  [switch]$DryRun,
  [int]$PollTimeoutSeconds = 1200
)

$ErrorActionPreference = 'Continue'
$cli = 'C:\Users\wardc\Documents\New project gpt\AI-archive\apps\hyper3d-cli\hyper3d.cmd'
$projectDir = 'C:\Users\wardc\Documents\Codex\2026-09-22\digital-human-design'

# 统一风格前缀：与主角色的"象牙白层片 / 炭黑地层 / 朱红内缝 / 哑光纤维"语言一致
$style = 'Stylized sculptural museum prop for a layered-memory gallery. Material language: warm ivory paper and plaster over visible charcoal-black strata, one narrow cinnabar-red seam, matte tactile fibrous surfaces, torn layered edges, refined art-object finish. Single standalone object, centered, no text, no people, no duplicates.'

$batch = @(
  @{ name='s1-01-pedestal';  prompt="A cylindrical display pedestal, two tiers, slightly irregular hand-formed edges, about waist height. $style" }
  @{ name='s1-02-bench';     prompt="A low rectangular gallery bench with slab legs, solid blocky form, subtle paper-layer texture on the seat edge. $style" }
  @{ name='s1-03-lamp';      prompt="A slim floor lamp on a round base with a conical paper shade, matte and unlit, simple silhouette. $style" }
  @{ name='s1-04-barrier';   prompt="A freestanding exhibition barrier post with a retractable belt housing on top, simple geometric body. $style" }
  @{ name='s1-05-reel';      prompt="A large empty cable reel standing upright like a round display disc, layered paper sides. $style" }
  @{ name='s1-06-crate';     prompt="A solid wooden storage crate with visible plank lines and a simple lid, blocky proportions. $style" }
  @{ name='s1-07-headphones';prompt="A pair of over-ear studio headphones resting on a small round stand, chunky simplified forms. $style" }
  @{ name='s1-08-camera';    prompt="A vintage twin-lens reflex camera standing upright on a small base, two round lenses stacked, simplified geometric body. $style" }
)

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

Write-Host "=== 场景资产批次（$($targets.Count) 项，预计 $([math]::Round($targets.Count * 0.5,1)) 额度） ==="
foreach ($t in $targets) { Write-Host ("  {0,-18} {1}" -f $t.name, $t.prompt.Substring(0, [Math]::Min(72, $t.prompt.Length))) }

if ($DryRun) { Write-Host "`n[DryRun] 未提交。" ; exit 0 }

$auth = Invoke-H3d @('auth','status','--output','json')
if ($auth.text -notmatch '"authenticated"\s*:\s*true') { Write-Host "未授权，停止。" -ForegroundColor Red; exit 1 }
$m0 = [regex]::Match($auth.text, '"subscription_balance"\s*:\s*([0-9.]+)')
$startBalance = if ($m0.Success) { [double]$m0.Groups[1].Value } else { -1 }
Write-Host "`n=== 开始前额度: $startBalance ==="

$root = Join-Path $projectDir 'work\batch-scene'
if (-not (Test-Path $root)) { New-Item -ItemType Directory -Path $root -Force | Out-Null }

$results = @()
$globalStart = Get-Date

foreach ($t in $targets) {
  $dir = Join-Path $root $t.name
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  Write-Host ""
  Write-Host ("########## {0} ##########" -f $t.name) -ForegroundColor Cyan

  $t0 = Get-Date
  # 统一用 100k 三角面：控制得当、进场景前再减面即可
  $gen = Invoke-H3d @('generate', '--prompt', $t.prompt, '--tier', 'Gen-2.5-Medium',
                      '--mesh-mode', 'Raw', '--quality', '100000', '--format', 'glb', '--output', 'json')
  Set-Content -Path (Join-Path $dir 'generate.raw.txt') -Value $gen.text -Encoding UTF8
  Set-Content -Path (Join-Path $dir 'prompt.txt') -Value $t.prompt -Encoding UTF8
  Write-Host $gen.text

  if ($gen.code -ne 0) {
    Write-Host "  提交失败（退出码 $($gen.code)），不重试，继续。" -ForegroundColor Red
    $results += [pscustomobject]@{ name=$t.name; outcome='submit-failed'; seconds=[int]((Get-Date)-$t0).TotalSeconds }
    continue
  }
  $id = Get-JsonField -Text $gen.text -Field 'generation_id'
  if (-not $id) {
    Write-Host "  未解析出 generation_id，存盘待人工确认，继续。" -ForegroundColor Yellow
    $results += [pscustomobject]@{ name=$t.name; outcome='id-unparsed'; seconds=[int]((Get-Date)-$t0).TotalSeconds }
    continue
  }
  Write-Host "  generation_id = $id" -ForegroundColor Green
  Set-Content -Path (Join-Path $dir 'generation-id.txt') -Value $id -Encoding UTF8

  $poll = Invoke-H3d @('poll', $id, '--timeout', "$PollTimeoutSeconds", '--output', 'json')
  Set-Content -Path (Join-Path $dir 'poll.raw.txt') -Value $poll.text -Encoding UTF8
  $res = Invoke-H3d @('result', $id, '--output', 'json')
  Set-Content -Path (Join-Path $dir 'result.raw.txt') -Value $res.text -Encoding UTF8

  $saved = 0
  foreach ($ch in ($res.text -split '\},\s*\{')) {
    $nm = [regex]::Match($ch, '"name"\s*:\s*"([^"]+\.glb)"')
    $ur = [regex]::Match($ch, '"url"\s*:\s*"(https?://[^"]+)"')
    if ($nm.Success -and $ur.Success) {
      $kind = if ($nm.Groups[1].Value -match 'shaded') { 'shaded' } else { 'pbr' }
      $dest = Join-Path $dir ("$($t.name)-$kind.glb")
      try {
        Invoke-WebRequest -Uri $ur.Groups[1].Value -OutFile $dest -TimeoutSec 1200 -UseBasicParsing
        Write-Host "  已下载 $kind ($((Get-Item $dest).Length) 字节)" -ForegroundColor Green
        $saved++
      } catch { Write-Host "  下载失败 $kind -> $($_.Exception.Message)" -ForegroundColor Red }
    }
  }
  $secs = [int]((Get-Date)-$t0).TotalSeconds
  Write-Host "  用时 $secs 秒" -ForegroundColor Cyan
  $results += [pscustomobject]@{ name=$t.name; outcome=($(if ($saved -gt 0) { 'ok' } else { 'no-download' })); seconds=$secs }
}

$results | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $root 'scene-manifest.json') -Encoding UTF8
$auth2 = Invoke-H3d @('auth','status','--output','json')
$m1 = [regex]::Match($auth2.text, '"subscription_balance"\s*:\s*([0-9.]+)')
$endBalance = if ($m1.Success) { [double]$m1.Groups[1].Value } else { -1 }

Write-Host ""
Write-Host "=== 批次完成 ===" -ForegroundColor Cyan
$results | Format-Table -AutoSize | Out-String -Width 120 | Write-Host
Write-Host "总用时 $([int]((Get-Date)-$globalStart).TotalSeconds) 秒"
Write-Host "额度: $startBalance -> $endBalance  消耗 $(if ($startBalance -ge 0 -and $endBalance -ge 0) { [math]::Round($startBalance-$endBalance,2) } else { '未知' })"
Write-Host "产物: $root"
