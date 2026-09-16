---
title: "WSA Upgrade Compatibility & Data Retention Framework"
description: "This document specifies the validation procedure for ensuring seamless, data-preserving upgrades between successive WSABuilds releases."
category: "getting-started"
order: 1
---

This document specifies the validation procedure for ensuring seamless, data-preserving upgrades between successive WSABuilds releases.

---

## 1. Upgrade Architecture & Guarantees

In Windows Subsystem for Android, all user data, installed Android apps, settings, and root modules reside inside:
- `%LocalAppData%\Packages\MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe\LocalCache\`
- `%LocalAppData%\Packages\MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe\LocalState\userdata.vhdx`

Because WSABuilds preserves the verified package identity:
- **Package Name**: `MicrosoftCorporationII.WindowsSubsystemForAndroid`
- **Publisher**: `CN=Microsoft Corporation, O=Microsoft Corporation, L=Redmond, S=Washington, C=US`
- **Package Family Name**: `MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe`

Windows considers successive versions of WSABuilds to be **the exact same application family**.

---

## 2. In-Place Update Mechanics

Upgrades are executed through `Install.ps1` or `WSAUpdater.py` via PowerShell:

```powershell
Add-AppxPackage -ForceApplicationShutdown -ForceUpdateFromAnyVersion -Register .\AppxManifest.xml
```

### Fallback Protection:
If in-place re-registration encounters a lock or schema conflict, `Install.ps1` invokes:
```powershell
Remove-AppxPackage -PreserveApplicationData -Package $Installed.PackageFullName
Add-AppxPackage -ForceApplicationShutdown -ForceUpdateFromAnyVersion -Register .\AppxManifest.xml
```
The `-PreserveApplicationData` switch guarantees that `userdata.vhdx` and `%LocalAppData%` app state remain untouched on disk.

---

## 3. Automated Test Procedure

To validate upgrade compatibility on a Windows test runner:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts/validate_upgrade.ps1 -TargetPackageDir "output/WSA_<new_version>_x64"
```

The script:
1. Records the version of the currently installed WSA build.
2. Writes a unique cryptographic token into `%LocalAppData%\...\LocalCache\wsabuilds_upgrade_test_marker.txt`.
3. Registers the new `AppxManifest.xml`.
4. Asserts that the new version is registered in Windows AppX Package Manager.
5. Asserts that the token file in `LocalCache` is bit-for-bit preserved.
6. Emits `upgrade-validation-report.json`.
