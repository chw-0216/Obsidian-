<#
  节点导入 Clash Verge 自动化脚本
  ================================
  用途: 把 "IP:端口:用户名:密码" 格式的代理凭证一键导入 Clash Verge Rev 并自动选出能用的连法。

  用法1(推荐): 在 PowerShell 里运行并带上凭证(可多个,空格分隔):
      powershell -ExecutionPolicy Bypass -File "节点导入ClashVerge.ps1" "1.2.3.4:443:user:pass"
  用法2: 直接运行,按提示粘贴凭证。
  也支持无认证的 "IP:端口" 两段格式。

  它会做什么:
    1. 解析凭证,为每个节点生成 4 种候选连法: SOCKS5直连 / HTTP直连 / SOCKS5经v2rayN前置 / HTTP经v2rayN前置
       (前置=先走本机 v2rayN SOCKS 127.0.0.1:1099 出国再连节点,应对"封中国大陆IP"的服务商)
    2. 用 Clash Verge 自带的 mihomo 内核起一个临时实例,逐个实测延迟,找出真正能通的连法
    3. 把配置写入 Clash Verge (固定档案 lclaude0001,重复运行会覆盖更新,不会越积越多)
    4. 重启 Clash Verge,能通的节点自动排第一位(即默认选中)
    5. 通过 Clash 混合端口 7897 做端到端验证,打印出口 IP
  注意: 写入后若要全局上网,仍需在 Clash Verge 主页开启"系统代理"开关(脚本不动系统设置)。
#>
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Creds)

$AppDir   = Join-Path $env:APPDATA "io.github.clash-verge-rev.clash-verge-rev"
$Mihomo   = "C:\Program Files\Clash Verge\verge-mihomo.exe"
$AppExe   = "C:\Program Files\Clash Verge\clash-verge.exe"
$Uid      = "lclaude0001"
$CtrlPort = 19091
$TestPort = 17890
$Secret   = "claude-import-test"
$TestUrl  = "http://www.gstatic.com/generate_204"
$FrontName = "前置-v2rayN"

function Test-Port($ip, $port, $ms = 1500) {
    try {
        $c = New-Object Net.Sockets.TcpClient
        $r = $c.BeginConnect($ip, [int]$port, $null, $null)
        $ok = $r.AsyncWaitHandle.WaitOne($ms)
        if ($ok) { $c.EndConnect($r) }
        $c.Close()
        return $ok
    } catch { return $false }
}

# ---------- 1. 输入与解析 ----------
if (-not $Creds -or $Creds.Count -eq 0) {
    $raw = Read-Host "粘贴节点凭证 (IP:端口:用户名:密码, 多个用空格分隔)"
    $Creds = $raw -split '[\s,;]+' | Where-Object { $_ }
}

$nodes = @()
$idx = 0
foreach ($c in $Creds) {
    $p = $c.Trim() -split ':'
    if ($p.Count -ne 4 -and $p.Count -ne 2) { Write-Warning "跳过无法解析的输入: $c"; continue }
    if ($p[1] -notmatch '^\d+$') { Write-Warning "端口不是数字,跳过: $c"; continue }
    $idx++
    $user = $null; $pass = $null
    if ($p.Count -eq 4) { $user = $p[2]; $pass = $p[3] }
    $nodes += [pscustomobject]@{ Ip = $p[0]; Port = $p[1]; User = $user; Pass = $pass; Tag = "$($p[0])" }
}
if ($nodes.Count -eq 0) { Write-Host "没有可用的凭证输入,退出。" -ForegroundColor Red; exit 1 }
Write-Host "解析到 $($nodes.Count) 个节点。" -ForegroundColor Cyan

# ---------- 2. 生成候选连法 ----------
$hasFront = Test-Port "127.0.0.1" 1099
if ($hasFront) { Write-Host "检测到 v2rayN SOCKS(1099) 在运行,将包含'经前置'候选。" -ForegroundColor Cyan }
else { Write-Host "v2rayN SOCKS(1099) 未运行,只测直连候选。若节点封中国IP,请先开 v2rayN 再重跑。" -ForegroundColor Yellow }

