# NVIDIA 免费 DeepSeek v4 pro · 7 小时微信深度分析一键启动脚本
#
# 用途：在 NVIDIA 免费层（≤40 RPM）上跑全量聊天片段标注 + 2 个 pending 事件深度分析。
# 凭证：NVIDIA API key（nvapi-...）只从环境变量或参数读取，绝不写入磁盘/日志。
#
# 用法：
#   .\启动-NVIDIA-7小时分析.ps1 -ApiKey "nvapi-你的key"          # 传参（本进程内存）
#   $env:NVIDIA_API_KEY="nvapi-你的key"; .\启动-NVIDIA-7小时分析.ps1
#
# 关键参数：
#   -Hours  运行总时长（默认 7 小时）
#   -Rpm    全局限速（默认 40）
#   -Db     数据库路径（默认 scale 副本，只写 _v3 表）
#
param(
    [string]$ApiKey = $env:NVIDIA_API_KEY,
    [int]$Hours = 7,
    [float]$Rpm = 40,
    [string]$Db = "data/scale/wechat-analysis-scale.sqlite3",
    [string]$Model = "deepseek-ai/deepseek-v4-pro"
)

$ErrorActionPreference = 'Stop'
$workDir = 'C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区'
Set-Location -LiteralPath $workDir

# ── 凭证检查 ──────────────────────────────────────────────────────────────
if (-not $ApiKey) {
    Write-Host '❌ 未提供 NVIDIA API key。' -ForegroundColor Red
    Write-Host '   方式一：.\启动-NVIDIA-7小时分析.ps1 -ApiKey "nvapi-..."' -ForegroundColor Yellow
    Write-Host '   方式二：$env:NVIDIA_API_KEY="nvapi-..."; .\启动-NVIDIA-7小时分析.ps1' -ForegroundColor Yellow
    Write-Host '   （免费 key 在 https://build.nvidia.com 注册获取）' -ForegroundColor DarkGray
    exit 1
}
if (-not $ApiKey.StartsWith('nvapi-')) {
    Write-Host '⚠ 提示：key 不是 nvapi- 开头，请确认是 NVIDIA 的 key。' -ForegroundColor Yellow
}

# ── 环境变量（仅本进程，不写盘）────────────────────────────────────────────
$env:ANTHROPIC_BASE_URL = 'https://integrate.api.nvidia.com/v1'
$env:ANTHROPIC_AUTH_TOKEN = $ApiKey

$logDir = Join-Path $workDir 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$logFile = Join-Path $logDir "nvidia_7h_$stamp.log"

Write-Host ''
Write-Host '=== NVIDIA 免费 DeepSeek v4 pro · 微信深度分析 ===' -ForegroundColor Cyan
Write-Host "模型：$Model"
Write-Host "全局限速：$Rpm RPM（NVIDIA 免费层上限）"
Write-Host "预算时长：$Hours 小时"
Write-Host "数据库：$Db（只写 _v3 表，历史表只读）"
Write-Host "日志：$logFile"
Write-Host "API key：已从参数/环境变量读取（不打印、不落盘）" -ForegroundColor Green
Write-Host ''

# ── 阶段 0：无 API 冒烟 + 基线验证 ─────────────────────────────────────────
Write-Host '[阶段0] 无 API 基线验证（测试 + 抽样预演）...' -ForegroundColor Cyan
& python -m unittest discover -s tests 2>&1 | Tee-Object -FilePath $logFile -Append | Select-Object -Last 2
if ($LASTEXITCODE -ne 0) {
    Write-Host '❌ 测试未通过，中止。请检查日志。' -ForegroundColor Red
    exit 1
}

# 生成全量计划（0 API，确认规模）
$planOut = & python -m src.deepseek_v3_executor plan --config config/v3_config.nvidia.json 2>&1
$planOut | Tee-Object -FilePath $logFile -Append | Select-Object -First 3
Write-Host '[阶段0] 完成。' -ForegroundColor Green
Write-Host ''

# ── 阶段 A：全量未标注片段标注（40 RPM 限速，主体约 2-3 小时）──────────────
Write-Host '[阶段A] 全量片段标注（40 RPM 限速，去重跳过已标注）...' -ForegroundColor Cyan
Write-Host "  启动时间：$(Get-Date -Format 'HH:mm:ss')，预计 2-3 小时，上限 $Hours 小时" -ForegroundColor Yellow

# 用一个临时 config 覆盖 rpm/hours（保持原 config 不变）
$runCfg = Join-Path $logDir "nvidia_run_$stamp.json"
(Get-Content -Raw config/v3_config.nvidia.json) -replace '"rpm_limit": 40', ('"rpm_limit": ' + $Rpm) | Set-Content -Encoding UTF8 $runCfg

& python -m src.deepseek_v3_executor run --config $runCfg 2>&1 | Tee-Object -FilePath $logFile -Append
if ($LASTEXITCODE -ne 0) {
    Write-Host '⚠ 阶段A 退出码非 0，请检查日志（可能部分完成，去重可续跑）。' -ForegroundColor Yellow
}
Write-Host '[阶段A] 完成。' -ForegroundColor Green
Write-Host ''

# ── 阶段 B：pending 事件深度分析（仅当事件包含证据时才跑）───────────────────
# 说明：已知 evs_31ee09e464ed1148（和舒哥聚会）、evs_36fb1961def13dc1（打折机票托运）
# 是拆分产生的空壳 pending —— 无证据、无联系人、无源候选，深度分析会因缺包失败。
# 这里先尝试构建包，失败则安全跳过并记入日志（0 副作用，不影响阶段 A 的标注成果）。
Write-Host '[阶段B] pending 事件深度分析（仅处理有证据的事件包）...' -ForegroundColor Cyan
$pendingEvents = 'evs_31ee09e464ed1148,evs_36fb1961def13dc1'
$pkgDir = Join-Path $workDir 'runs/deep_pending'
$buildOut = & python -m src.v3_event_pkg build --events $pendingEvents --db data/wechat-analysis-v3.sqlite3 --outdir $pkgDir 2>&1
$buildOut | Tee-Object -FilePath $logFile -Append
if ($LASTEXITCODE -eq 0) {
    & python -m src.v3_deep_analyzer analyze $pkgDir --db data/wechat-analysis-v3.sqlite3 --model $Model --api-style openai --rpm-limit $Rpm 2>&1 | Tee-Object -FilePath $logFile -Append
} else {
    Write-Host '[阶段B] 事件包构建失败（预期：pending 事件缺证据），安全跳过。' -ForegroundColor Yellow
    Write-Host '  说明：这两个 evs_* 事件是拆分空壳（无证据/联系人/源候选），需先回填候选再深度分析。' -ForegroundColor DarkGray
}
Write-Host '[阶段B] 完成。' -ForegroundColor Green
Write-Host ''

# ── 阶段 C：报告 ──────────────────────────────────────────────────────────
Write-Host '[阶段C] 生成报告...' -ForegroundColor Cyan
& python -m src.deepseek_v3_executor report (Get-ChildItem runs -Directory | Where-Object Name -like 'pilot_v3_*' | Sort-Object LastWriteTime -Descending | Select-Object -First 1).Name --config $runCfg 2>&1 | Tee-Object -FilePath $logFile -Append
Write-Host '[阶段C] 完成。' -ForegroundColor Green

Write-Host ''
Write-Host '=== 全部完成 ===' -ForegroundColor Cyan
Write-Host "日志：$logFile"
Write-Host 'API key 仅存在于本进程内存，脚本结束后不再持有。' -ForegroundColor Green
