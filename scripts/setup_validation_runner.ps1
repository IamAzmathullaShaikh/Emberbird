# =============================================================================
# setup_validation_runner.ps1 — Windows Validation Lab Host Provisioner
# =============================================================================
# Requires Run as Administrator.
# =============================================================================

# Test Administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "Please run this script from an elevated PowerShell prompt (Run as Administrator)."
    exit 1
}

Write-Host "=== Provisioning WSABuilds Windows Validation Lab Host ===" -ForegroundColor Cyan

# 1. Enable Windows Developer Mode (Loose-folder AppX registration)
Write-Host "[1/5] Enabling Developer Mode..." -ForegroundColor Yellow
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" /t REG_DWORD /f /v "AllowDevelopmentWithoutDevLicense" /d "1" | Out-Null
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" /t REG_DWORD /f /v "AllowAllTrustedApps" /d "1" | Out-Null

# 2. Enable Virtual Machine Platform
Write-Host "[2/5] Enabling Virtual Machine Platform..." -ForegroundColor Yellow
Enable-WindowsOptionalFeature -Online -NoRestart -FeatureName 'VirtualMachinePlatform' | Out-Null

# 3. Configure Firewall rules for ADB WSA Port (58526)
Write-Host "[3/5] Configuring ADB Firewall Rules..." -ForegroundColor Yellow
New-NetFirewallRule -DisplayName "WSA-ADB-Loopback" -Direction Inbound -LocalPort 58526 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue | Out-Null

# 4. Verify Essential Tools on PATH
Write-Host "[4/5] Checking Tooling..." -ForegroundColor Yellow
$tools = @("python.exe", "git.exe")
foreach ($t in $tools) {
    if (Get-Command $t -ErrorAction SilentlyContinue) {
        Write-Host "    [PASS] Found: $t" -ForegroundColor Green
    } else {
        Write-Warning "    [WARN] Tool not in PATH: $t"
    }
}

# 5. Finished
Write-Host "[5/5] Host Provisioning Completed Successfully!" -ForegroundColor Green
Write-Host "Note: A system reboot may be required if VirtualMachinePlatform was newly enabled." -ForegroundColor Cyan
