# Emberbird — Windows Subsystem for Android™ Automation Platform

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

## 1. Current Project Overview

**Emberbird** is an automated engineering and packaging platform for the **Windows Subsystem for Android (WSA)** on Windows 11 and Windows 10. Microsoft ended WSA development in March 2025; this platform continues patched, verified builds of the subsystem. It automates update discovery directly from Microsoft's Windows Update Delivery Network (FE3), integrates minimal **Google Play Store and Services (OpenGApps Pico)**, provides automated ARM translation layers (libhoudini) for x86_64 PCs, spoofs device properties to Google Pixel 5 (`redfin`) for Google Play Protect certification, and packages production-ready release archives in two officially supported **Tier 1 Editions**:

1. **Standard Edition (Rooted)**: Official Magisk Stable (v30.6+) and OpenGApps Pico for developers, modders, and power users.
2. **Banking & Enterprise Edition (Unrooted)**: Clean, unrooted ramdisk with OpenGApps Pico for users requiring 100% compatibility with banking, UPI, streaming DRM, and enterprise applications.

### Key Guarantees

* **Registry-First Release Intelligence**: Every download link, version, and hash the platform publishes is derived from the validated release registry (`data/releases/releases.json`). No hardcoded release truth exists anywhere in the platform.
* **Preserved Subsystem Identity**: Retains official Microsoft AppX package identity (`MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe`), ensuring clean in-place upgrades without user application data loss.
* **Unified Windows Support**: The exact same package installs on both **Windows 11 (Build 22000+)** and **Windows 10 22H2 (Build 19045.2311+)**. There are no separate OS downloads.
* **Reproducible Multi-Environment Builds**: Automated building via Linux/WSL2 (`build.sh`) and native pure-Python on Windows (`build_local.py`).
* **Strict Quality Gates**: Every build is checked against automated package integrity, identity drift detection, offline validation, and credential security scans.

---

## 2. Supported Build Types

Emberbird provides two purpose-built Tier 1 subsystem configurations plus a desktop manager:

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

* **Choose Standard Edition if**: You need root access, want to run Magisk modules (LSPosed, Zygisk), customize Android system files, or require an elevated ADB root shell.
* **Choose Banking & Enterprise Edition if**: You use financial apps (e.g. YONO SBI, PhonePe, Google Pay, Paytm), government identification apps, OTT streaming apps with strict Widevine DRM, or corporate work profiles that reject modified or rooted devices.

### WSABuilds Manager (Desktop Application, v0.2.2)

Native desktop lifecycle manager for the subsystem — architecture guide: [apps/manager/README.md](apps/manager/README.md).

* **Cold VHDX Snapshots**: Instant, compressed backups of your Android user data (`userdata.vhdx`) with SHA-256 cryptographic verification.
* **One-Click Rollback Restores**: Restore previous virtual disk snapshots safely if an app update or module breaks your environment.
* **Pre-Flight Upgrade Inspections**: Verifies 25 GB free disk space, graceful subsystem shutdown, and package readiness before applying updates.
* **Subsystem Health Monitoring**: Real-time status of Hyper-V virtualization state, AppX registration, and ADB bridge connectivity.

### Variant Transparency Matrix

Total transparency regarding supported vs unsupported variants:

