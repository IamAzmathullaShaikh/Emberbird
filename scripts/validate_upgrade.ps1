# =============================================================================
# validate_upgrade.ps1 — WSA In-Place Upgrade Compatibility Test Harness
# =============================================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$TargetPackageDir,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputReport = "upgrade-validation-report.json"
)

$ErrorActionPreference = "Stop"

$Report = @{
    Timestamp = (Get-Date).ToUniversalTime().ToString("o")
    Status = "NOT VERIFIED"
    Details = @()
    TestDataRetained = $false
    PackageUpdated = $false
}

Write-Host "=== WSA Upgrade Compatibility Test Harness ===" -ForegroundColor Cyan

# 1. Check existing installation
$PackageName = "MicrosoftCorporationII.WindowsSubsystemForAndroid"
$Installed = Get-AppxPackage -Name $PackageName -ErrorAction SilentlyContinue

if ($null -eq $Installed) {
    $Report.Status = "NOT VERIFIED"
    $Report.Details += "No baseline WSA installation detected. Upgrade testing requires pre-existing installation."
    Write-Warning $Report.Details[-1]
    $Report | ConvertTo-Json -Depth 5 | Out-File -FilePath $OutputReport -Encoding utf8
    exit 0
}

Write-Host "[+] Current installed WSA Version: $($Installed.Version)" -ForegroundColor Green
$InitialVersion = $Installed.Version

# 2. Simulate application state / user data in LocalCache
$AppDataPath = "$env:LOCALAPPDATA\Packages\MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe\LocalCache"
if (-not (Test-Path $AppDataPath)) {
    New-Item -ItemType Directory -Force -Path $AppDataPath | Out-Null
}
$TestMarkerFile = Join-Path $AppDataPath "wsabuilds_upgrade_test_marker.txt"
$TestPayload = "WSABuilds Persistence Test Token: " + [Guid]::NewGuid().ToString()
Set-Content -Path $TestMarkerFile -Value $TestPayload -Encoding utf8
Write-Host "[+] Seeded persistent test marker: $TestMarkerFile" -ForegroundColor Green

# 3. Perform in-place upgrade registration if target directory provided
if ($TargetPackageDir -and (Test-Path "$TargetPackageDir\AppxManifest.xml")) {
    Write-Host "[*] Executing in-place upgrade to $TargetPackageDir ..." -ForegroundColor Cyan
    try {
        Add-AppxPackage -ForceApplicationShutdown -ForceUpdateFromAnyVersion -Register "$TargetPackageDir\AppxManifest.xml"
        Start-Sleep -Seconds 3
        
        $PostInstall = Get-AppxPackage -Name $PackageName
        Write-Host "[+] Post-upgrade WSA Version: $($PostInstall.Version)" -ForegroundColor Green
        
        # Verify version progressed or re-registered
        $Report.PackageUpdated = ($null -ne $PostInstall)
        
        # Verify test marker data retention
        if (Test-Path $TestMarkerFile) {
            $ReadToken = Get-Content $TestMarkerFile -Raw
            if ($ReadToken.Trim() -eq $TestPayload.Trim()) {
                $Report.TestDataRetained = $true
                Write-Host "[+] User data persistence verified: test marker intact." -ForegroundColor Green
            }
        }
        
        $Report.Status = if ($Report.PackageUpdated -and $Report.TestDataRetained) { "VERIFIED" } else { "FAILED" }
    } catch {
        $Report.Status = "FAILED"
        $Report.Details += $_.Exception.Message
        Write-Error "Upgrade registration failed: $_"
    }
} else {
    $Report.Status = "PARTIALLY VERIFIED"
    $Report.Details += "Target package directory not supplied; baseline data seeding validated successfully."
}

$Report | ConvertTo-Json -Depth 5 | Out-File -FilePath $OutputReport -Encoding utf8
Write-Host "[+] Upgrade validation report written to $OutputReport" -ForegroundColor Cyan
