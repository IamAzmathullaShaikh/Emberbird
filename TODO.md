# WSABuilds — Master Engineering Roadmap & Alignment Plan

**Active Governance**: WSABuilds Master Governance Framework v5.1  
**Status Tracking**: `[x]` = Implemented & Verified | `[ ]` = Pending Execution  
**Quality Gates**: Build Reality Gate | Runtime Reality Gate | Renderer Separation Rule  

---

## 1. Completed Baseline & Foundation Milestones

- [x] **Initrd CPIO Trampoline & Magisk Dynamic Linker**: Re-engineered SVR4 CPIO injection in `build.sh` and `build_local.py` (`lspinit`, `init-ld.xz`, `.backup`, `stub.xz`).
- [x] **Zero-Click ADB Root Authorization**: Host public key injection and Magisk policy pre-seeding for ADB shell UID 0.
- [x] **Tier 1 Multi-Configuration Engine**: Standard Edition (Magisk + Pico) and Banking Edition (Vanilla unrooted ramdisk + Pico).
- [x] **WSABuilds Manager Dual Packaging**: Tauri v2 + React 18 packaging for portable ZIP and NSIS setup EXE with SHA-256 sidecars.
- [x] **Desktop Client Code Signing Pipeline**: Azure Trusted Signing guard and Authenticode PE header validation in `winget-release.yml`.
- [x] **Offline Automated Test Suites**: 81/81 automated tests passing (44 Python in `tests/`, 22 Website in `website/`, 15 Manager in `apps/manager/`).
- [x] **README UX Parity & Subsystem Architecture**: 17-section documentation landing page; eliminated `.github/README.md` collision via `WORKFLOWS.md`.

---

## 2. Phase 1: CI/CD Pipeline & GitHub Releases Reality Alignment

Align CI/CD workflows and GitHub Releases publication so artifacts, namespaces, and validation reports reflect actual repository builds.

- [x] **Task 1.1: Prevent Manager "Latest Release" Hijacking in `winget-release.yml`**
  - **Problem**: When `winget-release.yml` publishes a Manager release (`v*`), GitHub designates it as the repository's "Latest Release", displacing the WSA subsystem release from `/releases/latest`.
  - **Action**: Add `make_latest: false` to `softprops/action-gh-release` in `winget-release.yml` so desktop manager releases do not hijack the repository's primary release endpoint.
  - **Files**: `.github/workflows/winget-release.yml`
  - **Gate**: Build Reality Gate (CI workflow lint and dry-run).

- [x] **Task 1.2: Segregate Validation Reports in `release.yml`**
  - **Problem**: The `validate-and-publish` job loops over `MagiskOnWSA/output/WSA_*/` and outputs to static filenames (`magisk-validation-report.json`, `package-identity-report.json`, etc.), causing the second matrix edition to overwrite the first.
  - **Action**: Parameterize report filenames with edition key (`magisk-validation-report-standard.json`, `magisk-validation-report-vanilla.json`, etc.) and update the release upload pattern.
  - **Files**: `.github/workflows/release.yml`
  - **Gate**: Build Reality Gate (Syntax and workflow execution validation).

- [x] **Task 1.3: Multi-Package Metadata Aggregation in `release.yml`**
  - **Problem**: `PRIMARY_PKG=$(find MagiskOnWSA/output -maxdepth 1 -type d -name "WSA_*" | head -n 1)` only documents a single package in `release-metadata.json`.
  - **Action**: Update `scripts/generate_release_metadata.py` to index all discovered release packages in `MagiskOnWSA/output` and include dual checksum entries in `release-metadata.json`.
  - **Files**: `scripts/generate_release_metadata.py`, `.github/workflows/release.yml`
  - **Gate**: Build Reality Gate & Unit Test Suite (`test_identity_and_integrity.py`).

---

## 3. Phase 2: Website Downloads Portal Hardening (`website/`)

Fix API release resolution, package table filtering, and direct binary download URLs on the official web portal.

- [x] **Task 2.1: Targeted WSA Release Resolution in `release-service.ts`**
  - **Problem**: `release-service.ts` queries `/releases/latest`, returning Manager `v0.2.2` instead of the WSA subsystem release, which leaves zero Android packages visible on `/downloads`.
  - **Action**: Update `GitHubReleaseProvider.getLatestRelease()` to fetch the releases list (`/repos/{repo}/releases?per_page=20`) and discover the latest release matching tag prefix `wsa-v` or `Windows_`.
  - **Files**: `website/src/lib/release-service.ts`
  - **Gate**: Website Test Suite (`npm test` in `website/`).

- [x] **Task 2.2: Package Filtering & Root Flavor Recognition in `parser.ts`**
  - **Problem**: `detectRootFlavor('WSA_2407.40000.4.0_x64.7z')` returns `'unknown'` because the filename lacks the word `magisk`, causing the row to disappear when filtering by Standard Edition. In addition, metadata `.json` and checksum `.txt` files appear as download rows.
  - **Action**: Update `detectRootFlavor` to treat `WSA_*_x64.7z` as `Magisk` when `vanilla` is absent, and update `release-service.ts` asset filtering to exclude `.json` and `.txt` files from the main packages table.
  - **Files**: `website/src/lib/parser.ts`, `website/src/lib/release-service.ts`
  - **Gate**: Website Test Suite (`npm test` in `website/`).

