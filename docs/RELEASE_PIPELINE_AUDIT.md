# Emberbird Release Pipeline Audit Report

**Generated:** `2026-09-17T13:21:12Z` | **Host:** `Windows AMD64`
**Overall Status:** **`PARTIAL`** | **Total Pathways:** 6 (Buildable: 3, Partial: 3, Blocked: 0)

---

| Pathway | Architecture | Status | Primary Tool | Outputs |
| :--- | :--- | :--- | :--- | :--- |
| **Standard Edition (x64 Magisk + GApps)** | `x64` | `PARTIAL` | `python tools/build_local.py --arch x64` | `output/WSA_<ver>_x64/ (AppxManifest.xml, initrd.img, Install.ps1)` |
| **Banking Edition (x64 Vanilla + GApps)** | `x64` | `PARTIAL` | `python tools/build_local.py --arch x64 --root-sol none` | `output/WSA_<ver>_x64_vanilla/ (clean unrooted distribution)` |
| **ARM64 Edition (Snapdragon X Elite / Copilot+ PC)** | `arm64` | `PARTIAL` | `python tools/build_local.py --arch arm64 --wsa-file <arm64.msixbundle>` | `output/WSA_<ver>_arm64/ (native AArch64 unpackaged distribution)` |
| **Emberbird Manager Desktop Application** | `x64` | `BUILDABLE` | `npm --prefix apps/manager run build` | `WSABuildsManager-Setup-<ver>-x64.exe` |
| **Emberbird Web Portal & Documentation** | `any` | `BUILDABLE` | `npm --prefix website run build` | `website/dist/ (static production site)` |
| **Multi-Target Package Manifests (Winget, Scoop, Choco, Portable)** | `x64` | `BUILDABLE` | `python scripts/generate_package_manifests.py --target all --write` | `dist/manifests/winget/<ver>/Emberbird.Manager.yaml (version, installer, locale)` |

## Detailed Pathway Diagnostics

### 1. Standard Edition (x64 Magisk + GApps) [PARTIAL]
- **Pathway ID:** `standard`
- **Target Architecture:** `x64`
- **Primary Command:** `python tools/build_local.py --arch x64`
- **Required Inputs:** WSA MSIX / ZIP archive, Magisk Stable archive, gapps-13.0-x86_64.img
- **Expected Outputs:** output/WSA_<ver>_x64/ (AppxManifest.xml, initrd.img, Install.ps1)
- **Readiness Notes:** Toolchain ready. Requires stock Microsoft WSA MSIXBundle/zip input (--wsa-file or download/).
- **Actionable Remediation:** Provide stock WSA archive via --wsa-file or place in download/.

### 2. Banking Edition (x64 Vanilla + GApps) [PARTIAL]
- **Pathway ID:** `banking`
- **Target Architecture:** `x64`
- **Primary Command:** `python tools/build_local.py --arch x64 --root-sol none`
- **Required Inputs:** WSA MSIX / ZIP archive, gapps-13.0-x86_64.img
- **Expected Outputs:** output/WSA_<ver>_x64_vanilla/ (clean unrooted distribution)
- **Readiness Notes:** Clean ramdisk stripping toolchain ready. Requires stock Microsoft WSA MSIX/zip input.
- **Actionable Remediation:** Provide stock WSA archive via --wsa-file or place in download/.

### 3. ARM64 Edition (Snapdragon X Elite / Copilot+ PC) [PARTIAL]
- **Pathway ID:** `arm64`
- **Target Architecture:** `arm64`
- **Primary Command:** `python tools/build_local.py --arch arm64 --wsa-file <arm64.msixbundle>`
- **Required Inputs:** ARM64 WSA MSIXBundle (BYOB), gapps-13.0-arm64.img, Magisk arm64-v8a
- **Expected Outputs:** output/WSA_<ver>_arm64/ (native AArch64 unpackaged distribution)
- **Readiness Notes:** BYOB Pipeline active. Native ARM64 toolchain and ABI patcher verified; requires user-supplied ARM64 MSIXBundle.
- **Actionable Remediation:** Follow the BYOB guide in website/src/pages/arm64.astro: download ARM64 MSIXBundle and run tools/build_local.py --arch arm64.

### 4. Emberbird Manager Desktop Application [BUILDABLE]
- **Pathway ID:** `manager`
- **Target Architecture:** `x64`
- **Primary Command:** `npm --prefix apps/manager run build`
- **Required Inputs:** Node.js >= 18, Rust / Cargo (for native Tauri compilation)
- **Expected Outputs:** WSABuildsManager-Setup-<ver>-x64.exe, WSABuildsManager-Portable-<ver>-x64.zip
- **Readiness Notes:** Node dependencies installed. Frontend builds via vite; Tauri CLI compiles executable.

### 5. Emberbird Web Portal & Documentation [BUILDABLE]
- **Pathway ID:** `website`
- **Target Architecture:** `any`
- **Primary Command:** `npm --prefix website run build`
- **Required Inputs:** Node.js >= 18, documentation markdown files in docs/
- **Expected Outputs:** website/dist/ (static production site)
- **Readiness Notes:** Astro toolchain and dependencies ready. Static build produces 18 routes with Pagefind indexing.

### 6. Multi-Target Package Manifests (Winget, Scoop, Choco, Portable) [BUILDABLE]
- **Pathway ID:** `distribution`
- **Target Architecture:** `x64`
- **Primary Command:** `python scripts/generate_package_manifests.py --target all --write`
- **Required Inputs:** data/releases/releases.json, deployment/version.json
- **Expected Outputs:** dist/manifests/winget/<ver>/Emberbird.Manager.yaml (version, installer, locale), dist/manifests/emberbird-manager.nuspec, dist/manifests/emberbird-manager.json, dist/manifests/emberbird-manager-portable.json
- **Readiness Notes:** 100% pure Python stdlib generator active. Derives cryptographic hashes directly from releases.json.

---
*Generated automatically by `scripts/audit_release_pipeline.py` adhering to Execution Contract and Registry Truth.*
