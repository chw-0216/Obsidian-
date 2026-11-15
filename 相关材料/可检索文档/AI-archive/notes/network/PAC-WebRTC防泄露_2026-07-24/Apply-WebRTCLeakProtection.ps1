$ErrorActionPreference = 'Stop'

$policyValue = 'disable_non_proxied_udp'
$firewallGroup = 'AI-archive WebRTC Leak Protection'

# Chrome: use only proxied UDP for WebRTC, otherwise fall back to proxied TCP.
$chromePolicyPath = 'HKLM:\SOFTWARE\Policies\Google\Chrome'
New-Item -Path $chromePolicyPath -Force | Out-Null
New-ItemProperty -Path $chromePolicyPath -Name 'WebRtcIPHandling' -PropertyType String -Value $policyValue -Force | Out-Null

# Edge: equivalent policy supported by Edge 77 and later.
$edgePolicyPath = 'HKLM:\SOFTWARE\Policies\Microsoft\Edge'
New-Item -Path $edgePolicyPath -Force | Out-Null
New-ItemProperty -Path $edgePolicyPath -Name 'WebRtcLocalhostIpHandling' -PropertyType String -Value $policyValue -Force | Out-Null

function Ensure-ProgramUdpBlock {
    param(
        [Parameter(Mandatory)] [string] $Name,
        [Parameter(Mandatory)] [string] $DisplayName,
        [Parameter(Mandatory)] [string] $Program
    )

    if (-not (Test-Path -LiteralPath $Program)) {
        Write-Warning "Skipped missing executable: $Program"
        return
    }

    $existing = Get-NetFirewallRule -Name $Name -ErrorAction SilentlyContinue
    if ($existing) {
        Set-NetFirewallRule -Name $Name -Enabled True -Direction Outbound -Action Block -Profile Any | Out-Null
        Set-NetFirewallApplicationFilter -AssociatedNetFirewallRule $existing -Program $Program | Out-Null
        Set-NetFirewallPortFilter -AssociatedNetFirewallRule $existing -Protocol UDP | Out-Null
    } else {
        New-NetFirewallRule `
            -Name $Name `
            -DisplayName $DisplayName `
            -Group $firewallGroup `
            -Description 'Blocks direct outbound UDP for this Chromium-based app so PAC-proxied HTTP/HTTPS/WebSocket traffic cannot be bypassed by WebRTC/STUN. TCP remains allowed.' `
            -Direction Outbound `
            -Action Block `
            -Enabled True `
            -Profile Any `
            -Protocol UDP `
            -Program $Program | Out-Null
    }
}

if (-not ('AppContainerSidDeriver' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Security.Principal;

public static class AppContainerSidDeriver
{
    [DllImport("userenv.dll", CharSet = CharSet.Unicode)]
    private static extern int DeriveAppContainerSidFromAppContainerName(
        string appContainerName,
        out IntPtr appContainerSid
    );

    [DllImport("advapi32.dll")]
    private static extern IntPtr FreeSid(IntPtr sid);

    public static string GetSid(string packageFamilyName)
    {
        IntPtr sid;
        int result = DeriveAppContainerSidFromAppContainerName(packageFamilyName, out sid);
        if (result != 0)
        {
            Marshal.ThrowExceptionForHR(result);
        }

        try
        {
            return new SecurityIdentifier(sid).Value;
        }
        finally
        {
            FreeSid(sid);
        }
    }
}
'@
}

function Ensure-PackageUdpBlock {
    param(
        [Parameter(Mandatory)] [string] $Name,
        [Parameter(Mandatory)] [string] $DisplayName,
        [Parameter(Mandatory)] [string] $PackageFamilyName
    )

    if (-not (Get-AppxPackage -Name ($PackageFamilyName -split '_')[0] -ErrorAction SilentlyContinue)) {
        Write-Warning "Package not visible to elevated process; deriving rule from family name: $PackageFamilyName"
    }

    $packageSid = [AppContainerSidDeriver]::GetSid($PackageFamilyName)
    $existing = Get-NetFirewallRule -Name $Name -ErrorAction SilentlyContinue
    if ($existing) {
        Set-NetFirewallRule -Name $Name -Enabled True -Direction Outbound -Action Block -Profile Any | Out-Null
        Set-NetFirewallApplicationFilter -AssociatedNetFirewallRule $existing -Package $packageSid | Out-Null
        Set-NetFirewallPortFilter -AssociatedNetFirewallRule $existing -Protocol UDP | Out-Null
    } else {
        New-NetFirewallRule `
            -Name $Name `
            -DisplayName $DisplayName `
            -Group $firewallGroup `
            -Description 'Blocks direct outbound UDP for this packaged Chromium app so PAC-proxied HTTP/HTTPS/WebSocket traffic cannot be bypassed by WebRTC/STUN. TCP remains allowed.' `
            -Direction Outbound `
            -Action Block `
            -Enabled True `
            -Profile Any `
            -Protocol UDP `
            -Package $packageSid | Out-Null
    }
}

$programRules = @(
    @{
        Name = 'AIArchive-WebRTC-UDP-Chrome'
        DisplayName = 'AI-archive WebRTC 防泄露 - Google Chrome'
        Program = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
    },
    @{
        Name = 'AIArchive-WebRTC-UDP-Edge'
        DisplayName = 'AI-archive WebRTC 防泄露 - Microsoft Edge'
        Program = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    },
    @{
        Name = 'AIArchive-WebRTC-UDP-Doubao'
        DisplayName = 'AI-archive WebRTC 防泄露 - 豆包'
        Program = 'C:\Users\wardc\AppData\Local\Doubao\Application\app\Doubao.exe'
    },
    @{
        Name = 'AIArchive-WebRTC-UDP-WeFlow'
        DisplayName = 'AI-archive WebRTC 防泄露 - WeFlow'
        Program = 'C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeFlow\app\WeFlow.exe'
    }
)

foreach ($rule in $programRules) {
    Ensure-ProgramUdpBlock @rule
}

$packageRules = @(
    @{
        Name = 'AIArchive-WebRTC-UDP-ChatGPT'
        DisplayName = 'AI-archive WebRTC 防泄露 - ChatGPT'
        PackageFamilyName = 'OpenAI.ChatGPT-Desktop_2p2nqsd0c76g0'
    },
    @{
        Name = 'AIArchive-WebRTC-UDP-Claude'
        DisplayName = 'AI-archive WebRTC 防泄露 - Claude'
        PackageFamilyName = 'Claude_pzs8sxrjxfjjc'
    },
    @{
        Name = 'AIArchive-WebRTC-UDP-Codex'
        DisplayName = 'AI-archive WebRTC 防泄露 - Codex'
        PackageFamilyName = 'OpenAI.Codex_2p2nqsd0c76g0'
    }
)

foreach ($rule in $packageRules) {
    Ensure-PackageUdpBlock @rule
}

Write-Output 'WebRTC leak-protection policies and firewall rules applied.'