| Configuration Variant | Support Status | Rationale & Architectural Reality |
|---|---|---|
| **WSA x64 Standard (Magisk + Pico)** | **SUPPORTED** | **Tier 1 Primary Production**. Automated builds, official Magisk Stable, OpenGApps Pico ext4 overlay. |
| **WSA x64 Banking (Vanilla + Pico)** | **SUPPORTED** | **Tier 1 Enterprise Production**. Clean unrooted ramdisk, zero Magisk hooks, OpenGApps Pico ext4 overlay. |
| **WSABuilds Manager x64** | **SUPPORTED** | **Tier 1 Desktop Client**. Dual packaging (Portable ZIP + NSIS Setup) with unit-test coverage. |
| **WSA arm64 Standard (Magisk + Pico)** | **NOT YET AVAILABLE** | **Tier 2 (Planned)**. No ARM64 assets are currently published; CI cross-compilation enablement is tracked on the engineering roadmap (see `TODO.md`, Task 4.2). |
| **Windows Insider Canary Channel** | **EXPERIMENTAL** | Subject to upstream Microsoft preview channel instability and internal API shifts. |
| **KernelSU Variants** | **NOT SUPPORTED** | **Eliminated**. Requires custom kernel source builds outside retail WSA; breaks automated updates. |
| **SuperSU Variants** | **NOT SUPPORTED** | **Eliminated**. Completely obsolete and incompatible with modern Android 13 (API 33). |
| **MindTheGapps Variants** | **NOT SUPPORTED** | **Eliminated**. Upstream `MindTheGappsBuilder` project is unmaintained for WSA. Standardized on Pico. |
| **Larger GApps (Nano/Micro/Full/Stock)** | **NOT SUPPORTED** | **Eliminated**. Excluded to prevent system partition bloat and ensure lightweight deployment. |
| **AOSP No-GApps Builds** | **NOT SUPPORTED** | **Eliminated**. Unsupported in CI automation; all official builds include verified Google Play services. |

---

## 3. Release Architecture

### How releases are organized

* **One tag, both editions.** The current production release is tagged `wsa-v2311.40000.5.0` and ships both editions: `WSA_2407.40000.4.0_x64.7z` is the **Standard (rooted) Edition** and `WSA_2407.40000.4.0_x64_vanilla.7z` is the **Banking (unrooted) Edition**. (The tag name reflects the discovery baseline; the enclosed packages are `2407.40000.4.0` — the release registry records this mapping explicitly.)
* **Checksums are published beside the packages.** SHA-256 checksums for every package are published in `checksums.txt` on the same release page.
* **A separate tag carries the Manager.** Desktop Manager releases are tagged `v*` (currently `v0.2.2`) and never displace the subsystem release from `/releases/latest`.
* **Channels.** Subsystem builds ship on the `retail` channel; Manager releases on the `stable` channel. The channel contract (`data/contracts/channel-contract.md`) defines the tokens and their mapping to release reality.
* **ARM64**: pre-built ARM64 packages are **not currently published**. The build pipeline currently targets x64 only. Monitor the releases portal and the engineering roadmap (`TODO.md`, Task 4.2) for ARM64 enablement progress.

### Official Release Packages (Tier 1 Production)

