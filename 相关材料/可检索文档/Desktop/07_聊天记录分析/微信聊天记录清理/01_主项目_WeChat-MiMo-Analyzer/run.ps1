param(
    [ValidateSet('ingest', 'pilot', 'analyze', 'report', 'verify', 'search', 'search-labels')]
    [string]$Action = 'report',
    [string]$Query = '',
    [string]$Contact = '',
    [int]$LimitBatches = 10,
    [int]$SearchLimit = 20
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = (Get-Command python -ErrorAction Stop).Source
$Source = 'C:\Users\wardc\Desktop\微信完整导出_2026-07-24\01_WeFlow可读导出'
$Database = Join-Path $ProjectRoot 'data\wechat-private-v2.sqlite3'

switch ($Action) {
    'ingest' {
        & $Python (Join-Path $ProjectRoot 'src\weflow_ingest.py') --source $Source --database $Database
    }
    'pilot' {
        & $Python (Join-Path $ProjectRoot 'src\analyze_with_claude.py') --database $Database --limit-batches 1 --batch-size 3
        if ($LASTEXITCODE -eq 0) {
            & $Python (Join-Path $ProjectRoot 'src\build_report.py') --database $Database
        }
    }
    'analyze' {
        & $Python (Join-Path $ProjectRoot 'src\analyze_with_claude.py') --database $Database --limit-batches $LimitBatches --minimum-messages 5 --minimum-chars 500 --require-two-way
        if ($LASTEXITCODE -eq 0) {
            & $Python (Join-Path $ProjectRoot 'src\build_report.py') --database $Database
        }
    }
    'report' {
        & $Python (Join-Path $ProjectRoot 'src\build_report.py') --database $Database
    }
    'verify' {
        & $Python (Join-Path $ProjectRoot 'src\verify.py') --database $Database
    }
    'search' {
        if ([string]::IsNullOrWhiteSpace($Query)) { throw 'search 需要 -Query 参数' }
        & $Python (Join-Path $ProjectRoot 'src\search.py') $Query --database $Database --contact $Contact --limit $SearchLimit
    }
    'search-labels' {
        if ([string]::IsNullOrWhiteSpace($Query)) { throw 'search-labels 需要 -Query 参数' }
        & $Python (Join-Path $ProjectRoot 'src\search.py') $Query --scope annotations --database $Database --contact $Contact --limit $SearchLimit
    }
}

exit $LASTEXITCODE
