# 启动 Phase 2/3 进化流水线 + 深度联系人报告
# 用法: .\启动-Phase2-Phase3.ps1
# 或: .\启动-Phase2-Phase3.ps1 -Phase 3  (跳过 Phase 2，直接跑 Phase 3)
# 或: .\启动-Phase2-Phase3.ps1 -Phase deep  (跳过 Phase 2/3，直接跑深度分析)

param(
    [ValidateSet("2","3","deep","all")]
    [string]$Phase = "all"
)

$ErrorActionPreference = "Continue"
$ws = "C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区"
Set-Location $ws

# 端点配置
$env:ANTHROPIC_AUTH_TOKEN = "[REDACTED_CREDENTIAL]"
$env:HTTP_PROXY = "http://127.0.0.1:1100"
$env:HTTPS_PROXY = "http://127.0.0.1:1100"

# 确保日志目录存在
New-Item -ItemType Directory -Force -Path "$ws\logs" | Out-Null

$ts = Get-Date -Format 'yyyyMMdd_HHmmss'

if ($Phase -eq "all" -or $Phase -eq "2") {
    Write-Host "========== Phase 2: 模式提取 ==========" -ForegroundColor Cyan
    $logfile = "$ws\logs\phase2_$ts.log"
    python -u -m src.v3_evolution_pipeline --phase 2 --rpm 10 --workers 2 --max-contacts 100 2>&1 | Tee-Object -FilePath $logfile
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Phase 2 异常退出 (exit=$LASTEXITCODE)，检查日志: $logfile" -ForegroundColor Red
        exit 1
    }
    Write-Host "Phase 2 完成!" -ForegroundColor Green
}

if ($Phase -eq "all" -or $Phase -eq "3") {
    Write-Host "========== Phase 3: 自我进化 ==========" -ForegroundColor Cyan
    $logfile = "$ws\logs\phase3_$ts.log"
    python -u -m src.v3_evolution_pipeline --phase 3 --rpm 10 --workers 2 2>&1 | Tee-Object -FilePath $logfile
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Phase 3 异常退出 (exit=$LASTEXITCODE)，检查日志: $logfile" -ForegroundColor Red
        exit 1
    }
    Write-Host "Phase 3 完成!" -ForegroundColor Green
}

if ($Phase -eq "all" -or $Phase -eq "deep") {
    Write-Host "========== 深度联系人报告 ==========" -ForegroundColor Cyan
    $logfile = "$ws\logs\deep_contact_$ts.log"
    python -u -m src.v3_deep_contact_analyzer --min-msgs 10 --rpm 10 --workers 2 2>&1 | Tee-Object -FilePath $logfile
    if ($LASTEXITCODE -ne 0) {
        Write-Host "深度联系人报告异常退出 (exit=$LASTEXITCODE)，检查日志: $logfile" -ForegroundColor Red
        exit 1
    }
    Write-Host "深度联系人报告完成!" -ForegroundColor Green
}

Write-Host "全部完成!" -ForegroundColor Green