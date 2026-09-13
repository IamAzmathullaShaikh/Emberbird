# WSABuilds — Windows Subsystem for Android™ Automation Platform

<p align="center">
  <img src="https://img.shields.io/badge/WSA-2407.40000.4.0-blue.svg?style=for-the-badge&logo=android" alt="WSA Version"/>
  <img src="https://img.shields.io/badge/Android-13.0%20(API%2033)-green.svg?style=for-the-badge&logo=android" alt="Android 13"/>
  <img src="https://img.shields.io/badge/GApps-OpenGApps%20Pico-orange.svg?style=for-the-badge&logo=googleplay" alt="OpenGApps Pico"/>
  <img src="https://img.shields.io/badge/Root-Magisk%20Stable%20(v30.6+)-red.svg?style=for-the-badge" alt="Magisk Stable"/>
  <img src="https://img.shields.io/badge/Architecture-x64%20%7C%20arm64-purple.svg?style=for-the-badge" alt="x64 / arm64"/>
  <img src="https://img.shields.io/github/actions/workflow/status/IamAzmathullaShaikh/WSABuilds/build.yml?label=CI%20Build&style=for-the-badge" alt="CI Status"/>
</p>

---

## 1. Project Overview

**WSABuilds** is an automated engineering and packaging platform for the **Windows Subsystem for Android (WSA)** on Windows 11 and Windows 10. The platform automates update discovery directly from Microsoft's Windows Update Delivery Network (FE3), seamlessly integrates **Magisk Stable root** into the early boot ramdisk (`initrd.img`), injects minimal **Google Play Store and Services (OpenGApps Pico)**, applies ARM translation layers (libhoudini), spoofs device properties to Google Pixel 5 (`redfin`) for Google Play Protect certification, and packages production-ready release archives.

### Primary Goals:
1. **Preserve Subsystem Integrity:** Retain official Microsoft AppX package identity (`MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe`) to allow in-place upgrades without losing user application data.
2. **Reliable Upstream Synchronization:** Automatically track and verify new WSA retail releases, official Magisk stable versions, and OpenGApps overlays without manual intervention.
3. **Reproducible Multi-Environment Builds:** Enable single-command compilation via both a modular Linux/WSL2 pipeline (`build.sh`) and a native pure-Python Windows builder (`build_local.py`).
4. **Strict Quality Gates:** Enforce automated package integrity, identity drift detection, offline validation, and security scans across all builds.

### Supported Build Targets:
* **Host Operating System:** Windows 11 (Build 22000+), Windows 10 (Build 19045+), and Ubuntu Linux (20.04/22.04/24.04 via WSL2 or CI runners).
* **Target Architectures:** `x64` (Primary) and `arm64`.
* **Target Release Channel:** `retail` (Production Stable).

---

## Downloads

