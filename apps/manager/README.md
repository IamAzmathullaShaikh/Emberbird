# WSABuilds Manager — Desktop Client

WSABuilds Manager is the native desktop management client for the **Windows Subsystem for Android™ (WSA)** platform on Windows 10 and Windows 11. It provides one-click cold VHDX backups, safe rollback restores, environment health checks, and guided package updates.

---

## 1. Purpose & Core Capabilities

- **Atomic Cold VHDX Backups**: Shuts down WSA, verifies file locks, and streams `userdata.vhdx` to backup storage with streaming SHA-256 integrity checksums.
- **Rollback Safety Snapshots**: Automatically takes a pre-restore snapshot (`.pre_restore.bak`) before overwriting existing storage, ensuring zero data loss on failed restores.
- **Preflight Upgrade Gating**: Asserts Windows Developer Mode, verifies at least 25GB free disk space, and inspects active WSA processes prior to executing package installations.
- **Automated Retention Management**: Prunes historical snapshots based on user-defined retention limits while preserving baseline integrity metadata.

---

## 2. Subsystem Architecture

The application is structured into two cooperating layers:

1. **Frontend Layer (`src/`)**:
   - **Framework**: React 18, TypeScript, Tailwind CSS, Vite.
   - **Views**:
     - `StatusCard.tsx`: Real-time WSA runtime status, package family detection, and hypervisor health.
     - `BackupView.tsx`: One-click cold VHDX backup creation, retention policies, and archive sizing.
     - `RestoreView.tsx`: Candidate selection, pre-restore verification, and rollback initiation.
     - `UpdateView.tsx`: Preflight checks, staged package deployment, and AppX registration.
   - **IPC Bridge (`src/lib/ipc.ts`)**: Type-safe abstraction over Tauri IPC invoke commands with built-in development mocking.

2. **Native Backend Layer (`src-tauri/`)**:
   - **Framework**: Tauri v2, Rust native desktop engine.
   - **Modules**:
     - `backup.rs`: Cold shutdown coordination, Win32 file lock inspection, SHA-256 digest computation.
     - `registry.rs`: Backup registry index, candidate discovery, retention pruning.
     - `restore.rs`: Integrity verification, safety copy preparation, atomic restore execution.
     - `installer.rs`: Developer Mode verification, loose-folder registration via PowerShell `Add-AppxPackage`.
     - `coordinator.rs`: Comprehensive preflight check (25GB disk space, process state, version gating).
     - `detector.rs`: Process inspection (`WsaClient.exe`, `WsaService.exe`) and AppX package query.

---

## 3. Local Development Setup

### Prerequisites
- **Node.js**: Version 20.0 or higher.
- **Rust Toolchain**: Stable release (`rustup install stable`).
- **Build Tools**: Visual Studio 2022 C++ Build Tools with the *Desktop development with C++* workload and Windows 10/11 SDK.
- **Windows Runtime**: Microsoft Edge WebView2 (pre-installed on Windows 11).

### Setup Commands
```powershell
# Navigate to the manager directory
cd apps/manager

# Install frontend dependencies
npm install
```

---

## 4. Development Commands

```powershell
# Run Vite frontend in development mode (browser preview on localhost:1420)
npm run dev

# Launch full native desktop application with hot-reloading Rust backend
npm run tauri dev

# Build production static frontend bundle
npm run build

# Compile release desktop executable (wsabuilds-manager.exe)
npm run tauri build
```

---

## 5. Testing & Quality Commands

```powershell
# Run frontend Node unit test suite (15 unit tests)
npm test

# Run TypeScript typechecker
npm run typecheck

# Inside apps/manager/src-tauri:
cd src-tauri

# Run Rust compile check
cargo check

# Run Rust clippy linter (warnings treated as errors)
cargo clippy -- -D warnings

# Run native Rust unit tests
cargo test --verbose
```

---

## 6. CI/CD Overview

Desktop manager validation and packaging are governed by dedicated GitHub Actions workflows:

- **`.github/workflows/manager-build.yml`**:
  - Runs on `windows-latest`.
  - Executes frontend tests, TypeScript typechecks, `cargo check`, `cargo clippy`, and native Rust unit tests.
- **`.github/workflows/winget-release.yml`**:
  - Triggers on application release tags (`v*`).
  - Compiles release binary, packages `WSABuildsManager-Portable-0.2.0-x64.zip`, generates GNU SHA-256 checksums, and stages Winget manifests.

---

## 7. Common Pitfalls & Error Codes

| Error Code | Trigger Condition | Remediation |
|---|---|---|
| **`WSA-MGR-001`** | Backup attempted while `userdata.vhdx` is locked by running WSA processes | Turn off WSA in WSA Settings, wait 10 seconds for file handle release, and retry. |
| **`WSA-MGR-002`** | `Add-AppxPackage` failed due to missing Developer Mode or insufficient privileges | Enable Developer Mode in Windows Settings (`ms-settings:developers`) and run as Administrator. |
| **`WSA-MGR-003`** | Free disk space < 25GB during upgrade preflight | Free up disk space on the target installation drive before proceeding. |

---

## 8. Version Synchronization Governance

The version of WSABuilds Manager must remain strictly synchronized across all project files:
1. `deployment/version.json` (`manager.version`)
2. `apps/manager/package.json` (`version`)
3. `apps/manager/src-tauri/Cargo.toml` (`package.version`)
4. `apps/manager/src-tauri/tauri.conf.json` (`version`)
5. `manifests/w/WSABuilds/WSABuildsManager/[version]/`

Enforce version consistency before submitting changes by running:
```powershell
python scripts/validate_distribution.py
```
