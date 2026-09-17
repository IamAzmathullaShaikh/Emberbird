# Emberbird Project Status

**Status:** Production Stewardship Edition  
**Milestone:** `emberbird-v1.0.0`  
**Operating Posture:** Repository Stewardship  
**Default Branch:** `main`  
**Architecture:** Frozen (`Reality → Registry → Contracts → Consumers`)  

---

## 1. Executive Status & Operating Posture

Emberbird has completed its Metamorphosis Programme (Phases E0–E7) and all initial post-metamorphosis engineering phases (D1, A1, R1, P2–P7). The platform operates under the **Production Stewardship Edition** model.

### Core Operating Axioms
1. **Published Artifacts Are Truth**: The release registry (`data/releases/releases.json`) reflects only genuine, published binary artifacts with verified SHA-256 vault hashes. No synthetic releases or placeholder hashes are permitted (Truth Hierarchy L1).
2. **Canonical Data Pipeline**: All consumers, portals, and managers strictly adhere to:
   $$\text{Reality} \longrightarrow \text{Registry} \longrightarrow \text{Contracts} \longrightarrow \text{Consumers}$$
3. **Contracts Are Frozen**: The contract specifications in `data/contracts/` govern wire formats, releases, channels, and integrity across the ecosystem.
4. **Historical Preservation Is Permanent**: Historical releases, tags, manifests, and lineage attributions (MustardChef, WSABuilds, MagiskOnWSA, AGPL-3.0) are immutable (Rule M4, Rule S1).
5. **No Transformation / No Redesign**: The platform architecture is frozen. Future capabilities require separately chartered programmes ratified by the Programme Board (`docs/programme-board.md`).

---

## 2. Platform Subsystems & Component Matrix

| Subsystem | Phase / Provenance | Status | Direct Consumer / Entrypoint |
|---|---|---|---|
| **Release Registry Engine** | Cycle P0 / S1 | **ACTIVE / AUTHORITATIVE** | `platform/release-engine/` (`releases.json`, `releases.schema.json`) |
| **Release Contracts** | Cycle P0 / E1.5 | **FROZEN** | `data/contracts/` (`release-contract.md`, `channel-contract.md`) |
| **Subsystem Doctor (CLI)** | Phase D1 | **PRODUCTION READY** | `scripts/doctor.py` / `platform/doctor/` (Probes PRB-01 to PRB-07) |
| **ARM64 Toolchain (BYOB)** | Phase A1 (P8) | **PRODUCTION READY** | `tools/build.sh`, `tools/build_local.py` (`--wsa-file`, `--arch arm64`) |
| **Android 14 Research** | Phase R1 | **COMPLETE (LTS BASELINE)** | `docs/research/ANDROID14_FEASIBILITY.md` (Android 13 LTS Ratified) |
| **Desktop Manager (V2)** | Phase P2 | **REGISTRY-DRIVEN** | `apps/manager/` (License Transparency, VHDX Safeguards) |
| **Documentation & Downloads** | Phase P3 | **REGISTRY-DRIVEN** | `website/` (Zero-network build-time release provider) |
| **Compatibility Platform** | Phase P4 | **HARDENED** | `compatibility/` (Validated against canonical channel tokens) |
| **Ember Observatory** | Phase P5 | **OPERATIONAL** | `services/analytics/observatory.py` (Telemetry policy distillation) |
| **Trusted Signing Governance** | Phase P6 | **RATIFIED** | `docs/LICENSE_AUDIT.md` §5 (Azure Trusted Signing / FIPS 140-2 Level 3) |
| **Distribution Automation** | Phase P7 | **OPERATIONAL** | `scripts/generate_package_manifests.py` (Winget, Scoop, Chocolatey) |
| **Programme Intelligence** | AntiGravity | **ACTIVE (10.0 / 10.0)** | `scripts/programme_intelligence.py` (Continuous 10-dimension audit) |

---

## 3. Governance Scorecard & Dimension Health

The AntiGravity Programme Intelligence System continuously verifies that all 10 architectural and governance invariants pass offline without network requirements:

```
================================================================================
  AntiGravity Programme Intelligence System
  Platform: Emberbird (Stewardship Edition)
  Status: HEALTHY | Overall Health Score: 10.0 / 10.0
  Dimensions Invariant: 10 / 10 PASS
================================================================================
#   Dimension                        Status   Score  Details
--------------------------------------------------------------------------------
1   Registry Integrity               PASS     10.0   6 releases, 9 vault cuts; release_engine verified
2   Consumer Compliance              PASS     10.0   Website & Manager 100% registry-driven
3   Documentation Integrity          PASS     10.0   95 Markdown docs link-clean; mirror guard OK
4   Secret & Credential Posture      PASS     10.0   0 GitHub tokens/keys; 0 machine paths
5   Privacy & Zero-PII               PASS     10.0   Opt-in telemetry; 0 personal data collected
6   Distribution Synchronization     PASS     10.0   Emberbird.Manager 0.2.2 synchronized in manifests
7   Historical Preservation          PASS     10.0   MustardChef & WSABuilds lineage intact; G3 clean
8   Branch & WIP Hygiene             PASS     10.0   4 protected branches documented; diffs preserved
9   Test Battery Readiness           PASS     10.0   36 test suites registered; all guards green
10  CI/CD Workflow Truth             PASS     10.0   All 13 workflows documented in WORKFLOWS.md
================================================================================
```

---

## 4. Verification & Testing Posture

- **Python Test Battery**: 338 tests pass offline (`python -m unittest discover -s tests`).
- **Desktop Manager Battery**: 33 tests pass (`npm test --prefix apps/manager`); `tsc --noEmit` passes with 0 type errors.
- **Website Test Battery**: 39 tests pass (`npm test --prefix website`); `tsc --noEmit` passes with 0 type errors.
- **Relative Link Integrity**: 95 Markdown files audited with 0 broken links (`scripts/check_doc_links.py`).

---

## 5. Continuity & Future Work

All changes to Emberbird must preserve backwards compatibility, attribution, and registry authority. Any new engineering initiative requires a formal charter approved by the Programme Control Board (`docs/programme-board.md`).
