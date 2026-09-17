# Project Emberbird — Programme Control Board (G4)

**Platform**: Emberbird  
**Authority**: `docs/METAMORPHOSIS.md` G4 · `docs/EMBERBIRD_CHARTER.md` · `docs/PROGRAMME_INTELLIGENCE.md`  
**Governance**: Tracks Open / Deferred / Rejected / Adopted programme decisions, separate from technical ADRs.

---

## 1. Adopted Programme Decisions (Closed & CI-Ratified)

| Phase / Item | Decision | Ratification / Commit | Primary Benefit |
|---|---|---|---|
| **P0 Foundation** | Establish authoritative release registry (`releases.json`), schema, and release engine. | `3961db1` | Single validated source of truth; zero guessing or scraping. |
| **P1 Population** | CI scheduled drift automation (`registry-drift.yml`), vault verification, policy write path. | `6ae1931` | Registry self-auditing against published GitHub reality. |
| **E1 Inventory** | Git-index identity classification tool (`identity_map.py`) and Brand Policy (`BRAND.md`). | `d5b8256` | 100% transparent audit of all 933+ historical identity occurrences. |
| **E2 Restructure** | Atomic directory restructuring per `PATH_MAP.md` v2 (`tools/`, `utilities/`, `upstream/`). | `51b6810` | Eliminates legacy path collisions; isolates vendored upstreams. |
| **E3A Rebrand** | Living document and website chrome rebrand to Emberbird with keep-token protection. | `e4f21ad` | Consistent user-facing identity without erasing historical lineage. |
| **E3B Web Migration** | Website switches to build-time registry consumer (`RegistryReleaseProvider`); G2/S2 parity. | `a5402c3` | 0 GitHub API calls during website builds; 100% registry-driven. |
| **E3C Manager Migration** | Desktop Manager consumes bundled registry (`registry.ts`); S2 parity proven. | `191c5d9` | Offline-safe release resolution for the desktop client. |
| **E4 Repo Identity** | Canonical repository identity becomes `IamAzmathullaShaikh/Emberbird`. | `9a2a45f` | GitHub API rename executed; backward redirects preserved. |
| **E5 Distribution** | Author new Winget manifests under `Emberbird.Manager` (v0.2.2); freeze historical package. | `0f8a401` | Clean publisher identity; historical manifests untouched. |
| **E6 Experience** | Transform master README into front door; add website attribution footer. | `3a57c6b` | Modern developer experience and transparent ancestry. |
| **E7 Purity Audit** | Enforce purity guards (0 hardcoded releases/hashes, 0 undocumented workflows). | `93a74e6` | Milestone `emberbird-v1.0.0` cut and validated. |
| **Default Branch Switch** | Switch repository default branch from `master` to `main`. | API Probe | Aligns integration branch with modern conventions. |
| **Programme Intelligence System** | Authoritative system operating model, automated drift detection (`programme_intelligence.py`), and project memory. | Current Baseline | Continuous audit across 10 repository dimensions; durability against environment change. |
| **Phase D1 (Project Doctor)** | Stdlib-first host diagnostic & remediation CLI (`platform/doctor/`, `scripts/doctor.py`). | Current Head | Automated host inspection (PRB-01–07), elevated safe self-healing, `--json` IPC output. |
| **Phase A1 (Project Snapdragon)** | Native ARM64 enablement, Bring-Your-Own-Bundle (`--wsa-file`), ABI mapping, and toolchain tests. | Current Head | Tier-1 ARM64 build pipeline for Qualcomm Snapdragon X Elite and Copilot+ PCs. |
| **Phase R1 (Project Genesis)** | Android 14 Treble GSI & Microsoft HAL paravirtualization research; LTS Android 13 baseline ratified. | Current Head | Rigorous technical audit preventing unstable releases; rock-solid LTS stability. |
| **Phase P2 (Manager V2)** | Registry supersession resolution, navigation tabs, and comprehensive Licenses Screen (`LicensesView.tsx`). | Current Head | Transparent legal disclosures and offline registry resolution in desktop client. |
| **Phase P3 (Website on Registry)** | Registry release provider (`RegistryReleaseProvider`) and compatibility hub alignment. | Current Head | Zero-network, schema-validated website release discoverability. |
| **Phase P4 (Compatibility Platform)** | Channel contract validation (`tested_channel`) against `data/contracts/channel-contract.md`. | Current Head | Strict schema validation for community and laboratory compatibility reports. |
| **Phase P5 (Ember Observatory)** | Telemetry-driven policy recommendation engine (`services/analytics/observatory.py`). | Current Head | Provenance-backed, signed recommendation decisions applied to release registry. |
| **Phase P6 (Trusted Signing)** | Azure Trusted Signing & Key Governance Addendum in `docs/LICENSE_AUDIT.md`. | Current Head | HSM FIPS 140-2 Level 3 key isolation and RFC 3161 Authenticode timestamping. |
| **Phase P7 (Distribution Automation)** | Multi-target manifest generator (`generate_package_manifests.py`) and expansion evaluation. | Current Head | Automated Winget, Scoop, and Chocolatey manifest generation from registry vault. |

---

## 2. Deferred Roadmap Items (Locked Future Phases)

Per the Execution Contract, all chartered and roadmap engineering phases (P0–P8, E0–E7, D1, A1, R1) are fully implemented, verified, and closed. Any future work requires a new, separately chartered programme.

---

## 3. Rejected Proposals

| Proposal | Rejection Date | Grounding & Charter Rule |
|---|---|---|
| **KernelSU Integration** | Cycle S1 / E0 | Requires compiling custom Linux kernels outside retail Microsoft WSA. Violates single-maintainer durability and automated update pipeline. |
| **Third-Party App Store Broker** | P0 Charter | Violates Charter Section 1: "Emberbird is NOT an app store or third-party APK broker." |
| **Runtime GitHub Release Discovery** | P0 / E3B | Violates Registry Independence: consumers must never scrape GitHub HTML or APIs to discover releases. |
| **Mutating Historical Releases / Tags** | Metamorphosis Charter | Violates Rule M4: "Release History Is Immutable." Historical tags and manifests remain frozen forever. |
| **Erasing WSABuilds Ancestry** | Metamorphosis Charter | Violates Rule S1: "Historical Identity Preservation." Upstream attribution is permanent. |

---

## 4. Open Investigations & Lab Status

- **Task 5.1 (Live Target-Environment Verification)**:
  - **Status**: `REQUIRES TARGET ENVIRONMENT VALIDATION`
  - **Context**: Full cold-boot restore on physical Windows 10 (19045) and Windows 11 (22631+) hardware cannot be executed inside headless CI runners.
  - **Lab Procedure**: Fully documented in `docs/WINDOWS_VALIDATION_LAB.md`. The gate will execute when dedicated physical lab hardware is connected.
