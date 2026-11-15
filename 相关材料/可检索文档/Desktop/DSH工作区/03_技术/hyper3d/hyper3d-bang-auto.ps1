# BANG 自动拆分对照：不带 --instruction，仅给 --strength 5
# 目的：判定本次 8 个部件是"我的语义描述导致"还是"算法默认就这样切"
# 计费：BANG 每次固定 0.5 额度。只提交一次，失败即停。

$ErrorActionPreference = 'Continue'
$cli = 'C:\Users\wardc\Documents\New project gpt\AI-archive\apps\hyper3d-cli\hyper3d.cmd'
$outDir = 'C:\Users\wardc\Documents\Codex\2026-09-22\digital-human-design\work\bang-auto'
$sourceGenId = 'cd20c16e-1bd8-47ab-8463-e7a72214ef04'

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

$before = Invoke-H3d @('auth','status','--output','json')
Write-Host "=== 提交前额度 ==="
Write-Host $before.text
if ($before.text -notmatch '"authenticated"\s*:\s*true') { Write-Host "未授权，停止。" -ForegroundColor Red; exit 1 }

Write-Host "=== 提交 BANG（自动拆分，无 instruction） ==="
$t0 = Get-Date
$bang = Invoke-H3d @('bang', $sourceGenId, '--strength', '5', '--format', 'glb', '--output', 'json')
Set-Content -Path (Join-Path $outDir 'bang.raw.txt') -Value $bang.text -Encoding UTF8
Write-Host $bang.text
if ($bang.code -ne 0) { Write-Host "提交失败，退出码 $($bang.code)，不重试。" -ForegroundColor Red; exit 1 }

$bangId = Get-JsonField -Text $bang.text -Field 'generation_id'
if (-not $bangId) { Write-Host "未解析出 generation_id，请人工确认，不要重复提交。" -ForegroundColor Yellow; exit 1 }
Write-Host "[BANG auto generation_id] $bangId" -ForegroundColor Green
Set-Content -Path (Join-Path $outDir 'generation-id.txt') -Value $bangId -Encoding UTF8

$poll = Invoke-H3d @('poll', $bangId, '--timeout', '1200', '--output', 'json')
Set-Content -Path (Join-Path $outDir 'poll.raw.txt') -Value $poll.text -Encoding UTF8
$t1 = Get-Date
Write-Host "=== poll（耗时 $([int]($t1-$t0).TotalSeconds) 秒） ==="
Write-Host $poll.text

$res = Invoke-H3d @('result', $bangId, '--output', 'json')
Set-Content -Path (Join-Path $outDir 'result.raw.txt') -Value $res.text -Encoding UTF8
Write-Host "=== result ==="
Write-Host $res.text

$saved = @()
$chunks = ($res.text -split '\},\s*\{')
$i = 0
foreach ($ch in $chunks) {
  $nm = [regex]::Match($ch, '"name"\s*:\s*"([^"]+\.glb)"')
  $ur = [regex]::Match($ch, '"url"\s*:\s*"(https?://[^"]+)"')
  if ($nm.Success -and $ur.Success) {
    $i++
    $dest = Join-Path $outDir ("auto-{0:d2}-{1}" -f $i, $nm.Groups[1].Value)
    try {
      Invoke-WebRequest -Uri $ur.Groups[1].Value -OutFile $dest -TimeoutSec 900 -UseBasicParsing
      $len = (Get-Item $dest).Length
      Write-Host "已下载 $($nm.Groups[1].Value) ($len 字节)" -ForegroundColor Green
      $saved += [pscustomobject]@{ file=$dest; name=$nm.Groups[1].Value; bytes=$len }
    } catch { Write-Host "下载失败 -> $($_.Exception.Message)" -ForegroundColor Red }
  }
}

[pscustomobject]@{
  source_generation_id = $sourceGenId
  bang_generation_id = $bangId
  mode = 'automatic (no instruction)'
  strength = 5
  seconds = [int]((Get-Date)-$t0).TotalSeconds
  files = $saved
} | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $outDir 'bang-manifest.json') -Encoding UTF8

Write-Host "=== 提交后额度 ==="
Write-Host (Invoke-H3d @('auth','status','--output','json')).text
Write-Host "=== 完成，用时 $([int]((Get-Date)-$t0).TotalSeconds) 秒 ===" -ForegroundColor Cyan
