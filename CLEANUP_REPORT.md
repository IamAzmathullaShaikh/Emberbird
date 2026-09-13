# WSABuilds Static Analysis & Repository Cleanup Report

**Date:** September 13, 2026  
**Auditor:** Principal CI/CD & Reliability Engineering Team  
**Scope:** Repository-wide static analysis and systematic pruning of dead, stale, stub, and duplicate code, scripts, binaries, and documentation.  
**Total Files Removed:** 776 files across 4 cleanup phases.

---

## Executive Summary

Over successive upstream iterations, the repository accumulated over 700 obsolete binaries, unreferenced helper utilities, duplicate documentation pages from upstream forks, and dead update checkers. This cleanup report documents the forensic static analysis and subsequent pruning of all components that are no longer part of the active WSABuilds build, validation, or release pipeline.

---

## 1. Static Analysis Methodology

Every directory and file was analyzed using three validation criteria:
1. **Direct Inbound References:** Does any active GitHub Actions workflow (`.github/workflows/*.yml`), build script (`MagiskOnWSA/scripts/*`, `build_local.py`), or test file (`tests/*`) call, import, or source the file?
2. **Documentation Integrity:** Does any active Markdown document in `README.md` or `Documentation/` link to the file via relative or absolute URL?
3. **Execution Verification:** Does the file perform an operation required by the locked production target (Windows 11 / 10 x64, Retail WSA, Magisk Stable, OpenGApps Pico)?

Files failing all three criteria were classified as **DEAD**, **STUB**, or **STALE** and removed.

---

## 2. Inventory of Removed Components

### 2.1 Legacy Build System Tree (`MagiskOnWSAOld/`)

* **File:** `MagiskOnWSAOld/` (703 files including subdirectories `DLL/`, `arm64/`, `bin/`, `cacerts/`, `installer/`, `libhoudini/`, `linker/`, `scripts/`, `x64/`, `xml/`)
* **Referenced By:** None. (Previously referenced in dormant steps in `build.yml` and `release.yml`, cleaned up in commit `2d56c87`).
* **Last Usage Evidence:** Legacy snapshot of upstream `LSPosed/MagiskOnWSA` prior to the modular refactoring into `MagiskOnWSA/`. Contains old binaries (`makepri.exe`, `fuse.erofs`, `mkfs.erofs`), old DLLs, and duplicate build scripts targeting obsolete MindTheGapps and KernelSU.
* **Removal Reason:** Complete technical debt. Zero dependencies from active build scripts. Retaining 700+ stale files bloated git clones and caused CI linting overhead.
* **Action:** Permanently deleted in commit `7103cfa`.

---

### 2.2 Obsolete & Stub Update Checkers (`MagiskOnWSA/Update Check/`)

#### 1. `MTGUpdateCheck.py`
* **File:** `MagiskOnWSA/Update Check/MTGUpdateCheck.py`
* **Referenced By:** None.
* **Last Usage Evidence:** Queried `YT-Advanced/MindTheGappsBuilder` for MindTheGapps version releases.
* **Removal Reason:** MindTheGapps is obsolete and no longer built or supported by WSABuilds.
* **Action:** Permanently deleted in commit `7103cfa`.

#### 2. `MagiskCanaryUpdateCheck.py`
* **File:** `MagiskOnWSA/Update Check/MagiskCanaryUpdateCheck.py`
* **Referenced By:** None.
* **Last Usage Evidence:** Checked Magisk Canary releases for Canary builds.
* **Removal Reason:** WSABuilds builds only Magisk Stable (`MagiskStableUpdateCheck.py`). Canary builds are not maintained or released.
* **Action:** Permanently deleted in commit `7103cfa`.

#### 3. `WSAInsiderUpdateCheck.py`
* **File:** `MagiskOnWSA/Update Check/WSAInsiderUpdateCheck.py`
* **Referenced By:** None.
* **Last Usage Evidence:** Queried Microsoft FE3 Delivery for Windows Insider WSA builds.
* **Removal Reason:** WSABuilds releases exclusively target the Retail channel (`WSARetailUpdateCheck.py`).
* **Action:** Permanently deleted in commit `7103cfa`.

#### 4. `update-downloadvar.py`
* **File:** `MagiskOnWSA/Update Check/update-downloadvar.py`
* **Referenced By:** None.
* **Last Usage Evidence:** Attempted to parse an HTML table in `README.md` with headers `['Download Variant', 'Image', 'Image']`.
* **Removal Reason:** Broken / unreferenced stub. The target table does not exist in `README.md` and the script exited with code 1 if ever called.
* **Action:** Permanently deleted in commit `7103cfa`.

