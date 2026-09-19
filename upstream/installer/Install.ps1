# This file is part of MagiskOnWSALocal.
#
# MagiskOnWSALocal is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# MagiskOnWSALocal is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with MagiskOnWSALocal.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright (C) 2024 LSPosed Contributors
#

$Host.UI.RawUI.WindowTitle = "Installing Emberbird Subsystem for Android...."
function Test-Administrator {
    [OutputType([bool])]
    param()
    process {
        [Security.Principal.WindowsPrincipal]$user = [Security.Principal.WindowsIdentity]::GetCurrent();
        return $user.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator);
    }
}

function Get-InstalledDependencyVersion {
    param (
        [string]$Name,
        [string]$ProcessorArchitecture
    )
    PROCESS {
        If ($null -Ne $ProcessorArchitecture) {
            return Get-AppxPackage -Name $Name | ForEach-Object { if ($_.Architecture -Eq $ProcessorArchitecture) { $_ } } | Sort-Object -Property Version | Select-Object -ExpandProperty Version -Last 1;
        }
    }
}

Function Check-Windows11 {
    RETURN (Get-ComputerInfo | Select-Object -expand OsName) -match 11
}

Function Test-CommandExist {
    Param ($Command)
    $OldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'
    try { if (Get-Command $Command) { RETURN $true } }
    Catch { RETURN $false }
    Finally { $ErrorActionPreference = $OldPreference }
} #end function Test-CommandExist

# Track 0.3: Zombie-lock-free shutdown.
# A bare `Stop-Process WsaClient` leaves the Hyper-V worker (vmmemWSA) running
# with open handles on userdata.vhdx, which makes the next install/update fail
# with file-in-use errors. We shut down gracefully, then WAIT for the VM
# process to disappear before falling back to a forced kill.
Function Stop-EmberbirdSubsystem {
    If (Test-CommandExist WsaClient) {
        Start-Process WsaClient -Wait -Args "/shutdown" -ErrorAction SilentlyContinue
    }
    $deadline = (Get-Date).AddSeconds(20)
    While ((Get-Date) -Lt $deadline) {
        If (-Not (Get-Process -Name "vmmemWSA" -ErrorAction SilentlyContinue)) { Break }
        Start-Sleep -Milliseconds 500
    }
    If (Get-Process -Name "vmmemWSA" -ErrorAction SilentlyContinue) {
        Write-Warning "Subsystem VM did not exit gracefully; forcing shutdown"
        Stop-Process -Name "vmmemWSA" -Force -ErrorAction SilentlyContinue
    }
    Stop-Process -Name "WsaClient" -ErrorAction SilentlyContinue
    Stop-Process -Name "WsaService" -ErrorAction SilentlyContinue
    Stop-Process -Name "WsaSettings" -ErrorAction SilentlyContinue
    Stop-Process -Name "WSACrashUploader" -ErrorAction SilentlyContinue
}

# Track 0.2: Developer Settings bypass (VM warm-up).
# Instead of asking the user to click "Manage developer settings", we boot the
# subsystem once during installation: the deep link starts the VM, we poll for
# the vmmemWSA worker with a bounded deadline (no blind sleeps), then shut the
# subsystem down cleanly so userdata.vhdx is unlocked before first launch.
# The first user-facing launch therefore boots warm instead of cold.
Function Start-EmberbirdWarmUp {
    Write-Output "Initializing Subsystem components (one-time warm-up)...."
    Start-Process "wsa://settings"
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $deadline = (Get-Date).AddSeconds(90)
    $booted = $false
    While ((Get-Date) -Lt $deadline) {
        If (Get-Process -Name "vmmemWSA" -ErrorAction SilentlyContinue) {
            Start-Sleep -Seconds 8   # let Android finish the critical boot phase
            $booted = $true
            Break
        }
        Start-Sleep -Seconds 2
    }
    If ($booted) {
        Write-Output ("Subsystem warm-up completed in {0:N0} seconds" -f $sw.Elapsed.TotalSeconds)
    }
    Else {
        Write-Warning "Subsystem VM did not signal boot within 90 seconds. First launch may be slow. If Android never boots, check Virtual Machine Platform is enabled and reboot."
    }
    Stop-EmberbirdSubsystem
}

# Track 0.1: Single primary entry point.
# Exactly ONE user-facing launch happens when installation completes. The
# warm-up's internal wsa://settings boot is shut down before this runs, so the
# user sees a single Play Store window, never a duplicate/magisk pair.
Function Finish {
    Clear-Host
    Start-EmberbirdWarmUp
    Write-Output "Installation complete. Launching Emberbird Subsystem..."
    Start-Process "wsa://com.android.vending"
}

If ((Check-Windows11) -And (Test-CommandExist 'pwsh.exe')) {
    $pwsh = "pwsh.exe"
} Else {
    $pwsh = "powershell.exe"
}

If (-Not (Test-Administrator)) {
    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Bypass -Force
    $Proc = Start-Process -PassThru -Verb RunAs $pwsh -Args "-ExecutionPolicy Bypass -Command Set-Location '$PSScriptRoot'; &'$PSCommandPath' EVAL"
    If ($null -Ne $Proc) {
        $Proc.WaitForExit()
    }
    If ($null -Eq $Proc -Or $Proc.ExitCode -Ne 0) {
        Write-Warning "Failed to launch start as Administrator`r`nPress any key to exit"
        $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown');
    }
    exit
}
ElseIf (($args.Count -Eq 1) -And ($args[0] -Eq "EVAL")) {
    Start-Process $pwsh -NoNewWindow -Args "-ExecutionPolicy Bypass -Command Set-Location '$PSScriptRoot'; &'$PSCommandPath'"
    exit
}

