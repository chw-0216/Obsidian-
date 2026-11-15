# WS5281 HiLink SCRAM 登录 + 设备列表
$ErrorActionPreference = 'Stop'
$base = 'http://192.168.3.1'
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

function Get-Csrf {
    $h = Invoke-WebRequest -Uri "$base/html/index.html" -UseBasicParsing -NoProxy -TimeoutSec 10 -WebSession $session
    $p = ([regex]::Match($h.Content, 'name="csrf_param" content="([^"]+)"')).Groups[1].Value
    $t = ([regex]::Match($h.Content, 'name="csrf_token" content="([^"]+)"')).Groups[1].Value
    return @{ csrf_param = $p; csrf_token = $t }
}

function Post-Json($path, $csrf, $dataObj, $timeoutSec = 15) {
    $bodyObj = @{ csrf = $csrf; data = $dataObj }
    $json = $bodyObj | ConvertTo-Json -Compress -Depth 8
    $r = Invoke-WebRequest -Uri "$base$path" -Method Post -Body $json `
        -ContentType 'application/json; charset=utf-8' `
        -Headers @{ '_ResponseFormat' = 'JSON'; 'X-Requested-With' = 'XMLHttpRequest' } `
        -UseBasicParsing -NoProxy -SkipHttpErrorCheck -TimeoutSec $timeoutSec -WebSession $session
    $resp = $r.Content | ConvertFrom-Json
    $newCsrf = $csrf
    if ($resp.csrf_param -and $resp.csrf_token) { $newCsrf = @{ csrf_param = $resp.csrf_param; csrf_token = $resp.csrf_token } }
    return @{ resp = $resp; csrf = $newCsrf; status = $r.StatusCode }
}

function HexToBytes($hex) { $b = New-Object byte[] ($hex.Length / 2); for ($i = 0; $i -lt $b.Length; $i++) { $b[$i] = [Convert]::ToByte($hex.Substring($i * 2, 2), 16) }; return $b }
function BytesToHex($bytes) { -join ($bytes | ForEach-Object { $_.ToString('x2') }) }

function Scram-Login($password) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $enc = [System.Text.Encoding]::UTF8

    function Hmac-Sha256($key, $data) {
        $h = [System.Security.Cryptography.HMACSHA256]::new($key)
        $r = $h.ComputeHash($data)
        $h.Dispose()
        return $r
    }

    $csrf = Get-Csrf
    $nonceBytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($nonceBytes)
    $firstNonce = BytesToHex $nonceBytes

    $r1 = Post-Json '/api/system/user_login_nonce' $csrf @{ username = 'admin'; firstnonce = $firstNonce }
    $resp1 = $r1.resp
    if ($resp1.errcode) { return @{ ok = $false; msg = "nonce errcode=$($resp1.errcode)" } }
    if (-not $resp1.salt -or -not $resp1.servernonce) { return @{ ok = $false; msg = "nonce 响应缺少字段: $($r1.status)" } }

    $salt = HexToBytes ($resp1.salt)
    $iter = [int]$resp1.iterations
    $serverNonce = [string]$resp1.servernonce
    $authMsg = "$firstNonce,$serverNonce,$serverNonce"

    $pbkdf2 = [System.Security.Cryptography.Rfc2898DeriveBytes]::new($password, $salt, $iter, [System.Security.Cryptography.HashAlgorithmName]::SHA256)
    $saltPwd = $pbkdf2.GetBytes(32)

    $clientKey = Hmac-Sha256 ($enc.GetBytes('Client Key')) $saltPwd
    $serverKey = Hmac-Sha256 ($enc.GetBytes('Server Key')) $saltPwd
    $storedKey = $sha.ComputeHash($clientKey)
    $clientSig = Hmac-Sha256 $storedKey ($enc.GetBytes($authMsg))
    $serverSig = Hmac-Sha256 $serverKey ($enc.GetBytes($authMsg))

    $clientProof = New-Object byte[] 32
    for ($i = 0; $i -lt 32; $i++) { $clientProof[$i] = $clientKey[$i] -bxor $clientSig[$i] }

    $r2 = Post-Json '/api/system/user_login_proof' $r1.csrf @{ clientproof = (BytesToHex $clientProof); finalnonce = $serverNonce }
    $resp2 = $r2.resp

    if ($resp2.serversignature -and $resp2.serversignature -eq (BytesToHex $serverSig) -and $resp2.rsan) {
        return @{ ok = $true; csrf = $r2.csrf; level = $resp2.level }
    } else {
        return @{ ok = $false; msg = "proof 失败: errcode=$($resp2.errcode) category=$($resp2.errorCategory)" }
    }
}

$candidates = @('UE4997tY')
$result = $null
foreach ($pwd in $candidates) {
    "尝试密码: $pwd ..."
    $res = Scram-Login $pwd
    if ($res.ok) { "✓ 登录成功! level=$($res.level)"; $result = $res; break }
    else { "  ✗ $($res.msg)" }
    Start-Sleep -Milliseconds 800
}

if ($result) {
    "=== 拉取设备列表 HostInfo ==="
    $csrf = $result.csrf
    $getUrl = "$base/api/system/HostInfo"
    try {
        $g = Invoke-WebRequest -Uri $getUrl -UseBasicParsing -NoProxy -TimeoutSec 15 -WebSession $session -SkipHttpErrorCheck
        "HostInfo → $($g.StatusCode)"
        $g.Content.Substring(0, [Math]::Min(6000, $g.Content.Length))
    } catch { "拉取失败: $($_.Exception.Message)" }
} else {
    "所有候选密码均失败。请提供路由器管理密码或 WiFi 密码再试。"
}