function NodeYaml($name, $type, $n, $front) {
    $y  = "  - name: `"$name`"`n    type: $type`n    server: $($n.Ip)`n    port: $($n.Port)`n"
    if ($n.User) { $y += "    username: $($n.User)`n    password: $($n.Pass)`n" }
    if ($type -eq "socks5") { $y += "    udp: true`n" }
    if ($front) { $y += "    dialer-proxy: `"$FrontName`"`n" }
    return $y
}

$cands = @()   # name, yaml, front
foreach ($n in $nodes) {
    $cands += [pscustomobject]@{ Name = "$($n.Tag)-SOCKS5直连"; Yaml = (NodeYaml "$($n.Tag)-SOCKS5直连" "socks5" $n $false); Front = $false }
    $cands += [pscustomobject]@{ Name = "$($n.Tag)-HTTP直连";   Yaml = (NodeYaml "$($n.Tag)-HTTP直连"   "http"   $n $false); Front = $false }
    if ($hasFront) {
        $cands += [pscustomobject]@{ Name = "$($n.Tag)-SOCKS5经前置"; Yaml = (NodeYaml "$($n.Tag)-SOCKS5经前置" "socks5" $n $true); Front = $true }
        $cands += [pscustomobject]@{ Name = "$($n.Tag)-HTTP经前置";   Yaml = (NodeYaml "$($n.Tag)-HTTP经前置"   "http"   $n $true); Front = $true }
    }
}

$frontYaml = "  - name: `"$FrontName`"`n    type: socks5`n    server: 127.0.0.1`n    port: 1099`n    udp: true`n"

# ---------- 3. 临时 mihomo 实测 ----------
if (-not (Test-Path $Mihomo)) { Write-Host "找不到 $Mihomo ,请确认 Clash Verge 已安装。" -ForegroundColor Red; exit 1 }
$tmpDir = Join-Path $env:TEMP "clash-import-test"
New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null
$testCfg = Join-Path $tmpDir "test.yaml"

$sb = "mixed-port: $TestPort`nmode: rule`nlog-level: warning`nexternal-controller: 127.0.0.1:$CtrlPort`nsecret: $Secret`nproxies:`n"
if ($hasFront) { $sb += $frontYaml }
foreach ($c in $cands) { $sb += $c.Yaml }
$sb += "proxy-groups:`n  - name: TESTGROUP`n    type: select`n    proxies:`n"
foreach ($c in $cands) { $sb += "      - `"$($c.Name)`"`n" }
$sb += "rules:`n  - MATCH,TESTGROUP`n"
[IO.File]::WriteAllText($testCfg, $sb, [Text.UTF8Encoding]::new($false))

Write-Host "启动临时 mihomo 内核开始实测 $($cands.Count) 个候选连法..." -ForegroundColor Cyan
$proc = Start-Process -FilePath $Mihomo -ArgumentList "-f", "`"$testCfg`"", "-d", "`"$tmpDir`"" -WindowStyle Hidden -PassThru

$hdr = @{ Authorization = "Bearer $Secret" }
$up = $false
$deadline = (Get-Date).AddSeconds(12)
while ((Get-Date) -lt $deadline) {
    try { Invoke-RestMethod -Uri "http://127.0.0.1:$CtrlPort/version" -Headers $hdr -TimeoutSec 2 | Out-Null; $up = $true; break }
    catch { Start-Sleep -Milliseconds 500 }
}
if (-not $up) { Write-Host "临时内核启动失败。" -ForegroundColor Red; try { Stop-Process -Id $proc.Id -Force -Confirm:$false } catch {}; exit 1 }

$encUrl = [uri]::EscapeDataString($TestUrl)
foreach ($c in $cands) {
    $enc = [uri]::EscapeDataString($c.Name)
    $delay = -1
    try {
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:$CtrlPort/proxies/$enc/delay?timeout=6000&url=$encUrl" -Headers $hdr -TimeoutSec 12
        $delay = [int]$r.delay
    } catch {}
    $c | Add-Member -NotePropertyName Delay -NotePropertyValue $delay
    if ($delay -gt 0) { Write-Host ("  [通] {0}  {1}ms" -f $c.Name, $delay) -ForegroundColor Green }
    else { Write-Host ("  [不通] {0}" -f $c.Name) -ForegroundColor DarkGray }
}
try { Stop-Process -Id $proc.Id -Force -Confirm:$false } catch {}

$winners = @($cands | Where-Object { $_.Delay -gt 0 } | Sort-Object Delay)
$losers  = @($cands | Where-Object { $_.Delay -le 0 })

# ---------- 4. 写入 Clash Verge ----------
$ordered = @($winners) + @($losers)
$py  = "# 由 节点导入ClashVerge.ps1 于 $(Get-Date -Format 'yyyy-MM-dd HH:mm') 生成`n"
$py += "# 实测结果: $($winners.Count)/$($cands.Count) 个连法可用,可用者已排在选择组最前(默认选中)`n"
$py += "proxies:`n"
if ($hasFront) { $py += $frontYaml }
foreach ($c in $cands) { $py += $c.Yaml }
$py += "proxy-groups:`n  - name: `"选择节点`"`n    type: select`n    proxies:`n"
foreach ($c in $ordered) { $py += "      - `"$($c.Name)`"`n" }
$py += "      - DIRECT`n"
$py += "rules:`n  - GEOIP,CN,DIRECT`n  - MATCH,选择节点`n"

Write-Host "写入 Clash Verge 配置..." -ForegroundColor Cyan
try { Stop-Process -Name "clash-verge" -Force -Confirm:$false -ErrorAction Stop } catch {}
try { Stop-Process -Name "verge-mihomo" -Force -Confirm:$false -ErrorAction Stop } catch {}
Start-Sleep -Seconds 2

New-Item -ItemType Directory -Force -Path (Join-Path $AppDir "profiles") | Out-Null
[IO.File]::WriteAllText((Join-Path $AppDir "profiles\$Uid.yaml"), $py, [Text.UTF8Encoding]::new($false))

$ts = [DateTimeOffset]::Now.ToUnixTimeSeconds()
$item = "- uid: $Uid`n  type: local`n  name: Claude导入-单节点`n  file: $Uid.yaml`n  desc: 节点导入ClashVerge.ps1 自动生成`n  updated: $ts"
$profIdx = Join-Path $AppDir "profiles.yaml"
if (Test-Path $profIdx) {
    $txt = [IO.File]::ReadAllText($profIdx, [Text.Encoding]::UTF8)
    if ($txt -notmatch [regex]::Escape("uid: $Uid")) {
        if ($txt -match '(?m)^items:\s*(null)?\s*$') {
            $txt = $txt -replace '(?m)^items:\s*(null)?\s*$', "items:`n$item"
        } else {
            $txt = $txt -replace '(?m)^items:', "items:`n$item"
        }
    }
    if ($txt -match '(?m)^current:') { $txt = $txt -replace '(?m)^current:.*$', "current: $Uid" }
    else { $txt = "current: $Uid`n" + $txt }
    [IO.File]::WriteAllText($profIdx, $txt, [Text.UTF8Encoding]::new($false))
} else {
    [IO.File]::WriteAllText($profIdx, "# Profiles Config for Clash Verge`n`ncurrent: $Uid`nitems:`n$item`n", [Text.UTF8Encoding]::new($false))
}

# ---------- 5. 重启并端到端验证 ----------
Write-Host "重启 Clash Verge..." -ForegroundColor Cyan
Start-Process -FilePath $AppExe
Start-Sleep -Seconds 8

if ($winners.Count -gt 0) {
    $exitIp = $null
    try {
        $resp = Invoke-WebRequest -Uri "https://api.ipify.org" -Proxy "http://127.0.0.1:7897" -UseBasicParsing -TimeoutSec 25
        $exitIp = $resp.Content.Trim()
    } catch {}
    Write-Host ""
    if ($exitIp) {
        Write-Host "=== 全部完成 ===" -ForegroundColor Green
        Write-Host ("已选用: {0} ({1}ms), 经 Clash 出口 IP: {2}" -f $winners[0].Name, $winners[0].Delay, $exitIp) -ForegroundColor Green
        Write-Host "如需全局上网,请在 Clash Verge 主页打开「系统代理」开关。" -ForegroundColor Yellow
        if ($winners[0].Front) { Write-Host "注意: 当前连法依赖 v2rayN 前置,v2rayN 必须保持运行。" -ForegroundColor Yellow }
    } else {
        Write-Host "配置已写入且实测时可通,但重启后经 7897 端口验证失败,请打开 Clash Verge 查看「代理」页。" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "=== 四种连法全部不通,配置仍已写入 Clash Verge 供手动排查 ===" -ForegroundColor Red
    Write-Host "常见原因: 1) 凭证过期/未生效  2) 服务商封中国大陆IP且未开v2rayN前置" -ForegroundColor Yellow
    Write-Host "          3) 需要在卖家面板绑定/白名单你的IP  4) 协议特殊(如SNI中继),不是标准代理" -ForegroundColor Yellow
}
