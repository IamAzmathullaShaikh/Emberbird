# Emberbird Subsystem Maintenance — VHDx compaction for faster cold starts.
#
# What this does (real, supported operations only):
#   1. Verifies the subsystem is fully stopped (vmmemWSA gone) — compaction of a
#      mounted VHDx is impossible and would corrupt it.
#   2. Runs `Optimize-VHD` when the Hyper-V module is available, otherwise falls
#      back to `diskpart compact vdisk` (both shrink dynamic VHDx files that
#      grew during app use; smaller files attach faster and reclaim disk).
#
# What this deliberately does NOT do:
#   - It does not tune VM RAM. Windows manages vmmemWSA allocation dynamically
#     and honors no user-facing configuration knob; claims otherwise are false.
#   - It performs no "auxiliary storage rebuilds" — VHDx metadata is maintained
#     by the platform; there is no supported user-space reinit.
#   First-launch latency gains come from compaction here plus the installer's
#   post-register warm-up (see upstream/installer/Install.ps1).
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File optimize-subsystem.ps1
#
# Exit codes: 0 = success, 1 = failure, 2 = subsystem still running.

$ErrorActionPreference = 'Continue'

# --- 1. Safety gate: the subsystem must be fully stopped ---------------------
foreach ($p in @('vmmemWSA', 'WsaClient', 'WsaService')) {
    if (Get-Process -Name $p -ErrorAction SilentlyContinue) {
        Write-Error "Subsystem is running (process: $p). Run 'WsaClient /shutdown' and retry."
        exit 2
    }
}

$WsaPath = (Get-AppxPackage -Name 'MicrosoftCorporationII.WindowsSubsystemForAndroid' -ErrorAction SilentlyContinue).InstallLocation
if (-not $WsaPath -or -not (Test-Path $WsaPath)) {
    Write-Error "Emberbird Subsystem is not installed (no Appx package found)."
    exit 1
}
Write-Output "Subsystem location: $WsaPath"

$VhdxNames = @('userdata.vhdx', 'system.vhdx', 'system_ext.vhdx', 'vendor.vhdx', 'product.vhdx', 'metadata.vhdx')
$VhdxFiles = $VhdxNames | ForEach-Object { Join-Path $WsaPath $_ } | Where-Object { Test-Path $_ }
if (-not $VhdxFiles) {
    Write-Error "No VHDx files found under $WsaPath — nothing to optimize."
    exit 1
}

# --- 2. Compact dynamic VHDx files -------------------------------------------
$HasOptimizeVhd = $null -ne (Get-Command Optimize-VHD -ErrorAction SilentlyContinue)
if (-not $HasOptimizeVhd) {
    Write-Output "Optimize-VHD unavailable (Hyper-V module not installed); using diskpart fallback."
}

$DiskPartScript = Join-Path $env:TEMP 'emberbird-compact.txt'
$Failed = 0
foreach ($vhdx in $VhdxFiles) {
    $before = (Get-Item $vhdx).Length
    Write-Output ("Compacting {0} ({1:N1} MB)..." -f (Split-Path $vhdx -Leaf), ($before / 1MB))
    if ($HasOptimizeVhd) {
        Optimize-VHD -Path $vhdx -Mode Full -ErrorAction Continue | Out-Null
        if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
            Write-Warning "Optimize-VHD failed for $(Split-Path $vhdx -Leaf)"
            $Failed++
        }
    }
    else {
        @"
select vdisk file="$vhdx"
attach vdisk readonly
compact vdisk
detach vdisk
"@ | Set-Content -Path $DiskPartScript -Encoding Ascii
        diskpart /s $DiskPartScript | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "diskpart reported exit code $LASTEXITCODE for $(Split-Path $vhdx -Leaf)"
            $Failed++
        }
    }
    $after = (Get-Item $vhdx).Length
    Write-Output ("  {0:N1} MB -> {1:N1} MB" -f ($before / 1MB), ($after / 1MB))
}
Remove-Item $DiskPartScript -ErrorAction SilentlyContinue

if ($Failed -gt 0) {
    Write-Warning "Optimization finished with $Failed failure(s)."
    exit 1
}
Write-Output "Optimization complete. Next subsystem start will boot from compacted disks."
exit 0
