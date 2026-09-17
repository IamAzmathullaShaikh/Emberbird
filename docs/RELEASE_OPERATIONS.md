# Emberbird Release Operations Handbook (Epic RO1)

## Overview
This handbook provides the authoritative, zero-tribal-knowledge operational procedure for release stewards to audit, validate, package, and publish Emberbird releases under the **Real-World Release Operations** programme.

All operations derive from the immutable Truth Hierarchy:
```
Reality → Registry → Contracts → Consumers
```

---

## 1. Release Pipeline Audit (Task RO1.1)

Before initiating a release cycle, run the pipeline audit to verify environment prerequisites and toolchain readiness across all 6 release pathways:

```powershell
python scripts/audit_release_pipeline.py
```

### Inspected Pathways & Expected Statuses:
- **Standard Edition (x64 Magisk + GApps)**: `BUILDABLE` (or `PARTIAL` if stock MSIX needs to be downloaded).
- **Banking Edition (x64 Vanilla + GApps)**: `BUILDABLE` (or `PARTIAL` if stock MSIX needs to be downloaded).
- **ARM64 Edition (Snapdragon X Elite / Copilot+ PC)**: `PARTIAL` (BYOB pipeline — requires user ARM64 MSIXBundle).
- **Emberbird Manager Desktop Application**: `BUILDABLE` (Vite / React / Tauri toolchain).
- **Emberbird Web Portal & Documentation**: `BUILDABLE` (Astro static production compilation).
- **Multi-Target Package Manifests**: `BUILDABLE` (Winget, Scoop, Chocolatey, Portable).

To export machine-readable audit status:
```powershell
python scripts/audit_release_pipeline.py --json --output dist/pipeline-audit.json
```

---

## 2. Automated Release Validation Report (Task RO1.2)

Every release candidate is evaluated against 5 cryptographic and architectural readiness gates:

```powershell
python scripts/generate_release_validation_report.py --release-id <release-id>
```

### Verification Gates:
1. **Gate 1 (Checksum Completeness)**: Validates 64-character lowercase SHA-256 hashes for all assets.
2. **Gate 2 (Package Identity)**: Verifies publisher parameters (`MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe`) and architecture tokens.
3. **Gate 3 (Root Framework Integrity)**: Confirms official Magisk Stable v30.6+ integration for Standard Edition, or clean unrooted ramdisk for Banking Edition.
4. **Gate 4 (Google Services Integration)**: Verifies OpenGApps Pico runtime registration.
5. **Gate 5 (Distribution Synchronization)**: Checks tag and version alignment with `deployment/version.json`.

To export validation reports:
```powershell
python scripts/generate_release_validation_report.py --release-id wsa-2311-standard --markdown docs/RELEASE_VALIDATION_REPORT.md --json --output dist/release-validation.json
```

---

## 3. Automated Release Notes Generation (Task RO1.3)

Generate standard, 4-section release notes directly from registry truth without manual editing:

```powershell
python scripts/generate_release_notes.py --release-id <release-id>
```

### Generated Sections:
1. **User Notes**: Clear, non-technical overview, download links, and edition selection guide.
2. **Technical Changes**: Subsystem baseline, Android version, Magisk version, OpenGApps tag, signature stripping details.
3. **Compatibility Notes**: Play Integrity status, tested apps list, supported Windows builds (Windows 10/11 x64 and arm64).
4. **Upgrade Notes**: Pre-upgrade cold VHDX backup instructions, folder merge steps, data preservation, and rollback recovery.

To write release notes to disk:
```powershell
python scripts/generate_release_notes.py --release-id wsa-2311-standard --output dist/RELEASE_NOTES.md
```

---

## 4. Multi-Target Distribution Packaging

Generate package distribution manifests for package managers:

```powershell
python scripts/generate_package_manifests.py --target all --write
```

Generates:
- **Winget**: `dist/manifests/winget/<ver>/Emberbird.Manager.yaml` (Version, Installer, Locale manifests).
- **Chocolatey**: `dist/manifests/emberbird-manager.nuspec`.
- **Scoop**: `dist/manifests/emberbird-manager.json`.
- **Portable**: `dist/manifests/emberbird-manager-portable.json`.

---

## 5. Production Release Execution Pipeline (Epic PR1)

The complete end-to-end production release workflow moves release artifacts across the invariant hierarchy:
```
Reality → Registry → Build → Validate → Publish → Distribute → Deploy → Verify
```

### Stage 1: Release Candidate Staging (Task PR1.1)
Build and stage unpacked candidate directories for specified target editions:
```powershell
python scripts/build_release_candidates.py --target all --output-dir output
```
- Targets: `standard` (x64 Magisk), `banking` (x64 Vanilla), `arm64` (Snapdragon X Elite), `manager` (Desktop App).
- Produces: `output/release-candidate-manifest.json` recording build metadata, file counts, and sizes.

### Stage 2: Release Packager & Checksum Engine (Task PR1.2)
Compress staged candidates into `.7z` / `.zip` archives, compute cryptographic hashes, and generate checksum suites:
```powershell
python scripts/package_release.py --input-dir output --output-dir dist/release --format 7z
```
- Produces:
  - `dist/release/*.7z` or `*.zip`
  - `dist/release/checksums.sha256`
  - `dist/release/checksums.sha512`
  - `dist/release/checksums.txt`
  - `dist/release/release-metadata.json`
  - `dist/release/RELEASE_VALIDATION_REPORT.md`
  - `dist/release/RELEASE_NOTES.md`

