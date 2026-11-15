$ErrorActionPreference = 'Stop'

$ruleNames = @(
    'AIArchive-WebRTC-UDP-Chrome',
    'AIArchive-WebRTC-UDP-Edge',
    'AIArchive-WebRTC-UDP-Doubao',
    'AIArchive-WebRTC-UDP-WeFlow',
    'AIArchive-WebRTC-UDP-ChatGPT',
    'AIArchive-WebRTC-UDP-Claude',
    'AIArchive-WebRTC-UDP-Codex'
)

foreach ($ruleName in $ruleNames) {
    Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue |
        Remove-NetFirewallRule
}

$chromePolicyPath = 'HKLM:\SOFTWARE\Policies\Google\Chrome'
if (Test-Path $chromePolicyPath) {
    Remove-ItemProperty -Path $chromePolicyPath -Name 'WebRtcIPHandling' -ErrorAction SilentlyContinue
}

$edgePolicyPath = 'HKLM:\SOFTWARE\Policies\Microsoft\Edge'
if (Test-Path $edgePolicyPath) {
    Remove-ItemProperty -Path $edgePolicyPath -Name 'WebRtcLocalhostIpHandling' -ErrorAction SilentlyContinue
}

Write-Output 'WebRTC leak-protection policies and firewall rules removed.'
