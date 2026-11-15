# 微信聊天标注分析 - 一键启动 (PowerShell)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SrcDir = Join-Path $ProjectRoot "src"
$DataDir = Join-Path $ProjectRoot "data"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  微信聊天标注分析 - 一键启动" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[✓] Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[✗] 未找到 Python" -ForegroundColor Red
    exit 1
}

# 检查旧数据库
$OldDb = "C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeChat-MiMo-Analyzer\data\wechat-private-v2.sqlite3"
if (Test-Path $OldDb) {
    Write-Host "[✓] 旧系统数据库存在" -ForegroundColor Green
} else {
    Write-Host "[✗] 旧系统数据库不存在: $OldDb" -ForegroundColor Red
    exit 1
}

# 确保数据目录存在
if (-not (Test-Path $DataDir)) {
    New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
}

Write-Host ""

# 显示菜单
function Show-Menu {
    Write-Host "请选择操作:" -ForegroundColor Yellow
    Write-Host "  1. 运行 R1 标注 (可观察事实) - 推荐" -ForegroundColor White
    Write-Host "  2. 运行 R0 数据盘点" -ForegroundColor White
    Write-Host "  3. 查看当前进度" -ForegroundColor White
    Write-Host "  4. 继续 R1 (断点续跑)" -ForegroundColor White
    Write-Host "  5. 退出" -ForegroundColor White
    Write-Host ""
}

function Show-Progress {
    $dbPath = Join-Path $DataDir "wechat-personal.sqlite3"
    if (-not (Test-Path $dbPath)) {
        Write-Host "数据库不存在，尚未开始分析" -ForegroundColor Yellow
        return
    }

    $result = python -c @"
import sqlite3
import os

db_path = r'$dbPath'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute('SELECT count(*) FROM observations')
obs = cur.fetchone()[0]

cur.execute('SELECT count(*) FROM observations WHERE user_confirmed=""confirmed""')
confirmed = cur.fetchone()[0]

cur.execute('SELECT count(*) FROM relationships')
rels = cur.fetchone()[0]

cur.execute('SELECT count(*) FROM self_patterns')
patterns = cur.fetchone()[0]

cur.execute('SELECT count(*) FROM coaching_experiments')
coaching = cur.fetchone()[0]

cur.execute('SELECT count(*) FROM persona_rules')
persona = cur.fetchone()[0]

conn.close()

total_segments = 6303
pct = obs / total_segments * 100

print(f'R1 可观察事实: {obs}/{total_segments} ({pct:.1f}%)')
print(f'  已确认: {confirmed}')
print(f'R2 关系模型: {rels}')
print(f'R3 自我模式: {patterns}')
print(f'R4 沟通教练: {coaching}')
print(f'R5 数字分身: {persona}')
"@

    Write-Host ""
    Write-Host "=== 分析进度 ===" -ForegroundColor Cyan
    Write-Host $result
    Write-Host ""
}

# 主循环
while ($true) {
    Show-Menu
    $choice = Read-Host "请输入选项 (1-5)"

    switch ($choice) {
        "1" {
            Write-Host ""
            Write-Host "[R1] 开始标注可观察事实..." -ForegroundColor Green
            Write-Host "[信息] 使用默认参数: batch-size=4, max-batches=10, budget=0.25" -ForegroundColor Gray
            Write-Host "[信息] 按 Ctrl+C 可随时中断，进度会自动保存" -ForegroundColor Gray
            Write-Host ""

            python (Join-Path $SrcDir "run_r1_standard.py") --batch-size 4 --max-batches 10 --budget 0.25

            Write-Host ""
            Write-Host "[R1] 本轮完成！" -ForegroundColor Green
            Write-Host ""
        }
        "2" {
            Write-Host ""
            Write-Host "[R0] 运行数据盘点..." -ForegroundColor Green
            python (Join-Path $SrcDir "inventory.py") --database (Join-Path $DataDir "wechat-personal.sqlite3")
            Write-Host ""
        }
        "3" {
            Show-Progress
        }
        "4" {
            Write-Host ""
            Write-Host "[R1] 继续标注 (断点续跑)..." -ForegroundColor Green
            Write-Host "[信息] 自动跳过已标注的片段" -ForegroundColor Gray
            Write-Host ""

            python (Join-Path $SrcDir "run_r1_standard.py") --batch-size 4 --max-batches 10 --budget 0.25

            Write-Host ""
            Write-Host "[R1] 本轮完成！" -ForegroundColor Green
            Write-Host ""
        }
        "5" {
            Write-Host ""
            Write-Host "再见！" -ForegroundColor Cyan
            exit 0
        }
        default {
            Write-Host "[错误] 无效选项，请重新选择" -ForegroundColor Red
            Write-Host ""
        }
    }
}
