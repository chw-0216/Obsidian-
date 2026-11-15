# ZTE ZXHN F7615MV30 登录脚本
$ErrorActionPreference = 'Stop'
$base = 'http://192.168.1.1'
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$sha = [System.Security.Cryptography.SHA256]::Create()

function Get-Token {
    $r = Invoke-WebRequest -Uri "$base/" -UseBasicParsing -NoProxy -TimeoutSec 10 -WebSession $session
    $m = [regex]::Match($r.Content, 'Frm_Loginchecktoken"\)\.value = "([^"]+)"')
    if ($m.Success) { return $m.Groups[1].Value } else { return 'V2EiEtXqPIOXxkOBmuI5vzlK' }
}

function Try-Login($user, $pass) {
    $token = Get-Token
    $rand = Get-Random -Minimum 10000000 -Maximum 99999999
    $randStr = [string]$rand
    $hash = -join ($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($pass + $randStr)) | ForEach-Object { $_.ToString('x2') })
    $body = @{
        Username          = $user
        Password          = $hash
        UserRandomNum     = $randStr
        Frm_Logintoken    = '0'
        Frm_Loginchecktoken = $token
        action            = 'login'
        Right             = ''
    }
    try {
        $r = Invoke-WebRequest -Uri "$base/" -Method Post -Body $body `
            -ContentType 'application/x-www-form-urlencoded' `
            -Headers @{ 'X-Requested-With' = 'XMLHttpRequest' } `
            -UseBasicParsing -NoProxy -SkipHttpErrorCheck -TimeoutSec 20 -WebSession $session -MaximumRedirection 0
        return @{ status = $r.StatusCode; url = $r.BaseResponse.RequestMessage.RequestUri.ToString(); len = $r.Content.Length; head = $r.Content.Substring(0, [Math]::Min(200, $r.Content.Length)) }
    } catch {
        $resp = $_.Exception.Response
        if ($resp) {
            $loc = $resp.Headers['Location']
            return @{ status = [int]$resp.StatusCode; url = "REDIRECT: $loc"; len = 0; head = '' }
        }
        return @{ status = 0; url = $_.Exception.Message; len = 0; head = '' }
    }
}

$cands = @(
    @('CMCCAdmin', 'aDm8H%MdA'),
    @('CMCCAdmin', 'Cmcc10086#'),
    @('admin', 'admin'),
    @('user', 'user')
)
$success = $false
foreach ($c in $cands) {
    "尝试: $($c[0]) / $($c[1]) ..."
    $res = Try-Login $c[0] $c[1]
    "  状态=$($res.status) URL=$($res.url) len=$($res.len)"
    if ($res.head -match '(?i)错误|error|errmsg|登录失败') { "  头部: $($res.head)" }
    if ($res.status -eq 302 -and $res.url -notmatch '192\.168\.1\.1/?$') { "  ✓ 疑似登录成功 (重定向)"; $success = $true; break }
    if ($res.status -eq 200 -and $res.len -gt 2000 -and $res.head -notmatch '(?i)错误|errmsg') { "  ✓ 疑似登录成功 (页面返回)"; $success = $true; break }
    Start-Sleep -Milliseconds 1200
}
if (-not $success) { "未成功登录（注意3次错误锁定）。" }