| Architecture & Edition | Package Contents | Verified Download Target | Build Channel |
|---|---|---|---|
| **x64 Standard Edition** | • Magisk Stable (v30.6+)<br/>• OpenGApps Pico (Play Store + Services)<br/>• Automated Root & Pixel 5 Spoofing | [Download Standard Edition (x64)](https://github.com/IamAzmathullaShaikh/WSABuilds/releases/download/wsa-v2311.40000.5.0/WSA_2407.40000.4.0_x64.7z) | **Tier 1 (Production)** |
| **x64 Banking Edition** | • Vanilla (Clean Ramdisk, Zero Root)<br/>• OpenGApps Pico (Play Store + Services)<br/>• Pixel 5 Spoofing (Banking App Safe) | [Download Banking Edition (x64)](https://github.com/IamAzmathullaShaikh/WSABuilds/releases/download/wsa-v2311.40000.5.0/WSA_2407.40000.4.0_x64_vanilla.7z) | **Tier 1 (Production)** |
| **arm64 Standard Edition** | • Magisk Stable<br/>• OpenGApps Pico (arm64)<br/>• Native Qualcomm Snapdragon ABI | **Not currently pre-built** — no ARM64 assets are published on GitHub Releases yet; ARM64 CI enablement is tracked on the engineering roadmap (see `TODO.md`, Task 4.2) | **Tier 2 (Planned)** |

### Manager Downloads

* **Portable Archive (.zip)**: [Download WSABuildsManager-Portable-0.2.2-x64.zip](https://github.com/IamAzmathullaShaikh/WSABuilds/releases/download/v0.2.2/WSABuildsManager-Portable-0.2.2-x64.zip) (Zero installation required)
* **Setup Installer (.exe)**: [Download WSABuildsManager-Setup-0.2.2-x64.exe](https://github.com/IamAzmathullaShaikh/WSABuilds/releases/download/v0.2.2/WSABuildsManager-Setup-0.2.2-x64.exe) (NSIS installation with Start Menu integration)
* **Windows Package Manager (Winget)**: Not yet installable — the manifest is prepared and pending microsoft/winget-pkgs review. Download directly using the links above meanwhile.

### Checksum Verification

Always verify your downloaded package integrity using Windows PowerShell before extraction:

```powershell
Get-FileHash -Algorithm SHA256 .\WSA_*.7z
```

Compare the output against the official hashes published in `checksums.txt` on the release page. The registry's vault (`data/releases/releases.json`) records the authoritative hash for every published package cut.

---

## 4. Registry Architecture

The platform's release intelligence lives in **one validated registry** — not in READMEs, scripts, or workflow files.

### Components

| Component | Path | Role |
|---|---|---|
| **Registry** | `data/releases/releases.json` | The single source of truth: every release, edition, architecture, asset, and hash |
| **Schema (contract)** | `data/releases/releases.schema.json` | Draft-07 JSON Schema; rejects placeholder hashes and malformed entries structurally |
| **Generator** | `scripts/build_registry.py` | Idempotent generator that rebuilds the registry from live published GitHub reality |
| **Release Engine** | `platform/release-engine/` | Lookup + integrity service (`Registry`, `check_integrity`, `validate` CLI) |
| **Contracts** | `data/contracts/` | `release-contract.md` (frozen) and `channel-contract.md` |
| **Governance** | `data/releases/GOVERNANCE.md` | Evolution policy, hash doctrine, supersession and mirror rules |

### Binding rules

1. **Registry Independence**: No consumer (website, manager, CI, docs) may hardcode tags, hashes, or URLs. All release intelligence is derived from the registry. This is proven by `tests/test_registry_consumer.py` and enforced by the frozen release contract.
2. **Published Artifacts Are Truth**: A release exists in the registry only if its artifacts are published and their hashes were computed from the published bytes. If documentation and reality disagree, reality wins and the docs are corrected.
3. **Artifact identity = (package_name + sha256)**, never filename alone. Different releases may ship identical filenames with different hashes; the vault tracks each cut separately (currently 9 package cuts across 6 release entries).
4. **`recommended` is policy, `latest` is fact.** `latest` is chronological; `recommended` is set only by a designated policy system (Ember Observatory, Phase 5). Never assume they are equal. P0 ships with no recommendation; consumers fall back to `latest`.
5. **Provenance on every entry.** Each release records how it entered the registry — `provenance` (tool, mode, commit, generated_at) per release-contract §4.3 — and the whole-registry `generation` block records the reality source. Provenance timestamps are excluded from drift detection.

### Validating the registry

```bash
# Integrity checks + schema contract (CI Truth Gate — build.yml runs this)
python platform/release-engine/release_engine/__main__.py validate --schema
# REGISTRY OK: 6 releases, 9 vault entries (schema_version=1, migration=2, compatibility=backward)
# SCHEMA OK: registry conforms to releases.schema.json (draft-07 subset validator)
```

Detecting drift between registry states (added/removed releases, hash changes,
asset changes, status changes — provenance timestamps excluded by design):

```bash
python platform/release-engine/release_engine/__main__.py diff previous-releases.json
# add --fail-on-drift to enforce the no-drift policy (exit 2 on drift)
```

Regenerating from reality (requires network access to the GitHub API):

```bash
python scripts/build_registry.py
```

Every registry entry carries a provenance record (tool, mode, commit, generated_at)
mandated by the release contract; the whole-registry `generation` block records
the reality source the generator read.

---

## 5. Repository Structure

```text
WSABuilds/
├── .github/workflows/         # Active CI/CD workflows (release, build, winget, validation)
├── apps/manager/              # WSABuilds Manager desktop client (Tauri v2 + React 18)
├── compatibility/data/        # Community Android app compatibility database
├── config/                    # Baseline AppX manifest identity specification
├── data/contracts/            # Frozen platform contracts (release, channel)
├── data/releases/             # THE release registry: schema, generated registry, governance
├── deployment/                # Version metadata layer and Winget manifest configs
├── docs/archive/              # Historical upstream-era user docs (frozen record)
├── upstream/                  # Vendored upstream build inputs (provenance-pinned)
├── tools/                     # Build engine, update checkers, and XML SOAP templates
├── utilities/                 # User utility scripts (update / uninstall helpers)
├── manifests/                 # Staged Winget distribution manifests (schema 1.6.0)
├── platform/release-engine/   # Registry metadata service (lookup, integrity, validate CLI)
├── scripts/                   # CLI validation tools + the registry generator
├── services/analytics/        # Privacy-first telemetry aggregation engine
├── tests/                     # automated Python tests (unit, contract, consumer, reality)
├── website/                   # Official documentation portal, wizard, and downloads
├── WINDOWS11_BUILD_GUIDE.md   # WSL2 developer compilation guide
├── BUILD.md                   # Native Python Windows compilation guide
└── README.md                  # Master repository documentation (this file)
```

### Documentation map

| Subsystem / Topic | Authoritative Document | Focus & Content |
|---|---|---|
| **Subsystem Architecture** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Release engineering architecture, CI/CD matrix, ramdisk trampolines |
| **Emberbird Charter** | [docs/EMBERBIRD_CHARTER.md](docs/EMBERBIRD_CHARTER.md) | Platform mission, Bold Rule, governance pillars |
| **License Audit** | [docs/LICENSE_AUDIT.md](docs/LICENSE_AUDIT.md) | AGPL-3.0 posture, third-party license obligations |
| **Attribution** | [docs/ATTRIBUTION.md](docs/ATTRIBUTION.md) | Upstream ancestry and embedded components |
| **In-Place Upgrades** | [docs/UPGRADE_VALIDATION.md](docs/UPGRADE_VALIDATION.md) | Data preservation guarantees, AppX package family mechanics, test harness |
| **Windows Validation Lab** | [docs/WINDOWS_VALIDATION_LAB.md](docs/WINDOWS_VALIDATION_LAB.md) | Self-hosted Windows validation runner topology, security, and setup scripts |
| **Desktop Manager** | [apps/manager/README.md](apps/manager/README.md) | Tauri v2, React 18, Rust cold VHDX backup, rollback snapshot, and IPC bridge |
| **Web Portal & Search** | [website/README.md](website/README.md) | Astro static site, Tailwind styling, Pagefind search, doc sync pipeline |
| **Validation Tooling** | [scripts/README.md](scripts/README.md) | CLI validation tools (links, security, distribution, schema, identity) |
| **Privacy Telemetry** | [services/README.md](services/README.md) | Privacy-first telemetry aggregation engine, Zero-PII schema, metrics |
| **CI/CD Workflows** | [.github/WORKFLOWS.md](.github/WORKFLOWS.md) | GitHub Actions workflows, tag triggers, secrets, and issue forms |
| **App Compatibility Hub** | [compatibility/README.md](compatibility/README.md) | Compatibility database schema, app records, and PR moderation rules |
| **Distribution Specs** | [deployment/SPECIFICATION.md](deployment/SPECIFICATION.md) | Versioning layer, artifact naming grammar, and Winget packaging rules |
| **Windows 11 Build Guide** | [WINDOWS11_BUILD_GUIDE.md](WINDOWS11_BUILD_GUIDE.md) | Exhaustive step-by-step developer compilation guide using WSL2 Ubuntu |
| **Developer Build Spec** | [BUILD.md](BUILD.md) | Pure-Python local Windows builder and ShellCheck requirements |

---

## 6. Windows 11 Build Guide

Two paths are supported: **installing a published release** (most users) and **building from source** (developers).

### 6a. Install a Published Release (3 steps)

**Step 1 — Enable Windows Virtualization (one-time setup)**. Open PowerShell as **Administrator** and run:

```powershell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:HypervisorPlatform /all /norestart
```

*Restart your computer if prompted to finalize feature installation.* Ensure hardware virtualization (Intel VT-x or AMD-V) is enabled in your computer's BIOS/UEFI.

**Step 2 — Extract the package**. Extract the downloaded `.7z` solid archive using **[7-Zip](https://www.7-zip.org/)** (v22.01 or later) or WinRAR:

* Extract to a permanent, non-temporary directory on your fastest drive (e.g. `C:\WSA` or `D:\Emberbird`).
* *Do not extract to a temporary folder or `Downloads\Temp`, as Windows requires these files to remain on disk to run the subsystem.*

**Step 3 — Run the automated installer**:

1. Open the extracted folder.
2. Locate **`Install.ps1`**, right-click it, and select **Run with PowerShell** (or execute it in a PowerShell window).
3. The script verifies Developer Mode, validates partition images, registers the AppX manifest, and launches Windows Subsystem for Android.
4. Sign in to the **Google Play Store** and begin downloading apps.

> [!IMPORTANT]
> **Data-Preserving In-Place Upgrade Guarantee**: When updating to a newer release, **DO NOT UNINSTALL** your existing installation. Simply download the new release, extract it, and run `Install.ps1`. Windows automatically updates the package files while preserving all your installed Android apps, logins, and virtual storage (`userdata.vhdx`).

### 6b. Build from Source on Windows 11

**Linux/WSL2 pipeline** (`build.sh`):

```bash
cd tools
# Standard Edition (Magisk Stable + OpenGApps Pico):
./build.sh --root-sol magisk --gapps pico --compress-format 7z
# Banking Edition (Vanilla / No Root + OpenGApps Pico):
./build.sh --root-sol none --gapps pico --compress-format 7z
```

**Native Windows Python builder** (`build_local.py`) — no WSL required:

```cmd
cd tools
REM Standard Edition:
python build_local.py --root-sol magisk --gapps pico
REM Banking Edition:
python build_local.py --root-sol none --gapps pico
```

For the exhaustive walkthrough (WSL2 Ubuntu setup, dependency versions, troubleshooting), see [WINDOWS11_BUILD_GUIDE.md](WINDOWS11_BUILD_GUIDE.md) and [BUILD.md](BUILD.md).

### System Requirements & Prerequisites

| Requirement | Minimum Specification | Recommended Specification |
|---|---|---|
| **Operating System** | Windows 11 (Build 22000+) or Windows 10 22H2 (Build 19045.2311+) | Windows 11 23H2 / 24H2 64-bit |
| **Processor Architecture** | x86_64 (64-bit Intel Core i3 / AMD Ryzen 3) or ARM64 (Qualcomm Snapdragon) | Intel Core i5/i7/i9 (8th Gen+) or AMD Ryzen 5/7/9 |
| **Hardware Virtualization** | Intel VT-x or AMD-V enabled in BIOS/UEFI | Nested virtualization enabled |
| **System Memory (RAM)** | 8 GB DDR4 | 16 GB DDR4 / DDR5 or higher |
| **Storage Drive** | 20 GB free space on standard HDD/SSD | 40+ GB free space on fast NVMe Solid State Drive (SSD) |
| **Windows Settings** | Developer Mode enabled (`Settings > System > For developers`) | Developer Mode enabled |

---

## 7. Dependency Installation

Fresh Windows 11 machine → build-ready, using PowerShell:

```powershell
# 1. Git for Windows
winget install --id Git.Git -e

# 2. Python 3.11+ (the registry tooling and test suite are stdlib-first;
#    jsonschema is the only optional dependency, used when present)
winget install --id Python.Python.3.12 -e

# 3. 7-Zip (build packaging and manual extraction)
winget install --id 7zip.7zip -e

# 4. Node.js LTS (website + manager web UI)
winget install --id OpenJS.NodeJS.LTS -e

# 5. Rust toolchain (desktop manager backend)
winget install --id Rustlang.Rustup -e
```

Verify the toolchain:

```powershell
git --version; python --version; node --version; npm --version
```

WSL2 users (for `build.sh`) additionally need an Ubuntu environment with the packages listed in [WINDOWS11_BUILD_GUIDE.md](WINDOWS11_BUILD_GUIDE.md).

---

## 8. Developer Setup

```powershell
# Clone and enter the repository
git clone https://github.com/IamAzmathullaShaikh/WSABuilds.git
cd WSABuilds

# Optional Python environment (the core suite is stdlib-only)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install jsonschema   # optional: enables schema-contract tests

# Sanity-check the toolchain against repository reality
python -m unittest discover -s tests
python platform/release-engine/release_engine/__main__.py validate
```

Notes:

* `jsonschema` is **optional**: tests that need it skip cleanly when it is absent, so CI runs the full structural suite without installing it.
* The release engine package lives at `platform/release-engine/release_engine/` (importable as `release_engine` with that parent directory on `sys.path`; the `validate` CLI bootstraps its own path).
* Website development: `npm ci` inside `website/`. Manager development: see [apps/manager/README.md](apps/manager/README.md).

---

## 9. Build Instructions

Covered in [Section 6b](#6b-build-from-source-on-windows-11). Quick reference:

| Target | Command | Environment |
|---|---|---|
| Standard Edition | `./scripts/build.sh --root-sol magisk --gapps pico --compress-format 7z` | Linux/WSL2 |
| Banking Edition | `./scripts/build.sh --root-sol none --gapps pico --compress-format 7z` | Linux/WSL2 |
| Standard Edition | `python scripts\build_local.py --root-sol magisk --gapps pico` | Native Windows |
| Banking Edition | `python scripts\build_local.py --root-sol none --gapps pico` | Native Windows |

The pipeline currently targets **x64**. ARM64 enablement is roadmap work (Task 4.2) and is not yet part of the supported build matrix.

---

## 10. Validation Instructions

Every change is validated locally before push; CI ratifies independently.

```powershell
# Core Python test suite (unit, schema contract, engine, consumer, policy-guard tests)
python -m unittest discover -s tests -v

# Release registry validation — integrity + schema contract (must exit 0)
python platform/release-engine/release_engine/__main__.py validate --schema

# Registry drift gate — compare a previous snapshot against the committed registry (exit 2 on drift)
python platform/release-engine/release_engine/__main__.py diff <previous-snapshot.json> --fail-on-drift

# Vault mirror verification against published reality (network; --write persists statuses)
python platform/release-engine/release_engine/__main__.py verify --write

# Apply a recommended-release policy decision (provenance-gated, Execution Contract clause 9)
python platform/release-engine/release_engine/__main__.py apply-policy --decision <decision.json>

# Byte-compilation of all Python sources
python -m compileall -q scripts platform tests

# Website test suite
npm test --prefix website

# Desktop Manager test suite
npm test --prefix apps/manager

# Documentation link validator
python scripts/check_doc_links.py

# Security scan (credential/token detection)
python scripts/security_scan.py

# Distribution metadata validator
python scripts/validate_distribution.py

# Analytics privacy validator (Zero-PII)
python scripts/validate_analytics.py

# Clean-room end-to-end gate (20 checks)
python scripts/e2e_clean_room.py
```

### Quality-gate status

| Reality Dimension | Governance Status | Empirical Verification Evidence |
|---|---|---|
| **Repository Qualification** | **PASS (VERIFIED)** | The full Python test suite plus Website and Manager suites; 20-check clean-room E2E gate (`scripts/e2e_clean_room.py`). 0 broken links, 0 secrets, 0 package identity drift. |
| **Registry Reality Gate** | **PASS (VERIFIED)** | `validate` exits 0: 6 releases, 9 vault entries; schema contract tests green; registry-only consumer proof green. |
| **Build Reality Gate** | **PASS (VERIFIED)** | Build pipelines (`build.sh`, `build_local.py`) verified. Unpacked distribution and CPIO ramdisk structures verified. |
| **Runtime Reality Gate (Host)** | **PASS (VERIFIED)** | Verified on Windows host: active AppX registration (`Status: Ok`, `Version: 2407.40000.4.0`), `userdata.2.vhdx` (3.8 GB), and live `logcat` execution. |
| **Target Environment Gate** | **MANAGED** | Live Google Play Integrity attestation and physical locked VHDX file copy are actively observed in field validation. |

### Security & privacy posture

* **Microsoft Root Certificate Trust**: Network interactions with Microsoft's Windows Update Delivery Network (FE3) are secured via a bundled Microsoft Root CA 2011 / Intermediate CA 2.1 certificate bundle, eliminating OS certificate store tampering.
* **Zero-PII Telemetry**: Public telemetry aggregated under [services/analytics/](services/analytics/) collects zero personally identifiable information (0 IP addresses, 0 device IDs, 0 usernames). Validated by [scripts/validate_analytics.py](scripts/validate_analytics.py).
* **Automated Security Scans**: Every commit is audited by [scripts/security_scan.py](scripts/security_scan.py) to prevent accidental inclusion of personal access tokens, credentials, or private machine paths.

---

## 11. Troubleshooting

### Common Error Codes & Rapid Fixes

* **`0x80370102` (Virtual Machine Platform Not Enabled)**: Run in Administrator PowerShell: `dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart` and verify Intel VT-x/AMD-V in BIOS.
* **`0x80070005` (Access Denied / Developer Mode Disabled)**: Enable Developer Mode in Windows: `Settings > System > For developers > Developer Mode (On)`.
* **`0x80073CF9` (AppX Installation Failed)**: Ensure destination directory is on an NTFS drive and that the Windows AppX Deployment Service (`AppXSvc`) is running.

### Diagnostic Commands

Run these elevated PowerShell commands to resolve common environmental blocks:

```powershell
# 1. Re-enable Hyper-V & Virtual Machine Platform
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:HypervisorPlatform /all /norestart

# 2. Enable Windows Developer Mode via Registry
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" /t REG_DWORD /f /v "AllowDevelopmentWithoutDevLicense" /d "1"

# 3. Connect ADB to WSA (Port 58526) — enable USB Debugging in WSA Advanced Settings first
adb connect 127.0.0.1:58526
adb devices
```

### Guided diagnostics

* **Interactive Wizard**: [wsabuilds-website.pages.dev/troubleshoot/wizard](https://wsabuilds-website.pages.dev/troubleshoot/wizard) — step-by-step decision tree with copyable PowerShell commands.
* **Fix Guides**: Per-issue walkthroughs live under [docs/archive/](docs/archive/) — pre-install errors (`Fix Error 0x80073CF9.md` and siblings), post-install issues (`FixInternet.md`, `Google Play Issues.md`, and more).
* **Error-code reference**: [docs/troubleshooting/error-codes.md](docs/troubleshooting/error-codes.md) and the portal mirror at `website/src/content/docs/troubleshooting/`.

---

## 12. Contributing

We welcome community contributions, bug reports, and application compatibility records!

* **Issue Templates**: Structured forms for bug reports, feature suggestions, and compatibility submissions are available under [.github/ISSUE_TEMPLATE/](.github/ISSUE_TEMPLATE/).
* **Pull Request Guidelines**: Review the contribution checklist in [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md). All PRs must pass `build.yml` with 0 lint, link, or test failures.
* **Moderation Policies**: See [docs/community/compatibility-moderation.md](docs/community/compatibility-moderation.md) and [docs/community/discussions-governance.md](docs/community/discussions-governance.md).

### Application Compatibility Hub

Emberbird maintains a community-curated database of Android application compatibility records under [compatibility/data/](compatibility/data/):

| Application Name | Category | Standard Edition (Magisk) | Banking Edition (Vanilla) | Notes & Requirements |
|---|---|---|---|---|
| **YONO SBI** | Banking & UPI | Workaround Required | **Supported (Native)** | Magisk requires Shamiko and DenyList; Banking Edition runs natively. |
| **PhonePe** | Banking & Payments | Workaround Required | **Supported (Native)** | Requires Developer Options / USB Debugging disabled in WSA Settings. |
| **Paytm** | Payments & Financial | **Supported** | **Supported** | Compatible out of the box. |
| **WhatsApp** | Messaging & Social | **Supported** | **Supported** | Requires manual verification code entry (no direct telephony SIM in WSA). |
| **Google Authenticator** | Security & 2FA | **Supported** | **Supported** | Verified on host container with active cloud backup sync. |
| **Microsoft Authenticator** | Security & Enterprise | **Supported** | **Supported** | Fully compatible with Azure AD and personal accounts. |

Submit new records by adding JSON files to [compatibility/data/](compatibility/data/); CI schema checkers validate every submission automatically. Detailed report specifications and moderation rules: [compatibility/README.md](compatibility/README.md). Live portal: [wsabuilds-website.pages.dev/compatibility](https://wsabuilds-website.pages.dev/compatibility).

---

## 13. License

* **Build Scripts, Code & Tooling**: Licensed under the [GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)](LICENSE).
* **Documentation, Guides & Media**: Licensed under [Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC-BY-NC-ND-4.0)](LICENSE-CC-BY-NC-ND).
* **Third-party components**: Magisk (GPL-3.0), OpenGApps/MindTheGapps lineage (Apache-2.0), and Microsoft's WSA binaries (proprietary, redistributed as published) — full obligations and provenance in [docs/LICENSE_AUDIT.md](docs/LICENSE_AUDIT.md) and [docs/ATTRIBUTION.md](docs/ATTRIBUTION.md).
* **Trademarks**: **Windows Subsystem for Android™**, Windows 11, and Windows 10 are trademarks of Microsoft Corporation. Android™ and Google Play are trademarks of Google LLC. This open-source project is independently developed and is not affiliated with, endorsed by, or sponsored by Microsoft Corporation or Google LLC.

---

## 14. Release Workflow

### Pipeline

1. **Build** (`build.yml`): constructs both editions on every qualifying push; runs the Python test suite and byte-compilation.
2. **Release** (`release.yml`): packages both editions, generates per-edition validation reports (identity, integrity, Magisk, GApps) and `release-metadata.json` with per-package checksums, and publishes the release with `checksums.txt`.
3. **Manager release** (`winget-release.yml`): builds and signs the desktop Manager (Azure Trusted Signing guard + Authenticode validation), publishes `v*` releases with `make_latest: false` so the subsystem release keeps `/releases/latest`.
4. **Validation** (`validation.yml`, `docs-validation.yml`, `compatibility-validation.yml`, `security.yml`, `runtime-compatibility.yml`): continuous gates for tests, docs links, compatibility schema, secrets, and runtime checks.
5. **Registry regeneration** (`scripts/build_registry.py`): rebuilds `data/releases/releases.json` from published reality; the registry, not the workflow, is what consumers read.

### Governance

All releases are governed by transparent reality gates under the platform's Execution Contract (`TODO.md`, Part I) and the frozen release contract (`data/contracts/release-contract.md`):

* **Registry Independence** — consumers derive release intelligence exclusively from `data/releases/releases.json`.
* **Published Artifacts Are Truth** — no hash is published that was not computed from the published bytes; reality overrides documentation.
* **Builder Independence** — the registry records *what* was published, never *which script* built it; Builder V1 is not retired until Builder V2 parity is proven.
* **Deprecation, not deletion** — superseded releases stay queryable via explicit `superseded_by` chains.

Workflow inventory and tag triggers: [.github/WORKFLOWS.md](.github/WORKFLOWS.md).
