param([switch]$NoBrowser)
$ErrorActionPreference='Stop'
$appDirectory=$PSScriptRoot
$runtimeDirectory=Join-Path $appDirectory '.runtime'
New-Item -ItemType Directory -Path $runtimeDirectory -Force | Out-Null
$ready=$false
try{$health=Invoke-RestMethod -Uri 'http://127.0.0.1:4176/health' -TimeoutSec 2; $ready=$health.app -eq 'gesture-synth-local'}catch{}
if(-not $ready){
  $nodeCommand=(Get-Command node.exe -ErrorAction Stop).Source
  $scriptPath=Join-Path $appDirectory 'serve.mjs'
  $process=Start-Process -FilePath $nodeCommand -ArgumentList @('"'+$scriptPath+'"') -WorkingDirectory $appDirectory -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtimeDirectory 'server.log') -RedirectStandardError (Join-Path $runtimeDirectory 'server-error.log') -PassThru
  Set-Content -LiteralPath (Join-Path $runtimeDirectory 'server.pid') -Value $process.Id
  for($attempt=0;$attempt -lt 20;$attempt++){
    Start-Sleep -Milliseconds 250
    try{$health=Invoke-RestMethod -Uri 'http://127.0.0.1:4176/health' -TimeoutSec 1;if($health.app -eq 'gesture-synth-local'){$ready=$true;break}}catch{}
  }
}
if(-not $ready){throw 'Gesture Synth could not start. Check .runtime/server-error.log or port 4176.'}
Write-Output 'Gesture Synth: http://127.0.0.1:4176'
if(-not $NoBrowser){Start-Process 'http://127.0.0.1:4176'}
