# Emberbird Learning Path & Role Guides

Welcome to **Project Emberbird**! This guide outlines the most effective learning and execution paths based on your role and objectives.

---

## Path 1: End User (Install & Run Android Apps)

**Objective**: Install a verified, pre-configured Android environment on Windows 11 or Windows 10 in under 10 minutes.

1. **Choose Your Edition**:
   - Review [Supported Build Types](ARCHITECTURE.md#supported-build-types).
   - Pick **Standard Edition** (Magisk root) if you need root, LSPosed, or developer customization.
   - Pick **Banking & Enterprise Edition** (Vanilla) if you need 100% out-of-the-box compatibility with financial apps, UPI, or DRM-protected streaming.
2. **Download & Verify**:
   - Download package from the [Downloads Portal](https://wsabuilds-website.pages.dev/downloads) or [Releases](https://github.com/IamAzmathullaShaikh/Emberbird/releases).
   - Run `Get-FileHash -Algorithm SHA256 .\WSA_*.7z` and verify against `checksums.txt`.
3. **Install Subsystem**:
   - Extract `.7z` archive to a permanent directory (e.g. `C:\WSA`).
   - Right-click `Install.ps1` -> **Run with PowerShell**.
4. **Desktop Management**:
   - Install **Emberbird Manager** (`winget install Emberbird.Manager`) for one-click VHDX backups, snapshot rollbacks, and upgrade pre-flight checks.

---

## Path 2: Android App Tester & QA Specialist

**Objective**: Test Android applications on Windows, verify Play Integrity, and contribute to the community compatibility database.

1. **Configure Debugging**:
   - In WSA Settings -> **Advanced settings** -> Enable **Developer mode**.
   - Connect via ADB: `adb connect 127.0.0.1:58526`.
2. **App Compatibility Verification**:
   - Install the target application via Google Play Store or `adb install <app.apk>`.
   - Test basic launch, login flows, DRM video playback, and push notifications.
3. **Document Compatibility**:
   - Review existing entries in the [Compatibility Hub](https://wsabuilds-website.pages.dev/compatibility).
   - Submit new compatibility records using the [Compatibility Report Form](https://github.com/IamAzmathullaShaikh/Emberbird/issues/new?template=compatibility_report.yml).

---

## Path 3: Core Developer & Contributor

**Objective**: Understand the repository architecture, build custom editions, execute tests, and submit improvements within 30 minutes.

1. **Understand the Architecture**:
   - Read [ARCHITECTURE.md](ARCHITECTURE.md) and [EMBERBIRD_CHARTER.md](EMBERBIRD_CHARTER.md).
   - Key concept: **Registry Independence** — all consumers read `data/releases/releases.json`.
2. **Set Up Local Environment**:
   - Clone: `git clone https://github.com/IamAzmathullaShaikh/Emberbird.git && cd Emberbird`.
   - Run the Python test suite: `python -m unittest discover -s tests`.
3. **Explore Build Pipelines**:
   - Linux/WSL2: `tools/build.sh` (modifies ramdisks, packages MSIX, creates solid 7z archives).
   - Native Windows: `tools/build_local.py` (pure-Python Windows builder).
4. **Run Quality Gates**:
   - Registry validation: `python platform/release-engine/release_engine/__main__.py validate --schema`.
   - Security scan: `python scripts/security_scan.py`.
   - Link check: `python scripts/check_doc_links.py`.
5. **Submit Changes**:
   - Follow [CONTRIBUTING.md](../CONTRIBUTING.md) and use conventional commits.

---

## Path 4: Repository Steward & Release Engineer

**Objective**: Maintain registry integrity, govern releases, monitor drift, and oversee distribution packaging.

1. **Registry Governance**:
   - Review `data/releases/GOVERNANCE.md` and `data/contracts/release-contract.md`.
   - Invariant: **Published Artifacts Are Truth** — releases exist only if published bytes and hashes exist.
2. **Release Engine Tooling**:
   - Rebuilding registry from reality: `python scripts/build_registry.py`.
   - Detecting drift: `python platform/release-engine/release_engine/__main__.py diff previous.json --fail-on-drift`.
   - Verifying mirror availability: `python platform/release-engine/release_engine/__main__.py verify --write`.
3. **Distribution Management**:
   - Version seam: `deployment/version.json`.
   - Winget manifest validation: `python scripts/validate_distribution.py`.
4. **Branch & History Stewardship**:
   - Review [BRANCH_HYGIENE.md](BRANCH_HYGIENE.md) and [HISTORICAL_PRESERVATION.md](HISTORICAL_PRESERVATION.md).
   - Never delete tags, published releases, attribution, or historical manifests (M4/S1).