### Stage 3: Release Publication Flow (Task PR1.3)
Validate schema compliance, register the release into authoritative registry truth, and generate distribution descriptors:
```powershell
# Validate and test release publication without committing
python scripts/publish_release.py --dist-dir dist/release --dry-run

# Formally commit release to registry and generate publication descriptors
python scripts/publish_release.py --dist-dir dist/release
```
- Validates the complete release structure against `data/releases/releases.schema.json`.
- Registers published assets, SHA-256 hashes, and verification reports into `data/releases/releases.json`.
- Automatically syncs Manager package manager descriptors in `dist/manifests/`.
- Generates `dist/release/github-release.json`, `publish-github.sh`, and `publish-github.bat`.

---

## 7. Live Release Validation (Epic PR2)

Live Release Validation audits the entire operational release ecosystem across 7 core dimensions to verify that published reality, registry truth, download vectors, package distribution, website visibility, and manager discovery are 100% aligned:

```powershell
# Run full live release validation suite and update reports
python scripts/validate_live_release.py --all --output-dir dist/reports --markdown docs/RELEASE_HEALTH_REPORT.md

# Strict gate check (returns exit code 1 on any failure)
python scripts/validate_live_release.py --check
```

### Audited Dimensions:
1. **PR2.1 (Release Asset Verification)**: Verifies valid filenames, 64-hex lowercase SHA-256 (zero placeholders), non-zero byte sizes, and vault correlation.
2. **PR2.2 (Download Validation)**: Validates GitHub release download URLs, Downloads Hub (`downloads.astro`), and ARM64 experience guidance (`arm64.astro`).
3. **PR2.3 (Distribution Validation)**: Verifies active Winget manifests (`manifests/e/Emberbird/Manager/`), Scoop, Chocolatey, and Portable descriptors against registry hashes.
4. **PR2.4 (Registry Consistency)**: Verifies the invariant chain `Asset → Registry Entry → Vault Entry` with zero orphan assets or orphan vault entries.
5. **PR2.5 (Release Health Scoring)**: Computes 4-pillar health scoring (`Registry Health`, `Asset Integrity`, `Download Health`, `Distribution Health`) and generates `docs/RELEASE_HEALTH_REPORT.md`.
6. **PR2.6 (Website Release Visibility)**: Verifies Homepage, Downloads Hub, Registry Explorer, and Observatory surface live registry truth.
7. **PR2.7 (Manager Release Discovery)**: Verifies desktop manager discovers releases strictly through bundled `releases.json` without runtime network calls.

---

## 8. Continuous Release Operations Pipeline (Epic PR3)

The Continuous Release Pipeline orchestrates the complete shipping lifecycle into a single push-button operation without manual metadata authoring:

```powershell
# Run continuous release pipeline in safe pre-flight mode (PR3.1-PR3.4)
python scripts/release_pipeline.py --target manager --dry-run

# Formally execute continuous shipping for standard WSA release
python scripts/release_pipeline.py --target standard

# Run mandatory pre-commit validation battery for the main branch (PR3.5)
python scripts/release_pipeline.py --check-only
```

### Seven Continuous Steps:
1. **Step 1 (Candidate Staging)**: Automatically stages package directories with valid `AppxManifest.xml`, `Install.ps1`, `Run.bat`, and `initrd.img`.
2. **Step 2 (Packaging & Checksums)**: Compresses candidates into release archives and computes standard SHA-256 and SHA-512 checksum suites.
3. **Step 3 (GitHub Operations & Registry Sync)**: Registers release into `data/releases/releases.json`, validates against Draft-07 schema, updates vault entries, and creates GitHub payloads (`github-release.json`, `publish-github.bat`, `publish-github.sh`).
4. **Step 4 (Distribution Operations)**: Automatically authors Winget (`manifests/`), Scoop (`.json`), Chocolatey (`.nuspec`), and Portable manifests.
5. **Step 5 (Website Deployment & Surface Verification)**: Compiles static Astro website and verifies Homepage, Downloads Hub, Registry Explorer, Observatory, ARM64 Hub, and Doctor Centre.
6. **Step 6 (Manager Release Discovery)**: Confirms that Desktop Manager resolves release truth without runtime GitHub API network calls.
7. **Step 7 (Continuous Health Monitoring)**: Executes 4-pillar release health scoring and outputs `dist/reports/release-health-report.json` and `docs/RELEASE_HEALTH_REPORT.md`.

---

## 9. Release Steward Pre-Flight Checklist

Before announcing any production release, verify:
- [ ] Pipeline audit has 0 `BLOCKED` pathways (`python scripts/audit_release_pipeline.py`).
- [ ] Continuous Release Pipeline completes with 7/7 steps `PASS` (`python scripts/release_pipeline.py --dry-run`).
- [ ] Release candidates staged successfully (`python scripts/build_release_candidates.py`).
- [ ] Release packages compressed and checksummed (`python scripts/package_release.py`).
- [ ] Release publication pre-flight passes with 0 schema violations (`python scripts/publish_release.py --dry-run`).
- [ ] Live Release Validation returns 100.0% PASS (`python scripts/validate_live_release.py --check`).
- [ ] Release validation report returns `overall_readiness: READY` (`python scripts/generate_release_validation_report.py --release-id <id>`).
- [ ] Release notes contain all 4 mandated sections (`python scripts/generate_release_notes.py --release-id <id>`).
- [ ] Distribution manifests match release hashes (`python -m unittest tests/test_distribution_manifests.py`).
- [ ] Python, Manager, and Website test batteries are green.
- [ ] Programme Intelligence remains 10.0 / 10.0 (`python scripts/programme_intelligence.py --check`).