#### 5. `windows10patch.ps1`
* **File:** `MagiskOnWSA/Update Check/windows10patch.ps1`
* **Referenced By:** None.
* **Last Usage Evidence:** Standalone PowerShell script attempting to patch `AppxManifest.xml` and download DLLs from `MustardChef/WSAPatch`.
* **Removal Reason:** Misplaced, unreferenced standalone script located inside the `Update Check` folder. Not called by any workflow or installer.
* **Action:** Permanently deleted in commit `7103cfa`.

---

### 2.3 Obsolete Build & Debug Scripts (`MagiskOnWSA/scripts/`)

#### 1. `WSAUpdateChecker.py`
* **File:** `MagiskOnWSA/scripts/WSAUpdateChecker.py`
* **Referenced By:** None.
* **Last Usage Evidence:** Monolithic update checker hardcoded to Windows Insider Fast (`release_type = "WIF"`) and MindTheGapps.
* **Removal Reason:** Obsolete legacy script superseded by modular scripts in `MagiskOnWSA/Update Check/`.
* **Action:** Permanently deleted in commit `7103cfa`.

#### 2. `magisk_debug.sh`
* **File:** `MagiskOnWSA/scripts/magisk_debug.sh`
* **Referenced By:** None.
* **Last Usage Evidence:** Standalone debugging script from upstream LSPosed.
* **Removal Reason:** Unreferenced by `build.sh` or CI workflows.
* **Action:** Permanently deleted in commit `7103cfa`.

#### 3. `generateKernelSULink.py`
* **File:** `MagiskOnWSA/scripts/generateKernelSULink.py`
* **Referenced By:** None.
* **Last Usage Evidence:** Downloaded KernelSU releases.
* **Removal Reason:** KernelSU is not built or supported.
* **Action:** Permanently deleted in commit `c073ff9`.

---

### 2.4 Stale & Duplicate Documentation Trees

#### 1. `MagiskOnWSA/docs/` (35 files)
* **File:** `MagiskOnWSA/docs/` (including `Fixes/`, `Guides/`, `Custom-GApps.md`, `README.md`, `index.html`)
* **Referenced By:** None.
* **Last Usage Evidence:** Legacy documentation folder from upstream `LSPosed/MagiskOnWSALocal`. Included a 7-line stub `index.html` referencing non-existent `./Issues.html`, and `README.md` instructing users to clone `LSPosed/MagiskOnWSALocal` and choose MindTheGapps.
* **Removal Reason:** Confusing duplicate documentation tree. The authoritative documentation for WSABuilds resides in `Documentation/` and repository root.
* **Action:** Permanently deleted in commit `a4c2303`.

#### 2. `Documentation/Usage Guides/Post-Installation Guides/` (29 files)
* **File:** `Documentation/Usage Guides/Post-Installation Guides/` (including subdirectories `Magisk/`, `No Root/`, and individual files `MagiskDelta.md`, `MindTheGapps.md`, etc.)
* **Referenced By:** None.
* **Last Usage Evidence:** Post-installation splash guides for combinations like "MindTheGapps and Removed AMZ", "Magisk Delta", and "No Gapps".
* **Removal Reason:** Completely unreferenced across the entire repository. Stated that MindTheGapps and Magisk Delta were installed, conflicting with the actual build configuration (OpenGApps Pico + Magisk Stable).
* **Action:** Permanently deleted in commit `a4c2303`.

---

## 3. Post-Cleanup Verification

Following the pruning of all stale components:
1. **Broken Link Audit:** `python scripts/check_doc_links.py` scanned all 57 remaining Markdown files:
   ```
   [*] Audited 57 Markdown files.
   [+] All local Markdown links verified successfully! No broken links found.
   ```
2. **Python Syntax Compilation:** `python -m compileall -q scripts config tests MagiskOnWSA/scripts "MagiskOnWSA/Update Check" "WSABuilds Utilities/Update Script" "WSABuilds Utilities/Uninstall Script"` exited with code 0 (clean compilation across all active Python trees).
3. **Unit Tests:** `python -m unittest discover -s tests -v` executed 24/24 tests with 100% pass rate.
4. **Security Audit:** `python scripts/security_scan.py` reported zero detected credentials, tokens, or machine paths.
5. **Workflows:** All 6 GitHub Actions workflows (`build.yml`, `release.yml`, `validation.yml`, `update.yml`, `docs.yml`, `security.yml`) passed YAML syntax and schema checks.