<table>
<thead>
<tr>
<th>Operating System</th>
<th>Download Page</th>
</tr>
</thead>
<tbody>
<tr><td rowspan="4"><img src="https://upload.wikimedia.org/wikipedia/commons/e/e6/Windows_11_logo.svg" style="width: 200px;"/></td>
<td><p><a href="https://github.com/IamAzmathullaShaikh/WSABuilds/releases/latest"><img alt="win11x64downpre" src="https://img.shields.io/badge/Download%20Latest%20Release-Windows%2011%20x64-orange?style=for-the-badge&amp;logo=windows11"/></a></p></td>
</tr>
<tr>
<td><p><a href="https://github.com/IamAzmathullaShaikh/WSABuilds/releases/latest"><img alt="win11arm64downpre" src="https://img.shields.io/badge/Download%20Latest%20Release-Windows%2011%20arm64-orange?style=for-the-badge&amp;logo=windows11"/></a></p></td>
</tr>
<tr>
<td><p><a href="https://github.com/IamAzmathullaShaikh/WSABuilds/releases/latest"><img alt="win11x64downstable" src="https://img.shields.io/badge/Download%20Stable%20Package-Windows%2011%20x64-blue?style=for-the-badge&amp;logo=windows11"/></a></p></td>
</tr>
<tr>
<td><p><a href="https://github.com/IamAzmathullaShaikh/WSABuilds/releases/latest"><img alt="win11arm64downstable" src="https://img.shields.io/badge/Download%20Stable%20Package-Windows%2011%20arm64-blue?style=for-the-badge&amp;logo=windows11"/></a></p></td>
</tr>
<tr>
<td rowspan="2"><img src="https://upload.wikimedia.org/wikipedia/commons/0/05/Windows_10_Logo.svg" style="width: 200px;"/></td>
<td><p><a href="https://github.com/IamAzmathullaShaikh/WSABuilds/releases/latest"><img alt="win10x64down" src="https://img.shields.io/badge/Download%20Latest%20Release-Windows%2010%20x64-orange?style=for-the-badge&amp;logo=windows"/></a></p></td>
</tr>
<tr>
<td><p><a href="https://github.com/IamAzmathullaShaikh/WSABuilds/releases/latest"><img alt="win10x64down" src="https://img.shields.io/badge/Download%20Stable%20Package-Windows%2010%20x64-blue?style=for-the-badge&amp;logo=windows"/></a></p></td>
</tr>
</tbody>
</table>

---

## 2. Current Build Configuration

The active repository build configuration is locked and verified as follows:

| Component | Status | Details & Verification Evidence |
|---|---|---|
| **OpenGApps Pico** | **ACTUALLY BUILT (YES)** | **The sole active GApps distribution.** Built and mounted via `LSPosed/WSA-Addon` minimal ext4 images (`gapps-13.0-x86_64.img` + `gapps-13.0.rc`). Sourced in `build.sh` (lines 82–83) and `generateGappsLink.py`. Packages only `Phonesky.apk` (Play Store), `GmsCore.apk` (Google Play Services), and `GoogleServicesFramework.apk` (GSF). Verified in unit test `test_wsa_addon_gapps_discovery`. |
| **MindTheGapps** | **NOT BUILT (NO)** | Obsolete. The upstream `MindTheGappsBuilder` project is unmaintained for WSA. All MindTheGapps update checkers, build options, and documentation have been removed. |
| **OpenGApps Variants (Nano, Micro, Full, Stock)** | **NOT BUILT (NO)** | WSABuilds does not download or assemble larger OpenGApps variants. Only the lightweight Pico ext4 image is packaged to prevent bloat. |
| **NoGApps Builds** | **NOT BUILT (NO)** | CI/CD automation does not build or publish builds without GApps; builds are standardized on OpenGApps Pico. |
| **Magisk Stable** | **ACTUALLY BUILT (YES)** | Bundles official **Magisk Stable (≥ v26.0, currently v30.6+)**. Injects `magiskboot`, `lspinit`, and `overlay.d/sbin/init-ld.xz` into `initrd.img` with automated UID 0 ADB root shell privileges. |
| **KernelSU / SuperSU** | **NOT BUILT (NO)** | Unsupported. SuperSU is obsolete for modern Android (API 33). KernelSU requires custom kernel source tree builds outside of retail packaging. All KernelSU files have been purged. |

---

## 3. Supported Features

Only features verified by active repository code and tests are supported:

