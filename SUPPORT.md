# Support Guide — Project Emberbird

**Platform**: Emberbird (lifecycle platform for Android on Windows)  
**Official Portal**: [https://wsabuilds-website.pages.dev](https://wsabuilds-website.pages.dev)  
**Documentation**: [docs/](docs/) · [Troubleshooting Guide](TROUBLESHOOTING.md)

---

## 1. Where to Get Help

We provide multiple structured support channels depending on your inquiry:

| Need | Recommended Channel | Details |
|---|---|---|
| **Installation & Setup Help** | [GitHub Discussions](https://github.com/IamAzmathullaShaikh/Emberbird/discussions) | Search existing Q&A threads before creating a new topic. |
| **Reproducible Bug Reports** | [GitHub Issues (Bug Report)](https://github.com/IamAzmathullaShaikh/Emberbird/issues/new?template=bug_report.yml) | Include Windows build (`winver`), WSA edition, and error logs. |
| **Android App Compatibility** | [Compatibility Hub](https://wsabuilds-website.pages.dev/compatibility) / [Report Form](https://github.com/IamAzmathullaShaikh/Emberbird/issues/new?template=compatibility_report.yml) | Submit test results for banking, gaming, or productivity apps. |
| **Step-by-Step Diagnostics** | [Interactive Troubleshooting Wizard](https://wsabuilds-website.pages.dev/troubleshoot/wizard) | Interactive decision tree with copyable PowerShell commands. |
| **Feature Ideas & Feedback** | [GitHub Issues (Feature Request)](https://github.com/IamAzmathullaShaikh/Emberbird/issues/new?template=feature_request.yml) | Propose improvements aligned with platform mission. |

---

## 2. Fast Diagnostic Commands

Most common installation errors relate to Windows virtualization or Developer Mode. Run these elevated commands in **PowerShell (Administrator)** to diagnose and resolve:

```powershell
# 1. Verify and enable Virtual Machine Platform and Hypervisor Platform
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:HypervisorPlatform /all /norestart

# 2. Enable Windows Developer Mode via registry
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" /t REG_DWORD /f /v "AllowDevelopmentWithoutDevLicense" /d "1"

# 3. Check AppX Deployment Service status
Get-Service -Name AppXSvc

# 4. Connect ADB to WSA container (Port 58526)
adb connect 127.0.0.1:58526
adb devices
```

---

## 3. Common Error Code Reference

- **`0x80370102` (Virtual Machine Platform Not Enabled)**: Hardware virtualization (Intel VT-x or AMD-V) is disabled in your BIOS/UEFI, or the Windows Virtual Machine Platform feature is not enabled.
- **`0x80070005` (Access Denied / Developer Mode Disabled)**: Enable Developer Mode in `Settings > System > For developers`.
- **`0x80073CF9` (AppX Installation Failed)**: Ensure the target folder is on an NTFS drive, has sufficient space, and that the `AppXSvc` service is running.

For comprehensive troubleshooting guides and legacy issue walkthroughs, consult [TROUBLESHOOTING.md](TROUBLESHOOTING.md) and [docs/archive/](docs/archive/).

---

## 4. Scope of Support

### What We Support:
- Installation and lifecycle management of official Emberbird releases (Standard & Banking editions).
- In-place upgrades without user data loss (`userdata.vhdx`).
- Official desktop manager (`Emberbird.Manager`).
- Integration of Google Play Store (OpenGApps Pico) and Magisk Stable on supported Windows 10/11 versions.

### What We Do NOT Support:
- Third-party modified APKs, warez, or pirated software.
- Outdated root solutions (SuperSU, KingRoot).
- Custom kernel builds or KernelSU implementations.
- Modified Windows OS installations (e.g. stripped Windows "lite" ISOs with removed AppX / Hyper-V components).
