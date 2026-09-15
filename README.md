# WSABuilds — Windows Subsystem for Android™ Automation Platform

<p align="center">
  <img src="https://img.shields.io/badge/WSA-2407.40000.4.0-blue.svg?style=for-the-badge&logo=android" alt="WSA Version"/>
  <img src="https://img.shields.io/badge/Android-13.0%20(API%2033)-green.svg?style=for-the-badge&logo=android" alt="Android 13"/>
  <img src="https://img.shields.io/badge/GApps-OpenGApps%20Pico-orange.svg?style=for-the-badge&logo=googleplay" alt="OpenGApps Pico"/>
  <img src="https://img.shields.io/badge/Root-Magisk%20Stable%20%7C%20Vanilla%20(No%20Root)-blue.svg?style=for-the-badge" alt="Magisk Stable | Vanilla"/>
  <img src="https://img.shields.io/badge/Architecture-x64%20(ARM64%20on%20roadmap)-purple.svg?style=for-the-badge" alt="x64 architecture"/>
  <img src="https://img.shields.io/github/actions/workflow/status/IamAzmathullaShaikh/WSABuilds/build.yml?label=CI%20Build&style=for-the-badge" alt="CI Status"/>
  <img src="https://img.shields.io/github/actions/workflow/status/IamAzmathullaShaikh/WSABuilds/release.yml?label=WSA%20Release&style=for-the-badge" alt="WSA Release Pipeline"/>
  <img src="https://img.shields.io/github/actions/workflow/status/IamAzmathullaShaikh/WSABuilds/winget-release.yml?label=Manager%20Release&style=for-the-badge" alt="Manager Release Pipeline"/>
</p>

<p align="center">
  <a href="https://wsabuilds-website.pages.dev"><strong>🌐 Official Website & Downloads Portal</strong></a> — interactive documentation, compatibility hub, and diagnostic wizard
</p>

---

## 1. Project Overview

**WSABuilds** is an automated engineering and packaging platform for the **Windows Subsystem for Android (WSA)** on Windows 11 and Windows 10. The platform automates update discovery directly from Microsoft's Windows Update Delivery Network (FE3), integrates minimal **Google Play Store and Services (OpenGApps Pico)**, provides automated ARM translation layers (libhoudini) for x86_64 PCs, spoofs device properties to Google Pixel 5 (`redfin`) for Google Play Protect certification, and packages production-ready release archives in two officially supported **Tier 1 Editions**:

1. **Standard Edition (Rooted)**: Features official Magisk Stable (v30.6+) and OpenGApps Pico for developers, modders, and power users.
2. **Banking & Enterprise Edition (Unrooted)**: Features a clean, unrooted ramdisk with OpenGApps Pico for users requiring 100% compatibility with banking, UPI, streaming DRM, and enterprise applications.

### Key Guarantees:
* **Preserved Subsystem Identity**: Retains official Microsoft AppX package identity (`MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe`), ensuring clean in-place upgrades without user application data loss.
* **Unified Windows Support**: The exact same package installs on both **Windows 11 (Build 22000+)** and **Windows 10 22H2 (Build 19045.2311+)**. There are no separate OS downloads.
* **Reproducible Multi-Environment Builds**: Supports automated building via Linux/WSL2 (`build.sh`) and native pure-Python on Windows (`build_local.py`).
* **Strict Quality Gates**: Every build is checked against automated package integrity, identity drift detection, offline validation, and credential security scans.

---

## 2. Supported Editions

WSABuilds provides two purpose-built Tier 1 configurations to serve different application requirements:

| Edition Specification | Standard Edition (Rooted) | Banking & Enterprise Edition (Vanilla) |
|---|---|---|
| **Target Audience** | Developers, modders, power users, penetration testers | Everyday users, banking, UPI, enterprise MDM, streaming |
| **Root Solution** | **Magisk Stable (v30.6+)** integrated into ramdisk | **Vanilla (Zero Root)**: Completely unrooted clean ramdisk |
| **Root Privileges** | Automated UID 0 ADB root shell and Magisk manager | No `su` binary, no root daemon, no `/sbin` modifications |
| **Google Services** | OpenGApps Pico (Play Store + Play Services) | OpenGApps Pico (Play Store + Play Services) |
| **Device Spoofing** | Pixel 5 (`redfin`) Play Protect fingerprint | Pixel 5 (`redfin`) Play Protect fingerprint |
| **Banking / UPI Apps** | Workarounds required (DenyList, Shamiko modules) | **Native out-of-the-box compatibility** (Zero root detection) |
| **In-Place Upgrades** | Supported (Lossless user data retention) | Supported (Lossless user data retention) |