* **Automated Microsoft Retail WSA Fetching:** Pure-Python SOAP/XML interaction with the Windows Update FE3 delivery endpoint (`fe3.delivery.mp.microsoft.com`), secured by a bundled Microsoft Root Certificate Authority 2011 and Intermediate CA 2.1 certificate bundle.
* **Initrd Trampoline Ramdisk Hooking:** Synthesizes standard SVR4 CPIO `initrd.img` archives containing `lspinit`, `wsainit`, `magiskboot`, `overlay.d/sbin/init-ld.xz`, and Magisk 26+ dynamic linker support.
* **OpenGApps Loopback Overlay Mounting:** Integrates minimal Android 13 ext4 filesystem overlays (`gapps-13.0-x86_64.img`) mounted via `gapps-13.0.rc` in early boot without modifying base system partitions.
* **Google Play Protect Certification Spoofing:** Injects Google Pixel 5 (`redfin`) device fingerprints into `build.prop` via `fixGappsProp.py` to ensure certified device status in the Google Play Store.
* **Zero-Click Automated ADB Root Authorization:** Automatically seeds the host's `adbkey.pub` into `overlay.d/sbin/adbkey.pub` and pre-configures Magisk's database (`/data/adb/magisk.db`) granting ADB shell (UID 2000) immediate root permissions.
* **Preserved AppX Identity:** Preserves Microsoft package family name `MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe` and publisher identity `8wekyb3d8bbwe` across all builds, ensuring seamless upgrades.
* **Dual Compilation Backends:** Fully functional compilation via Linux / WSL2 (`build.sh`) and native pure-Python Windows builder (`build_local.py`).
* **Automated Release Engineering:** 3-stage GitHub Actions lifecycle generating LZMA2 solid 7z archives, GNU SHA-256 digests, and machine-readable `release-metadata.json`.

---

## 4. Removed Components

As part of the forensic audit and technical debt reduction refactoring, all dead, unmaintained, and unsupported components were pruned:

* **KernelSU Removal:** Removed `generateKernelSULink.py`, `KernelSUUpdateCheck.py`, all KernelSU installation guides, and KernelSU radio options from `run.sh`.
* **SuperSU Removal:** Purged all historical references and obsolete SuperSU assumptions.
* **Legacy Build System Purge (`MagiskOnWSAOld/`):** Deleted 703 stale files, old compiled binaries (`makepri.exe`, `fuse.erofs`, `mkfs.erofs`), old DLLs, and duplicate build scripts targeting obsolete MindTheGapps and KernelSU pipelines.
* **Obsolete Update Checkers:** Deleted `MTGUpdateCheck.py` (MindTheGapps), `MagiskCanaryUpdateCheck.py` (Canary), `WSAInsiderUpdateCheck.py` (Insider), `update-downloadvar.py` (broken table parser), and `windows10patch.ps1`.
* **Dead Helper Utilities:** Deleted `WSAUpdateChecker.py` (monolithic legacy updater) and `magisk_debug.sh` (unused upstream script).
* **Stale Documentation:** Deleted `MagiskOnWSA/docs/` (legacy duplicate docs, stub `index.html`) and `Documentation/Usage Guides/Post-Installation Guides/` (29 unreferenced splash pages for deprecated variants).

---

## 5. Repository Structure