$FileList = Get-Content -Path .\filelist.txt
If (((Test-Path -Path $FileList) -Eq $false).Count) {
    Write-Error "Some files are missing in the folder. Please try to build again. Press any key to exit"
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    exit 1
}

If (((Test-Path -Path "MakePri.ps1") -And (Test-Path -Path "makepri.exe")) -Eq $true) {
    $ProcMakePri = Start-Process $pwsh -PassThru -NoNewWindow -Args "-ExecutionPolicy Bypass -File MakePri.ps1" -WorkingDirectory $PSScriptRoot
    $null = $ProcMakePri.Handle
    $ProcMakePri.WaitForExit()
    If ($ProcMakePri.ExitCode -Ne 0) {
        Write-Warning "Failed to merge resources, WSA Settings will always be in English`r`nPress any key to continue"
        $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    }
    $Host.UI.RawUI.WindowTitle = "Installing Emberbird Subsystem for Android...."
}

reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" /t REG_DWORD /f /v "AllowDevelopmentWithoutDevLicense" /d "1"

# When using PowerShell which is installed with MSIX
# Get-WindowsOptionalFeature and Enable-WindowsOptionalFeature will fail
# See https://github.com/PowerShell/PowerShell/issues/13866
if ($PSHOME.contains("8wekyb3d8bbwe")) {
    Import-Module DISM -UseWindowsPowerShell
}

If ($(Get-WindowsOptionalFeature -Online -FeatureName 'VirtualMachinePlatform').State -Ne "Enabled") {
    Enable-WindowsOptionalFeature -Online -NoRestart -FeatureName 'VirtualMachinePlatform'
    Write-Warning "Need restart to enable virtual machine platform`r`nPress y to restart or press any key to exit"
    $Key = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    If ("y" -Eq $Key.Character) {
        Restart-Computer -Confirm
    }
    Else {
        exit 1
    }
}

[xml]$Xml = Get-Content ".\AppxManifest.xml";
$Name = $Xml.Package.Identity.Name;
Write-Output "Installing $Name version: $($Xml.Package.Identity.Version)"
$ProcessorArchitecture = $Xml.Package.Identity.ProcessorArchitecture;
$Dependencies = $Xml.Package.Dependencies.PackageDependency;
$Dependencies | ForEach-Object {
    $InstalledVersion = Get-InstalledDependencyVersion -Name $_.Name -ProcessorArchitecture $ProcessorArchitecture;
    If ( $InstalledVersion -Lt $_.MinVersion ) {
        If ($env:WT_SESSION) {
            $env:WT_SESSION = $null
            Write-Output "Dependency should be installed but Windows Terminal is in use. Restarting to conhost.exe"
            Start-Process conhost.exe -Args "powershell.exe -ExecutionPolicy Bypass -Command Set-Location '$PSScriptRoot'; &'$PSCommandPath'"
            exit 1
        }
        Write-Output "Dependency package $($_.Name) $ProcessorArchitecture required minimum version: $($_.MinVersion). Installing...."
        Add-AppxPackage -ForceApplicationShutdown -ForceUpdateFromAnyVersion -Path "$($_.Name)_$ProcessorArchitecture.appx"
    }
    Else {
        Write-Output "Dependency package $($_.Name) $ProcessorArchitecture current version: $InstalledVersion. Nothing to do."
    }
}

$Installed = $null
$Installed = Get-AppxPackage -Name $Name

If (($null -Ne $Installed) -And (-Not ($Installed.IsDevelopmentMode))) {
    Write-Warning "There is already one installed WSA. Please uninstall it first.`r`nPress y to uninstall existing WSA or press any key to exit"
    $key = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    If ("y" -Eq $key.Character) {
        Clear-Host
        Remove-AppxPackage -Package $Installed.PackageFullName
    }
    Else {
        exit 1
    }
}

# Track 0.3 (replace path): a development-mode package makes same-version
# `-Register` a silent no-op (the install location never moves). Remove it with
# preserved user data first so the new package actually installs.
If (($null -Ne $Installed) -And ($Installed.IsDevelopmentMode)) {
    Write-Output "Replacing development-mode installation (user data preserved)...."
    Remove-AppxPackage -PreserveApplicationData -Package $Installed.PackageFullName
    $Installed = $null
    Start-Sleep -Seconds 3
}

# Track 0.3 (lock path): full subsystem shutdown incl. the vmmemWSA worker so
# no stale handle survives on userdata.vhdx during registration.
Stop-EmberbirdSubsystem

Write-Output "Installing Emberbird Subsystem for Android...."
Add-AppxPackage -ForceApplicationShutdown -ForceUpdateFromAnyVersion -Register .\AppxManifest.xml
If ($?) {
    Finish
}
ElseIf ($null -Ne $Installed) {
    Write-Error "Failed to update.`r`nPress any key to uninstall existing installation while preserving user data.`r`nTake in mind that this will remove the Android apps' icon from the start menu.`r`nIf you want to cancel, close this window now."
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    Clear-Host
    Remove-AppxPackage -PreserveApplicationData -Package $Installed.PackageFullName
    Add-AppxPackage -ForceApplicationShutdown -ForceUpdateFromAnyVersion -Register .\AppxManifest.xml
    If ($?) {
        Finish
    }
}
Write-Output "All Done!`r`nPress any key to exit"
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