### Which Edition Should I Download?
* **Choose Standard Edition if**: You need root access, want to run Magisk modules (LSposed, Zygisk), use cheat engines, customize Android system files, or require an elevated ADB root shell (`su`).
* **Choose Banking & Enterprise Edition if**: You use financial apps (e.g. YONO SBI, PhonePe, Google Pay, Paytm), government identification apps, OTT streaming apps with strict Widevine DRM, or corporate work profiles that reject modified or rooted devices.

---

## 3. Downloads & Verification

### Official Release Packages (Tier 1 Production)

| Architecture & Edition | Package Contents | Verified Download Target | Build Channel |
|---|---|---|---|
| **x64 Standard Edition** | • Magisk Stable (v30.6+)<br/>• OpenGApps Pico (Play Store + Services)<br/>• Automated Root & Pixel 5 Spoofing | [Download Standard Edition (x64)](https://github.com/IamAzmathullaShaikh/WSABuilds/releases/download/wsa-v2311.40000.5.0/WSA_2407.40000.4.0_x64.7z) | **Tier 1 (Production)** |
| **x64 Banking Edition** | • Vanilla (Clean Ramdisk, Zero Root)<br/>• OpenGApps Pico (Play Store + Services)<br/>• Pixel 5 Spoofing (Banking App Safe) | [Download Banking Edition (x64)](https://github.com/IamAzmathullaShaikh/WSABuilds/releases/download/wsa-v2311.40000.5.0/WSA_2407.40000.4.0_x64_vanilla.7z) | **Tier 1 (Production)** |
| **arm64 Standard Edition** | • Magisk Stable<br/>• OpenGApps Pico (arm64)<br/>• Native Qualcomm Snapdragon ABI | **Not currently pre-built** — no ARM64 assets are published on GitHub Releases yet; ARM64 CI enablement is tracked on the engineering roadmap (see `TODO.md`, Task 4.2) | **Tier 2 (Planned)** |

> [!TIP]
> **Architecture Guidance**:
> * **Download x64** if your computer has an **Intel** (Core, Xeon, Celeron) or **AMD** (Ryzen, Athlon) processor. It includes automated 64-bit ARM translation (libhoudini) allowing ARM-only apps and games to run transparently.
> * **ARM64 (Snapdragon) users**: pre-built ARM64 packages are **not currently published** on GitHub Releases, and the build pipeline currently targets x64 only (`build.sh --arch` accepts `x64`). Monitor the releases portal and the engineering roadmap for ARM64 enablement progress.

> [!NOTE]
> **Both editions ship in the same release.** In the release assets, `WSA_2407.40000.4.0_x64.7z` is the **Standard (rooted) Edition** and `WSA_2407.40000.4.0_x64_vanilla.7z` is the **Banking (unrooted) Edition**. SHA-256 checksums for both are published in `checksums.txt` on the same release page.

### WSABuilds Manager Desktop Application (v0.2.2)
Native desktop lifecycle manager with cold VHDX backups, safe rollback restores, and guided updates:
* **Portable Archive (.zip)**: [Download WSABuildsManager-Portable-0.2.2-x64.zip](https://github.com/IamAzmathullaShaikh/WSABuilds/releases/download/v0.2.2/WSABuildsManager-Portable-0.2.2-x64.zip) (Zero installation required)
* **Setup Installer (.exe)**: [Download WSABuildsManager-Setup-0.2.2-x64.exe](https://github.com/IamAzmathullaShaikh/WSABuilds/releases/download/v0.2.2/WSABuildsManager-Setup-0.2.2-x64.exe) (NSIS installation with Start Menu integration)
* **Windows Package Manager (Winget)**: Not yet installable — the manifest is prepared and pending microsoft/winget-pkgs review. Download directly using the links above meanwhile.

### Checksum Verification
Always verify your downloaded package integrity using Windows PowerShell before extraction:
```powershell
Get-FileHash -Algorithm SHA256 .\WSA_*.7z
```
Compare the output against the official hashes published in `checksums.txt` on the release page.

---

## 4. Quick Start Installation Guide

Follow these 3 steps to install or upgrade Windows Subsystem for Android on Windows 11 or Windows 10:

### Step 1: Enable Windows Virtualization (One-Time Setup)
Open PowerShell as **Administrator** and run:
```powershell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:HypervisorPlatform /all /norestart
```
*Restart your computer if prompted to finalize feature installation.* Ensure hardware virtualization (Intel VT-x or AMD-V) is enabled in your computer's BIOS/UEFI.

### Step 2: Extract the Package
Extract the downloaded `.7z` solid archive using **[7-Zip](https://www.7-zip.org/)** (v22.01 or later) or **WinRAR**:
* Extract to a permanent, non-temporary directory on your fastest drive (e.g. `C:\WSA` or `D:\WSABuilds`).
* *Do not extract to a temporary folder or `Downloads\Temp`, as Windows requires these files to remain on disk to run the subsystem.*

### Step 3: Run the Automated Installer
1. Open the extracted folder.
2. Locate **`Install.ps1`**, right-click it, and select **Run with PowerShell** (or execute in PowerShell).
3. The script verifies Developer Mode, validates partition images, registers the AppX manifest, and launches Windows Subsystem for Android.
4. Sign in to the **Google Play Store** and begin downloading apps.

> [!IMPORTANT]
> **Data-Preserving In-Place Upgrade Guarantee**:
> When updating to a newer release of WSABuilds, **DO NOT UNINSTALL** your existing installation. Simply download the new release, extract it, and run `Install.ps1`. Windows automatically updates the package files while preserving all your installed Android apps, logins, and virtual storage (`userdata.vhdx`).

---

## 5. System Requirements & Prerequisites

| Requirement | Minimum Specification | Recommended Specification |
|---|---|---|
| **Operating System** | Windows 11 (Build 22000+) or Windows 10 22H2 (Build 19045.2311+) | Windows 11 23H2 / 24H2 64-bit |
| **Processor Architecture** | x86_64 (64-bit Intel Core i3 / AMD Ryzen 3) or ARM64 (Qualcomm Snapdragon) | Intel Core i5/i7/i9 (8th Gen+) or AMD Ryzen 5/7/9 |
| **Hardware Virtualization** | Intel VT-x or AMD-V enabled in BIOS/UEFI | Nested virtualization enabled |
| **System Memory (RAM)** | 8 GB DDR4 | 16 GB DDR4 / DDR5 or higher |
| **Storage Drive** | 20 GB free space on standard HDD/SSD | 40+ GB free space on fast NVMe Solid State Drive (SSD) |
| **Windows Settings** | Developer Mode enabled (`Settings > System > For developers`) | Developer Mode enabled |

---

## 6. Application Compatibility Hub

WSABuilds maintains a community-curated database of Android application compatibility records under [compatibility/data/](compatibility/data/):

| Application Name | Category | Standard Edition (Magisk) | Banking Edition (Vanilla) | Notes & Requirements |
|---|---|---|---|---|
| **YONO SBI** | Banking & UPI | Workaround Required | **Supported (Native)** | Magisk requires Shamiko and DenyList; Banking Edition runs natively. |
| **PhonePe** | Banking & Payments | Workaround Required | **Supported (Native)** | Requires Developer Options / USB Debugging disabled in WSA Settings. |
| **Paytm** | Payments & Financial | **Supported** | **Supported** | Compatible out of the box. |
| **WhatsApp** | Messaging & Social | **Supported** | **Supported** | Requires manual verification code entry (no direct telephony SIM in WSA). |
| **Google Authenticator** | Security & 2FA | **Supported** | **Supported** | Verified on host container with active cloud backup sync. |
| **Microsoft Authenticator** | Security & Enterprise | **Supported** | **Supported** | Fully compatible with Azure AD and personal accounts. |

For detailed report specifications and PR moderation rules, refer to [compatibility/README.md](compatibility/README.md) or browse the live portal at [wsabuilds-website.pages.dev/compatibility](https://wsabuilds-website.pages.dev/compatibility).

---

## 7. Interactive Diagnostic Wizard

If you encounter initialization errors, AppX deployment blocks, or connectivity issues, use our web-based troubleshooter:
* **Online Wizard**: Use the interactive troubleshooter at [wsabuilds-website.pages.dev/troubleshoot/wizard](https://wsabuilds-website.pages.dev/troubleshoot/wizard) (live web route; source: `website/src/pages/troubleshoot/wizard.astro`).
* **Key Features**: Step-by-step diagnostic decision tree with copyable PowerShell commands for automated error remediation.

### Common Error Codes & Rapid Fixes:
* **`0x80370102` (Virtual Machine Platform Not Enabled)**:
  Run in Administrator PowerShell: `dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart` and verify Intel VT-x/AMD-V in BIOS.
* **`0x80070005` (Access Denied / Developer Mode Disabled)**:
  Enable Developer Mode in Windows: `Settings > System > For developers > Developer Mode (On)`.
* **`0x80073CF9` (AppX Installation Failed)**:
  Ensure destination directory is on an NTFS drive and that Windows AppX Deployment Service (`AppXSvc`) is running.

---

## 8. WSABuilds Manager (Desktop Application)

**Status**: *Preview Release (v0.2.2)* &nbsp;|&nbsp; Architecture Guide: [apps/manager/README.md](apps/manager/README.md)

WSABuilds Manager provides desktop lifecycle management for Windows Subsystem for Android:
* **Cold VHDX Snapshots**: Create instant, compressed backups of your Android user data (`userdata.vhdx`) with SHA-256 cryptographic verification.
* **One-Click Rollback Restores**: Restore previous virtual disk snapshots safely if an app update or module breaks your environment.
* **Pre-Flight Upgrade Inspections**: Verifies 25 GB free disk space, graceful subsystem shutdown, and package readiness before applying updates.
* **Subsystem Health Monitoring**: Real-time status reporting of Hyper-V virtualization state, AppX registration, and ADB bridge connectivity.

Download the standalone portable archive or setup installer directly from [Section 3: Downloads](#3-downloads--verification).

---

## 9. Release Validation Status & Quality Gates

In strict adherence to the **WSABuilds Master Governance Framework v5.1**, all releases are governed by transparent reality gates:

| Reality Dimension | Governance Status | Empirical Verification Evidence |
|---|---|---|
| **Repository Qualification** | **PASS (VERIFIED)** | 89 automated tests pass across Python (46), Website (28), and Manager (15) suites; plus a 20-check clean-room E2E gate (`scripts/e2e_clean_room.py`). 0 broken links, 0 secrets, 0 package identity drift. |
| **Build Reality Gate** | **PASS (VERIFIED)** | Build pipelines (`build.sh`, `build_local.py`) verified. Unpacked distribution and CPIO ramdisk structures verified. |
| **Runtime Reality Gate (Host)** | **PASS (VERIFIED)** | Verified on Windows host: active AppX registration (`Status: Ok`, `Version: 2407.40000.4.0`), `userdata.2.vhdx` (3.8 GB), and live `logcat` execution. |
| **Target Environment Gate** | **MANAGED** | Live Google Play Integrity attestation and physical locked VHDX file copy are actively observed in field validation. |

---

## 10. Build Matrix & Variant Transparency

To prevent user confusion, WSABuilds maintains total transparency regarding supported vs unsupported variants:

| Configuration Variant | Support Status | Rationale & Architectural Reality |
|---|---|---|
| **WSA x64 Standard (Magisk + Pico)** | **SUPPORTED** | **Tier 1 Primary Production**. Automated builds, official Magisk Stable, OpenGApps Pico ext4 overlay. |
| **WSA x64 Banking (Vanilla + Pico)** | **SUPPORTED** | **Tier 1 Enterprise Production**. Clean unrooted ramdisk, zero Magisk hooks, OpenGApps Pico ext4 overlay. |
| **WSABuilds Manager x64** | **SUPPORTED** | **Tier 1 Desktop Client**. Dual packaging (Portable ZIP + NSIS Setup), 15 passing unit tests. |
| **WSA arm64 Standard (Magisk + Pico)** | **NOT YET AVAILABLE** | **Tier 2 (Planned)**. No ARM64 assets are currently published; CI cross-compilation enablement is tracked on the engineering roadmap (see `TODO.md`, Task 4.2). |
| **Windows Insider Canary Channel** | **EXPERIMENTAL** | Subject to upstream Microsoft preview channel instability and internal API shifts. |
| **KernelSU Variants** | **NOT SUPPORTED** | **Eliminated**. Requires custom kernel source builds outside retail WSA; breaks automated updates. |
| **SuperSU Variants** | **NOT SUPPORTED** | **Eliminated**. Completely obsolete and incompatible with modern Android 13 (API 33). |
| **MindTheGapps Variants** | **NOT SUPPORTED** | **Eliminated**. Upstream `MindTheGappsBuilder` project is unmaintained for WSA. Standardized on Pico. |
| **Larger GApps (Nano/Micro/Full/Stock)**| **NOT SUPPORTED** | **Eliminated**. Excluded to prevent system partition bloat and ensure lightweight deployment. |
| **AOSP No-GApps Builds** | **NOT SUPPORTED** | **Eliminated**. Unsupported in CI automation; all official builds include verified Google Play services. |

---

## 11. Documentation Portal & Guides Index

| Subsystem / Topic | Authoritative Document | Focus & Content |
|---|---|---|
| **Subsystem Architecture** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Release engineering architecture, CI/CD matrix, and ramdisk trampolines |
| **In-Place Upgrades** | [docs/UPGRADE_VALIDATION.md](docs/UPGRADE_VALIDATION.md) | Data preservation guarantees, AppX package family mechanics, test harness |
| **Windows Validation Lab** | [docs/WINDOWS_VALIDATION_LAB.md](docs/WINDOWS_VALIDATION_LAB.md) | Self-hosted Windows validation runner topology, security, and setup scripts |
| **Desktop Manager** | [apps/manager/README.md](apps/manager/README.md) | Tauri v2, React 18, Rust cold VHDX backup, rollback snapshot, and IPC bridge |
| **Web Portal & Search** | [website/README.md](website/README.md) | Astro static site, Tailwind styling, Pagefind search, doc sync pipeline |
| **Validation Tooling** | [scripts/README.md](scripts/README.md) | 10 CLI validation tools (links, security, distribution, schema, identity) |
| **Privacy Telemetry** | [services/README.md](services/README.md) | Privacy-first telemetry aggregation engine, Zero-PII schema, metrics |
| **CI/CD Workflows** | [.github/WORKFLOWS.md](.github/WORKFLOWS.md) | 11 GitHub Actions workflows, tag triggers, secrets, and issue forms |
| **App Compatibility Hub** | [compatibility/README.md](compatibility/README.md) | Compatibility database schema, app records, and PR moderation rules |
| **Distribution Specs** | [deployment/SPECIFICATION.md](deployment/SPECIFICATION.md) | Versioning layer, artifact naming grammar, and Winget packaging rules |
| **Windows 11 Build Guide** | [WINDOWS11_BUILD_GUIDE.md](WINDOWS11_BUILD_GUIDE.md) | Exhaustive step-by-step developer compilation guide using WSL2 Ubuntu |
| **Developer Build Spec** | [BUILD.md](BUILD.md) | Pure-Python local Windows builder and ShellCheck requirements |

---

## 12. Community Governance & Contributions

We welcome community contributions, bug reports, and application compatibility records!
* **Issue Templates**: Structured forms for bug reports, feature suggestions, and compatibility submissions are available under [.github/ISSUE_TEMPLATE/](.github/ISSUE_TEMPLATE/).
* **Pull Request Guidelines**: Review our contribution checklist in [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md). All PRs must pass `build.yml` with 0 lint, link, or test failures.
* **Compatibility Submissions**: Submit new Android app compatibility reports by adding JSON records to [compatibility/data/](compatibility/data/). All submissions are automatically validated by CI schema checkers.
* **Moderation Policies**: Read our guidelines in [docs/community/compatibility-moderation.md](docs/community/compatibility-moderation.md) and [docs/community/discussions-governance.md](docs/community/discussions-governance.md).

---

## 13. Troubleshooting & Diagnostic Commands

Run these elevated PowerShell commands to resolve common environmental blocks:

### 1. Re-Enable Hyper-V & Virtual Machine Platform
```powershell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:HypervisorPlatform /all /norestart
```

### 2. Enable Windows Developer Mode via Registry
```powershell
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" /t REG_DWORD /f /v "AllowDevelopmentWithoutDevLicense" /d "1"
```

### 3. Connect ADB to WSA (Port 58526)
Ensure USB Debugging is turned on in WSA Advanced Settings, then run:
```powershell
adb connect 127.0.0.1:58526
adb devices
```

### 4. Automated Diagnostic Wizard
For guided, interactive troubleshooting, launch the web wizard at [wsabuilds-website.pages.dev/troubleshoot/wizard](https://wsabuilds-website.pages.dev/troubleshoot/wizard).

---

## 14. Security, CA Trust & Privacy-First Analytics

* **Microsoft Root Certificate Trust**: Network interactions with Microsoft's Windows Update Delivery Network (FE3) are secured via a bundled Microsoft Root Certificate Authority 2011 and Intermediate CA 2.1 certificate bundle, eliminating OS certificate store tampering.
* **Zero-PII Telemetry**: Public telemetry aggregated under [services/analytics/](services/analytics/) collects zero personally identifiable information (0 IP addresses, 0 device IDs, 0 usernames). Validated by [scripts/validate_analytics.py](scripts/validate_analytics.py).
* **Automated Security Scans**: Every commit is audited by [scripts/security_scan.py](scripts/security_scan.py) to prevent accidental inclusion of personal access tokens, credentials, or private machine paths.

---

## 15. Subsystem Architecture & Repository Structure

### Technical Highlights:
* **Ramdisk Trampoline Hooking**: Synthesizes standard SVR4 CPIO `initrd.img` archives containing `lspinit`, `wsainit` (stock init), and `magiskboot`. Magisk dynamic linkers and initialization scripts are mounted early-boot before Android zygote initialization.
* **Ext4 Loopback Overlays**: Minimal Android 13 Google Play Store ext4 filesystem overlays (`gapps-13.0-x86_64.img`) are mounted read-only via `gapps-13.0.rc` in early boot without altering Microsoft's original retail system partition.
* **Pixel 5 Build Property Spoofing**: Injects Google Pixel 5 (`redfin`) device fingerprints into `build.prop` via `fixGappsProp.py` to satisfy Google Play Protect device certification.

### Repository Layout:
```text
WSABuilds/
├── .github/workflows/         # Active CI/CD workflows (release, build, winget, validation)
├── apps/manager/              # WSABuilds Manager desktop client (Tauri v2 + React 18)
├── compatibility/data/        # Community Android app compatibility database
├── config/                    # Baseline AppX manifest identity specification
├── deployment/                # Version metadata layer and Winget manifest configs
├── docs/                      # Technical architecture, upgrade validation, and lab specs
├── Documentation/             # Comprehensive user, usage, and troubleshooting guides
├── MagiskOnWSA/               # Core build engine, update checkers, and XML SOAP templates
├── manifests/                 # Staged Winget distribution manifests (schema 1.6.0)
├── scripts/                   # 10 CLI validation and security auditing tools
├── services/analytics/        # Privacy-first telemetry aggregation engine
├── tests/                     # 89 automated tests (Python, Website, Manager)
├── website/                   # Official documentation portal, wizard, and downloads
├── WINDOWS11_BUILD_GUIDE.md   # WSL2 developer compilation guide
├── BUILD.md                   # Native Python Windows compilation guide
└── README.md                  # Master repository documentation
```

---

## 16. Local Compilation, Development & Testing

You can build WSABuilds packages locally using either Linux/WSL2 or native Windows Python:

### Method A: Linux / WSL2 Build Pipeline (`build.sh`)
```bash
cd MagiskOnWSA
# Build Standard Edition (Magisk Stable + OpenGApps Pico):
./scripts/build.sh --root-sol magisk --gapps pico --compress-format 7z

# Build Banking Edition (Vanilla / No Root + OpenGApps Pico):
./scripts/build.sh --root-sol none --gapps pico --compress-format 7z
```

### Method B: Native Windows Python Builder (`build_local.py`)
```cmd
cd MagiskOnWSA
REM Build Standard Edition:
python scripts\build_local.py --root-sol magisk --gapps pico

REM Build Banking Edition:
python scripts\build_local.py --root-sol none --gapps pico
```

### Running Automated Test Suites
```powershell
# Run Core Python Test Suite (44 tests):
python -m unittest discover -s tests -v

# Run Website Test Suite (22 tests):
npm test --prefix website

# Run Desktop Manager Test Suite (15 tests):
npm test --prefix apps/manager

# Run Link & Security Validators:
python scripts/check_doc_links.py
python scripts/security_scan.py
python scripts/validate_distribution.py
```

---

## 17. License & Trademarks

* **Build Scripts, Code & Tooling**: Licensed under the [GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)](LICENSE).
* **Documentation, Guides & Media**: Licensed under [Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC-BY-NC-ND-4.0)](LICENSE-CC-BY-NC-ND).
* **Trademarks**: **Windows Subsystem for Android™**, Windows 11, and Windows 10 are trademarks of Microsoft Corporation. Android™ and Google Play are trademarks of Google LLC. This open-source project is independently developed and is not affiliated with, endorsed by, or sponsored by Microsoft Corporation or Google LLC.