```text
WSABuilds/
├── .github/
│   └── workflows/                # Active GitHub Actions CI/CD workflows
│       ├── build.yml             # Code quality, ShellCheck, compileall, unit tests
│       ├── release.yml           # 3-stage build, validation, and release publisher
│       ├── validation.yml        # Subsystem and package integrity validation
│       ├── update.yml            # Automated update discovery (Retail WSA, Magisk, GApps)
│       ├── docs.yml              # Markdown link integrity checker
│       └── security.yml          # Secret, token, and developer path audit
├── config/
│   └── baseline-identity.json    # Canonical AppX manifest identity baseline
├── docs/                         # Reliability engineering specifications
│   ├── ARCHITECTURE.md           # CI/CD and release architecture
│   ├── UPGRADE_VALIDATION.md     # In-place upgrade compatibility standards
│   └── WINDOWS_VALIDATION_LAB.md # Windows validation laboratory setup
├── Documentation/                # Authoritative user guides and documentation
│   ├── Fix Guides/               # Pre-install and post-install error resolution
│   ├── Sponsors/                 # Project sponsors
│   ├── Usage Guides/             # GPU selection, ADB sideloading, moving drive
│   └── WSABuilds/                # App compatibility, installation, updates, FAQ
├── MagiskOnWSA/                  # Core build system & update automation
│   ├── libhoudini/               # ARM64 translation libraries and installer
│   ├── scripts/                  # Core Linux build scripts (build.sh, extractors)
│   ├── Update Check/             # Modular update discovery (FE3, Magisk, GApps)
│   └── xml/                      # Microsoft FE3 SOAP request templates
├── scripts/                      # Release validation & security tooling
│   ├── check_doc_links.py        # Markdown local link validator
│   ├── generate_release_metadata.py # SHA-256 and JSON metadata generator
│   ├── security_scan.py          # Credential and token scanner
│   ├── validate_gapps.py         # Google Play component validator (Mode B offline)
│   ├── validate_magisk.py        # Magisk trampoline validator (Mode B offline)
│   ├── validate_package_identity.py # AppX identity baseline comparator
│   └── validate_package_integrity.py # Package file structure validator
├── templates/
│   └── release-notes-retail.md   # Release notes template
├── tests/                        # Offline unit test suite (24 passing tests)
│   ├── test_cpio_builder.py      # SVR4 CPIO and XZ compression tests
│   ├── test_identity_and_integrity.py # Identity drift and integrity tests
│   ├── test_props_spoof.py       # Pixel 5 build property spoofing tests
│   └── test_runtime_defects.py   # Runtime defects remediation tests (RT-01 to RT-04)
├── WSABuilds Utilities/          # End-user maintenance utilities
│   ├── Uninstall Script/         # Automated WSA uninstaller with restore points
│   └── Update Script/            # Automated WSA updater utility
├── BUILD.md                      # Developer build specifications
├── CLEANUP_REPORT.md             # Forensic static analysis and cleanup log
├── REMOVED_ROOT_SOLUTIONS.md     # KernelSU and SuperSU removal report
├── REPOSITORY_AUDIT.md           # Comprehensive repository-wide audit report
├── WINDOWS11_BUILD_GUIDE.md      # Standalone Windows 11 compilation guide
└── README.md                     # Master documentation
```

---

## 6. Dependencies

| Dependency | Minimum Version | Recommended Version | Scope / Purpose |
|---|---|---|---|
| **Git** | `2.34+` | `2.45+` | Version control, long path support (`core.longpaths`). |
| **Python** | `3.10` | `3.12+` | Standalone builder (`build_local.py`), validation scripts, update checks. |
| **Python Libraries** | — | — | `requests`, `packaging`, `certifi`, `beautifulsoup4`, `lxml`. |
| **WSL2** | `2.0+` | Latest | Linux build environment for `MagiskOnWSA/scripts/build.sh`. |
| **Linux Distribution** | Ubuntu 20.04 | Ubuntu 24.04 LTS | Standard WSL2 distribution for compilation. |
| **Linux Packages** | — | — | `e2fsprogs`, `attr`, `unzip`, `qemu-utils`, `aria2`, `p7zip-full`, `curl`, `xmlstarlet`. |
| **PowerShell** | `5.1` | `7.4+` | Host installation scripts (`Install.ps1`), DISM feature enablement. |
| **7-Zip** | `22.01` | `24.05+` (64-bit) | Release archive extraction and solid LZMA2 compression. |
| **GitHub Actions** | — | Standard Runner | Ubuntu 22.04 / 24.04 runners (`ubuntu-latest`). |

---

## 7. Windows 11 Build Guide

For complete, exhaustive instructions, refer to [WINDOWS11_BUILD_GUIDE.md](WINDOWS11_BUILD_GUIDE.md).

### Quickstart: Building on Windows 11 using WSL2