- [x] **Task 2.3: Direct Download URLs for Desktop Manager in `downloads.astro`**
  - **Problem**: The "Direct Installer (.exe)" and "Portable (.zip)" buttons link to the generic release tag page (`/tag/v0.2.2`) rather than directly downloading the binary assets.
  - **Action**: Construct direct asset download URLs pointing to `WSABuildsManager-Setup-{version}-x64.exe` and `WSABuildsManager-Portable-{version}-x64.zip`.
  - **Files**: `website/src/pages/downloads.astro`
  - **Gate**: Website Typecheck & Build (`npm run build` in `website/`).

---

## 4. Phase 3: Release Tag Harmonization & Repository Badges

Harmonize git tags, versions, and public badges with actual build output reality.

- [x] **Task 3.1: Reconcile Subsystem Baseline & Release Tag in `version.json`**
  - **Problem**: `deployment/version.json` defines `subsystem_baseline.wsa_version: "2311.40000.5.0"`, while the actual downloaded retail package is `2407.40000.4.0`.
  - **Action**: Update `subsystem_baseline.wsa_version` to `"2407.40000.4.0"` and record the target canonical release tag.
  - **Files**: `deployment/version.json`
  - **Gate**: Distribution Validator (`python scripts/validate_distribution.py`).

- [x] **Task 3.2: Correct Status Badges in `README.md`**
  - **Problem**: The top badge displays `WSA-2311.40000.5.0` and only one CI badge (`build.yml`) is shown.
  - **Action**: Update the version badge to `WSA-2407.40000.4.0` and add pipeline status badges for `release.yml` and `winget-release.yml`.
  - **Files**: `README.md`
  - **Gate**: Markdown Link Validator (`python scripts/check_doc_links.py`).

- [ ] **Task 3.3: Canonical Dual-Edition Release Tagging** (STATUS: BLOCKED — OWNER ACTION; requires an authenticated GitHub token to publish the `wsa-v2407.40000.4.0` release; after publication `version.json release_tag`, README download links and website fallback must be re-pointed in the same change to preserve user journeys)
  - **Problem**: The current dual-edition release is tagged under `wsa-v2311.40000.5.0`, creating semantic confusion with the enclosed `2407.40000.4.0` packages.
  - **Action**: Publish or tag a release matching the actual WSA version (`Windows_11_2407.40000.4.0` or `wsa-v2407.40000.4.0`) containing both verified `.7z` packages, and set `make_latest: true`.
  - **Files**: Release assets on GitHub
  - **Gate**: Runtime Reality Gate (Live asset URL verification).

---

## 5. Phase 4: Architecture Transparency & ARM64 Roadmap

Ensure hardware architecture claims in documentation match compilation and distribution capabilities.

- [x] **Task 4.1: Accurate ARM64 Documentation Transparency**
  - **Problem**: `README.md` badges and tables advertise ARM64 builds, but zero ARM64 binaries exist in GitHub release assets.
  - **Action**: Clarify in `README.md` Section 3 that ARM64 packages are not currently pre-built on GitHub Releases, and document the manual build command (`bash MagiskOnWSA/scripts/build.sh --arch arm64`) for users with Snapdragon devices.
  - **Files**: `README.md`, `docs/getting-started/quick-start.md`
  - **Gate**: Markdown Link Validator (`python scripts/check_doc_links.py`).

- [ ] **Task 4.2: ARM64 CI Cross-Compilation Investigation**
  - **Problem**: Building ARM64 packages requires downloading ARM64 WSA MSIX packs and packaging an ARM64 initrd ramdisk with compatible binaries.
  - **Action**: Research and prototype ARM64 workflow jobs in `release.yml` using `aarch64` sysroots or Ubuntu ARM emulation.
  - **Files**: `.github/workflows/release.yml`, `MagiskOnWSA/scripts/build.sh`
  - **Gate**: Build Reality Gate.

---

## 6. Phase 5: Post-Release Operations & Field Verification

Maintain continuous field verification and community submission workflows.

- [ ] **Task 5.1: Live Target Environment Verification Program**
  - **Goal**: Convert outstanding `REQUIRES TARGET ENVIRONMENT VERIFICATION` items into `VERIFIED` across Windows 10 (Build 19045) and Windows 11 (Build 22631+).
  - **Focus**: Host cold-restore rollback verification, Play Integrity basic/device attestation checks, and Winget installation pipeline validation.
  - **Files**: `docs/WINDOWS_VALIDATION_LAB.md`, `docs/UPGRADE_VALIDATION.md`
  - **Gate**: Runtime Reality Gate.

- [x] **Task 5.2: Automated Community Compatibility PR Ingestion**
  - **Goal**: Validate inbound community submissions against `compatibility/schema.json` and sync verified records to the web portal.
  - **Files**: `.github/workflows/compatibility-validation.yml`, `compatibility/data/`
  - **Gate**: Compatibility Schema Tests (`test_compatibility_schema.py`).
