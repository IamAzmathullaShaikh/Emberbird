# Architecture Decision Records (ADR) Index

This document serves as the formal register of Architectural Decision Records governing **Project Emberbird**.

---

## Summary of Decisions

| ID | Title | Status | Date | Primary Invariant |
|---|---|---|---|---|
| [ADR-001](#adr-001-registry-first-architecture--release-independence) | Registry-First Architecture & Release Independence | **ADOPTED** | 2026-09 | Consumers derive release intelligence solely from the registry. |
| [ADR-002](#adr-002-immutable-release-history--backward-compatibility-m4) | Immutable Release History & Backward Compatibility (M4) | **ADOPTED** | 2026-09 | Historical tags, manifests, and assets are never mutated or deleted. |
| [ADR-003](#adr-003-historical-identity-preservation--s1-attribution) | Historical Identity Preservation & S1 Attribution | **ADOPTED** | 2026-09 | Upstream lineage (MustardChef, WSABuilds, MagiskOnWSA) preserved. |
| [ADR-004](#adr-004-pure-offline-release-engine-core) | Pure-Offline Release Engine Core | **ADOPTED** | 2026-09 | Core metadata engine operates strictly offline without network calls. |
| [ADR-005](#adr-005-directory-restructure--index-based-inventory) | Directory Restructure & Index-Based Inventory | **ADOPTED** | 2026-09 | Reorganization governed by PATH_MAP v2 and git-index inventory scanning. |
| [ADR-006](#adr-006-consumer-migration-with-parity-proofs-g2s2) | Consumer Migration with Parity Proofs (G2/S2) | **ADOPTED** | 2026-09 | Legacy discovery replaced only after mathematical parity is proven. |
| [ADR-007](#adr-007-seam-derived-distribution-identity-e5) | Seam-Derived Distribution Identity (E5) | **ADOPTED** | 2026-09 | New package identity (`Emberbird.Manager`) ships as a separate stream. |
| [ADR-008](#adr-008-default-branch-switch-to-main--branch-hygiene) | Default Branch Switch to `main` & Branch Hygiene | **ADOPTED** | 2026-09 | Integration consolidated on `main`; protected branches retained. |

---

### ADR-001: Registry-First Architecture & Release Independence
- **Context**: Relying on live GitHub API calls or hardcoded release URLs causes breakage when endpoints change, rate limits hit, or repos move.
- **Decision**: All consumer surfaces (Web Portal, Desktop Manager, CLI, Winget) must derive release data exclusively from `data/releases/releases.json`.
- **Consequences**: Consumers operate deterministically offline; zero runtime dependence on GitHub API availability.

### ADR-002: Immutable Release History & Backward Compatibility (M4)
- **Context**: Renaming a project risks breaking existing installations, download links, and winget package lookups.
- **Decision**: Historical releases (`wsa-v2311`, `v0.2.0`, `v0.2.1`, `v0.2.2`), manifests, checksums, and tags are frozen and permanently immutable.
- **Consequences**: Old links continue to resolve; historical records documented in `HISTORICAL_PRESERVATION.md`.

### ADR-003: Historical Identity Preservation & S1 Attribution
- **Context**: Rebranding to Emberbird could accidentally obscure upstream open-source heritage.
- **Decision**: Attribution to MustardChef, WSABuilds, MagiskOnWSALocal, topjohnwu (Magisk), and Microsoft is legally protected and tested by CI (`test_attribution_preservation.py`).
- **Consequences**: Rebranding applies strictly to user-facing living chrome; historical lineage is never erased.

### ADR-004: Pure-Offline Release Engine Core
- **Context**: Embedding HTTP fetchers in core libraries leads to hidden network dependencies during testing and packaging.
- **Decision**: Keep `release_engine` core 100% offline-pure; inject network fetchers only at the explicit CLI boundary (`__main__.py`).
- **Consequences**: Unit tests run fully offline in milliseconds; zero flaky network test failures.

### ADR-005: Directory Restructure & Index-Based Inventory
- **Context**: The legacy directory structure had overlapping concerns (`Documentation/`, `MagiskOnWSA/scripts/`, `WSABuilds Utilities/`).
- **Decision**: Execute single-phase atomic restructure per `PATH_MAP.md` v2 into `tools/`, `utilities/`, `upstream/`, `docs/archive/`. Use git index scanning in `identity_map.py` to prevent line-shift false alarms.
- **Consequences**: Clean separation between tools, vendored upstreams, and archive documents.

### ADR-006: Consumer Migration with Parity Proofs (G2/S2)
- **Context**: Migrating consumers (Website, Manager) from GitHub API to Registry could subtly alter displayed releases or download targets.
- **Decision**: Enforce G2/S2 protocol: inventory discovery sites, create test-tree parity oracle, prove 100% output equality, then eliminate legacy discovery.
- **Consequences**: Zero consumer regressions; parity verified by automated test suites.

### ADR-007: Seam-Derived Distribution Identity (E5)
- **Context**: Publishing under the legacy package identifier `WSABuilds.WSABuildsManager` prevents proper platform branding.
- **Decision**: Author new manifests under `Emberbird.Manager` (v0.2.2) via `deployment/version.json` while keeping historical manifests frozen.
- **Consequences**: Clean new package identity for Windows Package Manager without mutating published historical history.

### ADR-008: Default Branch Switch to `main` & Branch Hygiene
- **Context**: Development had drifted with `master` as default while all modern work landed on `main`.
- **Decision**: Designate `main` as the default branch; retain `master`, `experimental`, and `gh-pages` as protected branches; delete merged feature branches after evidence verification.
- **Consequences**: Clean repository tree; clear contributor workflow targeting `main`.