```powershell
# 1. Enable Virtualization & WSL in PowerShell (Administrator)
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:HypervisorPlatform /all /norestart
wsl --install -d Ubuntu

# 2. Inside WSL2 Ubuntu terminal:
sudo apt-get update && sudo apt-get install -y \
  bash curl wget aria2 unzip p7zip-full python3 python3-pip python3-venv \
  e2fsprogs attr qemu-utils xmlstarlet libxml2-utils

# 3. Clone Repository:
git clone https://github.com/IamAzmathullaShaikh/WSABuilds.git
cd WSABuilds/MagiskOnWSA

# 4. Initialize Python Environment:
python3 -m venv python3-env
source python3-env/bin/activate
pip install -r scripts/requirements.txt

# 5. Build WSA Package (Magisk Stable + OpenGApps Pico):
./scripts/build.sh --compress-format 7z
```

Output is generated at `MagiskOnWSA/output/` as both an uncompressed directory and a `.7z` solid archive.

---

## 8. Release Process

Production release engineering follows a strictly validated 3-stage pipeline:

```text
[Stage 1: Verify Quality Gates]
  ├── Validate Baseline Identity Schema (baseline-identity.json)
  ├── Compile Python Sources (compileall)
  └── Run Complete Offline Unit Test Suite (python -m unittest)
             │ (Quality Gate Pass)
             ▼
[Stage 2: Build Release Package]
  ├── Query Microsoft FE3 for Retail WSA MSIX
  ├── Query topjohnwu/Magisk for Magisk Stable APK
  ├── Query LSPosed/WSA-Addon for OpenGApps Pico Ext4 Image
  ├── Assemble initrd.img & Inject Trampolines (build.sh)
  ├── Validate Package Subsystems (validate_magisk.py, validate_gapps.py)
  └── Upload Staged Release Artifact
             │ (Subsystems Validated)
             ▼
[Stage 3: Publish Release]
  ├── Download Staged Artifact
  ├── Compute GNU Coreutils SHA-256 Checksum
  ├── Generate release-metadata.json
  └── Publish to GitHub Releases (softprops/action-gh-release@v2)
```

---

## 9. Frequently Asked Questions (FAQs)

### Q: Why does this repository build OpenGApps Pico instead of MindTheGapps?
**A:** The upstream `MindTheGappsBuilder` project is no longer maintained for Windows Subsystem for Android. `LSPosed/WSA-Addon` provides battle-tested, ready-to-mount ext4 loopback images (`gapps-13.0-x86_64.img`) for Android 13 that integrate seamlessly into WSA without modifying system partitions.

### Q: Can I install this on Windows 10?
**A:** Yes. Builds are compatible with Windows 10 22H2 (Build 19045.2311+). Ensure `VirtualMachinePlatform` is enabled.

### Q: Does updating overwrite my Android apps and games?
**A:** No. Because WSABuilds preserves Microsoft's official AppX package identity (`MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe`), updating via `Install.ps1` performs an in-place upgrade that preserves your user data (`userdata.vhdx`).

### Q: Where did KernelSU and SuperSU go?
**A:** SuperSU cannot run on modern Android 13+. KernelSU requires compiling custom kernels into WSA which breaks upgrade compatibility and automated update delivery. Both have been removed to ensure the platform remains stable and focused exclusively on Magisk Stable.

---

## 10. Contributing

Contributions are welcome! Please follow these rules:
1. **Preserve Quality Gates:** All pull requests must pass `build.yml` (ShellCheck, `compileall`, and 24 unit tests).
2. **Document Link Integrity:** Run `python scripts/check_doc_links.py` before submitting to ensure no broken Markdown links.
3. **Security:** Run `python scripts/security_scan.py` to ensure no personal access tokens, credentials, or machine paths are introduced.
4. **Scope:** Keep changes aligned with the locked production target (Retail WSA, Magisk Stable, OpenGApps Pico). Do not introduce unmaintained root or GApps variants.

---

## 11. License

* **Build Scripts & Tooling:** Licensed under the [GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)](LICENSE).
* **Documentation & Media:** Licensed under [Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC-BY-NC-ND-4.0)](LICENSE-CC-BY-NC-ND).
* **Windows Subsystem for Android™** is a trademark of Microsoft Corporation. This project is not affiliated with, endorsed by, or sponsored by Microsoft.
