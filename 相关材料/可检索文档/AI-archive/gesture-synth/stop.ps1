$ErrorActionPreference='Stop'
$pidFile=Join-Path $PSScriptRoot '.runtime\server.pid'
if(Test-Path -LiteralPath $pidFile){
  $serverPid=[int](Get-Content -LiteralPath $pidFile -Raw)
  $processInfo=Get-CimInstance Win32_Process -Filter "ProcessId = $serverPid" -ErrorAction SilentlyContinue
  $expectedScript=Join-Path $PSScriptRoot 'serve.mjs'
  if($processInfo -and $processInfo.Name -eq 'node.exe' -and $processInfo.CommandLine.Contains($expectedScript)){Stop-Process -Id $serverPid;Write-Output 'Gesture Synth stopped.'}else{Write-Output 'The recorded Gesture Synth process is not running.'}
}
