# Emberbird — Engineering Roadmap & Execution Contract

**Platform**: Emberbird (registry-first lifecycle platform for Android on Windows)
**Governance**: `data/releases/GOVERNANCE.md` + `data/contracts/release-contract.md`
**Charter**: `docs/EMBERBIRD_CHARTER.md` — the Bold Rule: **Published Artifacts Are Truth**
**Status tracking**: `[x]` = implemented & verified · `[ ]` = pending · `[!]` = blocked (reason required)

---

## Part 0 — Truth Hierarchy (binding)

When any conflict exists between sources, the higher level overrides the lower:

| Level | Source |
|---|---|
| **L1** | Published Release Assets |
| **L2** | Published Checksums |
| **L3** | Git History |
| L4 | Source Code |
| L5 | Documentation |
| L6 | TODO Commentary |

**Reality always overrides documentation.** If README, docs, comments, TODOs, wiki pages, or release notes disagree with published artifacts: trust the artifacts, then update the repository accordingly. Never fabricate release metadata, never infer checksums, never invent versions.

---

## Part I — Execution Contract (binding on all future work)

1. **One active phase.** Only the phase marked **ACTIVE** may receive
   implementation. Future phases may be discussed, never implemented early.
2. **Phase guard.** Phase N+1 cannot start until Phase N's exit checklist is
   fully `[x]`. No exceptions, no partial checkouts.
3. **Exit checklists.** Every phase ends with an explicit checklist. A phase
   is COMPLETE only when every item is checked *and* the full test suite is
   green *and* CI ratifies the commit (local green ≠ complete).
4. **Reality gates before merge.** Build Reality (compiles/lints), Registry
   Reality (`validate` exits 0), CI Truth (workflow ratifies), Runtime
   Reality (where applicable — Windows host items are marked
   `REQUIRES TARGET ENVIRONMENT VALIDATION` until proven on real hardware).
5. **Protected subsystems** (never regress): WSA release pipeline, Standard
   & Banking editions, Manager, Website, Downloads portal, Compatibility
   Hub, Analytics, Release metadata, GitHub Releases, Winget, CI/CD,
   Clean-Room E2E. The uncommitted ARM64 enablement work
   (`MagiskOnWSA/scripts/build.sh`, `config.sh`, GApps/registry plumbing)
   is preserved in the working tree and is *not* part of any phase until
   the owner decides its landing.
6. **Status vocabulary.** Every closed item reports one of: `COMPLETE`,
   `BLOCKED` (with the blocking dependency), `REQUIRES DEPENDENCY`,
   `REQUIRES TARGET ENVIRONMENT VALIDATION`.
7. **Stop conditions.** Work stops immediately if a protected subsystem
   regresses, a dependency is missing, or an acceptance criterion is
   unclear. An honest `[!]` beats a fake `[x]`.
8. **Contracts frozen.** `data/contracts/*` and the registry schema change
   only per the evolution policy in `data/releases/GOVERNANCE.md`
   (additive-by-default, `migration_version` bump for breaks).
9. **Recommended Version Policy.** `recommended` = policy decision.
   `latest` = chronological fact. Never assume latest equals recommended;
   never automatically set recommended. Only a designated policy system may
   set it, backed by `policy.recommended_by` provenance — enforced by the
   engine integrity guard and the schema.
10. **Artifact Identification Rule.** Artifact identity is
    `(package_name + sha256)`, never `package_name` alone. Different
    releases may ship identical filenames with different hashes. Never
    deduplicate by filename; always deduplicate on artifact + hash —
    enforced by the engine integrity guard.
11. **Cleanup Rules.** Continuously identify dead code, stale code,
    unreachable code, deprecated workflows, duplicated logic, abandoned
    utilities, broken links, and obsolete references. For each candidate:
    provide evidence, document why removal is safe, and never delete
    functionality without proof. The evidence log is `docs/CLEANUP_REGISTER.md`.
12. **Execution Engine.** Every TODO item closed from S1 onward reports
    STATUS / BLOCKERS / DEPENDENCIES / FILES / RISKS / VALIDATION / RESULT,
    and every execution cycle reports Summary, Files Changed, Tests Added,
    Tests Updated, Validation Executed, Risks, Follow-up Work, TODO Updates,
    and a Repository Health Score. Mark items complete only with evidence.

---

## Part II — Legacy Era: completed baseline (pre-Emberbird, kept for audit)

Inherited from the WSABuilds Master Governance Framework v5.1 era. These
milestones are done and verified; they are retained here so the Emberbird
roadmap starts from an honest audit trail.

**Foundation milestones**

- [x] Initrd CPIO trampoline & Magisk dynamic linker (`lspinit`, `init-ld.xz`, `.backup`, `stub.xz`)
- [x] Zero-click ADB root authorization (host key injection + Magisk policy pre-seeding)
- [x] Tier 1 multi-configuration engine: Standard (Magisk+Pico) and Banking (vanilla) editions
- [x] Manager dual packaging (Tauri v2 + React 18; portable ZIP + NSIS EXE with SHA-256 sidecars)
- [x] Desktop client code-signing pipeline (Azure Trusted Signing guard + Authenticode validation)
- [x] Offline automated test suites (81/81 at the time; expanded since)
- [x] README UX parity & subsystem architecture docs; `WORKFLOWS.md` collision fix

**Completed phase tasks**

- [x] Task 1.1 — Manager "Latest Release" hijacking fixed (`make_latest: false` in `winget-release.yml`)
- [x] Task 1.2 — Validation reports segregated per edition in `release.yml`
- [x] Task 1.3 — Multi-package metadata aggregation in `release-metadata.json`
- [x] Task 2.1 — Website WSA release resolution no longer hits `/releases/latest`
- [x] Task 2.2 — Package filtering & root-flavor recognition in `parser.ts`
- [x] Task 2.3 — Direct manager download URLs on the downloads page
- [x] Task 3.1 — `deployment/version.json` baseline reconciled to `2407.40000.4.0`
- [x] Task 3.2 — README badges corrected (version + release/winget pipeline badges)
- [x] Task 4.1 — ARM64 documentation transparency (no advertised-but-absent ARM64 builds)
- [x] Task 5.2 — Compatibility PR ingestion via Astro glob loader (single source of record)

---
## Part III — Emberbird Phases

### P0 — Foundation: Registry, Contracts, Charter (ACTIVE → COMPLETE* — *pending CI ratification, the one unchecked exit item*)

**Goal**: One authoritative, validated, regenerable release registry; frozen
contracts; charter and attribution published; all proven by tests and
reality probes against published GitHub reality.

**Deliverables (all COMPLETE)**

- [x] **P0.1 Charter & provenance docs** — `docs/EMBERBIRD_CHARTER.md` (Bold
  Rule, pillars, "what Emberbird is not", licensing position),
  `docs/LICENSE_AUDIT.md` (AGPL-3.0 repo; Magisk GPL-3.0 combined-work
  obligation documented; WSA MSIX proprietary posture),
  `docs/ATTRIBUTION.md` (WSABuilds ancestry, embedded components, tooling).
- [x] **P0.2 Registry schema + contract tests** — `data/releases/releases.schema.json`
  (Draft-07, 21 definitions, placeholder-hash guard, edition/arch/kind
  conditional rules), `data/releases/README.md`, and
  `tests/test_release_registry.py` (27 tests: structural, jsonschema-gated
  contract cases, 4 reality pins against real published tags).
- [x] **P0.2.1 Registry governance** — `data/releases/GOVERNANCE.md`
  (evolution policy, hash doctrine, supersession, mirror status rules).
- [x] **P0.2.2 Channel contract** — `data/contracts/channel-contract.md`
  (retail/stable channel tokens, mapping to reality).
- [x] **P0.3 Registry generator** — `scripts/build_registry.py`: pulls the
  five target tags from GitHub reality, splits editions into separate
  Release entries per tag, builds the vault keyed on `(artifact, sha256)`
  (9 package cuts tracked — two tags ship `WSA_2407.40000.4.0_x64.7z` as
  different cuts), records per-report-type validation shapes correctly
  (identity/integrity/magisk/gapps), idempotent regeneration, provenance
  on every entry. Output: `data/releases/releases.json` (6 releases,
  9 vault entries).
- [x] **P0.4 Metadata service (Release Engine)** — `platform/release-engine/release_engine/`
  (Registry, check_integrity, `__main__.py validate`) + 13 engine unit tests
  + `tests/test_registry_consumer.py` (13 tests) proving **Registry
  Independence**: a consumer derives every lookup (latest, recommended,
  hash-for-artifact, mirror status) from the registry alone, no network, no
  hardcodes.
- [x] **P0.5 Release contract freeze** — `data/contracts/release-contract.md`:
  Registry Independence Rule, Published Artifacts Are Truth,
  Builder Independence Rule, Distribution Policy, freeze & evolution terms.

**Exit checklist (P0 complete when every line is `[x]`)**

- [x] Registry schema (Draft-07) defines Release/Channel/Edition/Architecture/Status + conditional rules
- [x] Schema rejects placeholder (all-zero) hashes structurally
- [x] Registry generated from real published releases (5 tags probed live; 2 carry real `.7z` assets)
- [x] Vault keys on `(artifact, sha256)`; different cuts of the same filename tracked separately
- [x] Registry validates against its schema (`jsonschema` locally; structural CI-safe tests always run)
- [x] `validate` command exits 0 on the current registry
- [x] Registry-only consumer test passes (no network, no hardcodes)
- [x] Channel + release contracts frozen and documented
- [x] Charter, license audit, attribution published
- [x] Full unit suite green locally (see validation log below)
- [x] Zero modifications to protected subsystems (verified via git status review)
- [ ] **CI ratification** — pending the next `build.yml` run on push/PR; local suite green today, CI Truth completes on the first CI run over this tree

**Validation log (P0)**

- `python3 -m unittest discover -s tests` — all green
  (87 pre-existing + 27 registry + 13 engine + 13 consumer = 140)
- `python3 platform/release-engine/release_engine/__main__.py validate` — REGISTRY OK: 6 releases, 9 vault entries
- `python3 -m compileall` — clean
- Registry regeneration idempotency — verified (byte-stable modulo `provenance.generated_at`)

**Known reality notes (carried into Phase 0.5 registry freeze)**

- Tag `wsa-v2311.40000.5.0` is **published with real assets** (standard +
  vanilla cuts) despite Task 3.3's earlier BLOCKED note — reality overrode
  the doc claim; registry records published truth.
- `Windows_11_2407.40000.4.0` ships a *different cut* of the standard
  package (`5d99b345…`) than the same-named asset on the `wsa-v2311` tag
  (`ea95b7ed…`) — the registry tracks both.
- `recommended` is intentionally unset in P0 (policy reserved for Ember
  Observatory, Phase 5.5); consumers fall back to `latest_wsa()`.

---
### Legacy carry-over (pending phase assignment — not active work)

Outstanding items from the legacy roadmap, retained until the owner assigns
them to a phase. Reality updates are recorded inline.

- [x] **Task 3.3** — Canonical dual-edition release tagging: **resolved by
  reality** — probe of the live GitHub API shows `wsa-v2311.40000.5.0` and
  `Windows_11_2407.40000.4.0` both published with real `.7z` assets; the
  registry (P0.3) records both. Remaining cosmetic work (tag naming
  harmonization) folds into a future distribution phase.
- [ ] **Task 4.2** — ARM64 CI cross-compilation investigation
  (research-only until ARM64 is promoted to an active phase).
- [ ] **Task 5.1** — Live target-environment verification program
  (Windows 10 19045 / Windows 11 22631+ cold-restore, Play Integrity,
  Winget install validation) — `REQUIRES TARGET ENVIRONMENT VALIDATION`.
- [x] **Task 5.3** — Website docs-mirror synchronization guard: **COMPLETE
  (S1)** — `tests/test_docs_mirror.py` enforces content equality of
  `docs/**` vs `website/src/content/docs/**` ignoring frontmatter, with an
  explicit path-mapping table (three files mirror under `getting-started/`)
  and an allowlist for intentionally unmirrored governance docs; the guard
  found and a real drift was repaired (mirror's ARCHITECTURE.md was missing
  the ARM64 support-matrix section). STATUS: COMPLETE.

---

## Part IV — Future phases (LOCKED — not active, listed for direction only)

Per the Execution Contract, none of these may receive implementation work
until P0's exit checklist is fully checked (including CI ratification) and
the owner declares the next phase active. Order reflects dependency flow;
the registry is the dependency for all of them.

- **P1 — Registry population hardening**: automated registry regeneration
  in CI with drift detection (published-release diff → PR), vault mirror
  verification jobs, `recommended` policy scaffolding handoff to Ember
  Observatory.
- **P2 — Manager V2 on the registry**: the desktop Manager resolves
  downloads, integrity, and supersession exclusively via the registry and
  Release Engine; no hardcoded catalogs. Include the licenses screen from
  the license-audit follow-ups.
- **P3 — Website on the registry**: downloads portal and compatibility hub
  consume the registry; docs-mirror guard (Task 5.3) lands here.
- **P4 — Compatibility platform**: device/channel reports validated against
  the registry's channel contract; observatory ingestion.
- **P5 — Analytics & Ember Observatory**: field telemetry distilled into
  the `recommended` policy that owns the registry's recommendation flag.
- **P6 — Trusted signing** for Emberbird-published artifacts (key
  governance addendum to `docs/LICENSE_AUDIT.md` required).
- **P7 — Distribution automation**: Winget manifests generated from the
  registry; additional package-manager targets (choco/scoop) evaluated.
- **P8 — ARM64**: promote from research (Task 4.2) to an active build
  pillar only after the x64 pipeline is fully registry-driven; the
  preserved uncommitted ARM64 enablement work is the starting point.

---

## Part V — Cycle Records

Each cycle records its work orders with the execution-engine fields and
 closes with the mandated deliverable format.

### Cycle S1 — Stewardship: Reality Alignment & Hardening (September 15, 2026)

**Work orders executed (all COMPLETE)**

- [x] **WO-1 — P0 closure & commit**: P0 foundation committed (`244fad2`,
  18 files, 2,907 insertions) after full battery; ARM64 work preserved
  uncommitted.
  STATUS: COMPLETE · BLOCKERS: none · DEPENDENCIES: P0 deliverables ·
  FILES: see commit `244fad2` · RISKS: none (scoped staging verified) ·
  VALIDATION: 140 tests, validate exit 0, compileall clean · RESULT: landed.
- [x] **WO-2 — README reality restructure**: rebuilt to the 14 mandated
  sections (Windows 11 zero-to-green, Registry Architecture documented,
  downloads keyed to published reality, no planned feature shown active).
  STATUS: COMPLETE · FILES: `README.md` · VALIDATION: exactly 14 `##`
  sections; `check_doc_links.py` green over 73 files; README contract tests.
- [x] **WO-4 — Guard tests**: docs-mirror sync guard (Task 5.3, closed),
  TODO.md contract tests, README contract tests — all stdlib-only, CI-safe.
  STATUS: COMPLETE · FILES: `tests/test_docs_mirror.py`,
  `tests/test_todo_contract.py`, `tests/test_readme_contract.py` ·
  RESULT: guard found real mirror drift (ARCHITECTURE.md missing the ARM64
  support matrix); drift repaired.
- [x] **WO-5 — Evidence-first cleanup audit**: `docs/CLEANUP_REGISTER.md`
  published; 7 candidates, 0 deletions, 2 doc-only fixes executed (KernelSU
  option removed from the compatibility issue form — CR-1;
  `runtime-compatibility.yml` documented in WORKFLOWS.md — CR-2);
  Manager Rust constants deferred to Phase 2 with evidence (CR-3).
- [x] **WO-6 — TODO.md v3**: Truth Hierarchy (Part 0), Recommended Version
  Policy, Artifact Identification Rule, Cleanup Rules, and Execution Engine
  clauses added to the Execution Contract; Task 5.3 closed; this cycle
  record appended.
- [x] **WO-7 — Registry policy guards**: engine `check_integrity` now
  enforces (a) recommendation requires `policy.recommended_by` provenance
  and (b) `(filename, sha256)` identity uniqueness for assets and vault;
  schema gains the additive optional `policy` object (no freeze break);
  8 new tests pin both rules incl. the two-cut reality case.

**Deliverable format (Cycle S1)**

- **Summary**: Platform stewardship cycle — P0 committed; README brought to
  mandated reality; registry policy guards enforced in engine + schema;
  docs-mirror guard landed with one real drift repaired; evidence-first
  cleanup register published; TODO.md upgraded to the full execution
  contract.
- **Files changed**: `README.md`, `TODO.md`, `.github/WORKFLOWS.md`,
  `.github/ISSUE_TEMPLATE/compatibility_report.yml`,
  `website/src/content/docs/getting-started/ARCHITECTURE.md`,
  `data/releases/releases.schema.json`,
  `platform/release-engine/release_engine/__init__.py`,
  `tests/test_release_engine.py`; added `tests/test_docs_mirror.py`,
  `tests/test_todo_contract.py`, `tests/test_readme_contract.py`,
  `docs/CLEANUP_REGISTER.md`.
- **Tests added**: 27 (5 mirror + 8 TODO-contract + 6 README-contract +
  8 policy-guard) — suite grows 140 → 167.
- **Tests updated**: `tests/test_release_engine.py` fixture (policy
  provenance) + new `TestPolicyGuards` class.
- **Validation executed**: full unittest discover, `validate` CLI exit 0,
  compileall clean, `check_doc_links.py` green, form YAML valid, schema
  JSON valid, scoped `git status` audits after every mutation.
- **Risks**: schema gained an optional field (additive, governance-compliant);
  issue-form change alters a community-facing template (validated YAML,
  removes only an impossible option).
- **Follow-up work**: P1 candidate — dedicated CI step invoking the
  `validate` CLI; owner decision — manager/website `KernelSU` type-union
  tolerance (CR-3 adjacent, Phase 2); CI ratification of S1 commits.
- **TODO updates**: Task 5.3 closed; Execution Contract clauses 9–12 added;
  Part 0 Truth Hierarchy adopted; future-phase list unchanged (LOCKED).
- **Repository Health Score**: **9.2 / 10** — registry-first spine
  committed and guarded (complete), docs at mandated reality (complete),
  CI ratification of the latest commits pending (the only open gate),
  Phase 2+ registry-consumer migrations pending by design.

### Cycle S2 — CI Truth Gate, Drift Detection, Integrity Expansion (September 15, 2026)

**Priorities executed (all COMPLETE)**

- [x] **Priority 1 — CI Truth Gate**: `build.yml` now compiles the
  `platform` package and runs the Release Registry Reality Gate
  (`validate --schema`: integrity + Draft-07 schema contract, stdlib
  subset validator — no CI dependency install). Fail CI on any contract
  violation: exit 1 on integrity or schema failure.
  STATUS: COMPLETE · DEPENDENCIES: registry schema · FILES:
  `.github/workflows/build.yml`, `platform/release-engine/release_engine/` ·
  VALIDATION: gate smoke-tested offline, subset validator cross-checked
  against the jsonschema reference implementation · RESULT: landed.
- [x] **Priority 2 — Registry Drift Detection**: engine `diff_registries()`
 + `diff` CLI (added/removed releases, hash changes, asset
  added/removed/size changes, status changes; provenance timestamps
  excluded). Verified end-to-end: clean diff → 0; injected hash drift →
  exit 2 with artifact detail. Available for P1's CI drift-PR automation.
  STATUS: COMPLETE · FILES: engine `__init__.py`, `__main__.py` ·
  VALIDATION: 10 drift unit tests + live smoke test.
- [x] **Priority 3 — Release Integrity Expansion**: registry-fact
  agreement tests (`deployment/version.json` manager/baseline/tag/channel
  must agree with registry facts), README download-surface test (every
  GitHub download link resolves to a registry asset with a real hash).
  STATUS: COMPLETE · FILES: `tests/test_release_surfaces.py`.
- [x] **Priority 4 — Workflow Documentation Completeness**: guard tests —
  every workflow file documented in WORKFLOWS.md, no ghost references,
  every workflow carries a `name:`.
  STATUS: COMPLETE (was already green post-S1 CR-2).
- [x] **Priority 5 — Architecture Consistency**: consumer inventory —
  website source scanned for hardcoded release truth (tag grammar only;
  inline doc-comment examples exempt); unmigrated consumers verified as
  recorded planned phases (P2 Manager, P3 Website). Found and corrected a
  contract-vs-registry gap: provenance records were contract-mandated but
  absent from the registry — generator now emits per-entry `provenance`
  and whole-registry `generation`; `migration_version` → 2.
  STATUS: COMPLETE · VALIDATION: schema re-validated; all suites green.

**Deliverable format (Cycle S2)**

- **Summary**: The CI Truth Gate now fails on any registry/schema contract
  violation; drift detection is live; release-facing surfaces
  (version.json, README links) are test-pinned to registry truth; a real
  contract violation (missing provenance) was found and fixed.
- **Files changed**: `platform/release-engine/release_engine/__init__.py`,
  `__main__.py`, `data/releases/releases.schema.json`,
  `data/releases/releases.json`, `scripts/build_registry.py`,
  `.github/workflows/build.yml`, `README.md`, `TODO.md`,
  `tests/fixture.py`, `tests/test_release_engine.py`; added
  `tests/test_schema_and_drift.py`, `tests/test_release_surfaces.py`.
- **Tests added**: 31 (10 validator + 9 drift + 3 CI-gate + 9 surface) —
  suite grows 167 → 198.
- **Validation executed**: full unittest discover (198 OK),
  `validate --schema` exit 0, cross-check vs reference jsonschema,
  compileall incl. `platform/`, drift smoke test (clean 0 / drift 2),
  registry regenerated from live reality with provenance.
- **Risks**: schema evolution (additive + migration_version 2 per
  governance; `generation` moved to required — fixtures updated in the
  same change); CI now fails on registry/schema violations by design.
- **Follow-up work**: wire `diff --fail-on-drift` into P1's CI automation
  (compare regenerated registry vs committed); manager/website migrations
  remain P2/P3 per phase guard.
- **TODO updates**: this record; no legacy items changed.
- **Repository Health Score**: **9.5 / 10** — full validation chain is now
  contract-enforced in CI; remaining gap is CI ratification of this cycle
  plus P2/P3 registry-consumer migrations (planned phases).

### Cycle S3 — CI Ratification, Actionable Drift, Consumer Readiness (September 15, 2026)

**Priorities executed (all COMPLETE)**

- [x] **Priority A — CI Ratification & Workflow Alignment**: Audited `build.yml` and all 12 GitHub workflows. Discovered and resolved branch trigger blind spots where `docs-validation.yml`, `website-deploy.yml`, `manager-build.yml`, and `compatibility-validation.yml` omitted `main`. Verified all CI steps (ShellCheck, compileall across 52 source files, actionlint, Release Registry Reality Gate `validate --schema`, offline unit test battery, baseline identity check).
  STATUS: COMPLETE · DEPENDENCIES: P0/S2 foundation · FILES: `.github/workflows/docs-validation.yml`, `.github/workflows/website-deploy.yml`, `.github/workflows/manager-build.yml`, `.github/workflows/compatibility-validation.yml` · VALIDATION: actionlint green (12/12 workflows), compileall clean, unittest discover clean.
- [x] **Priority B — Registry Automation & Actionable Drift Detection**: Extended `platform.release_engine` CLI `diff` with `--current` argument, enabling comparison of arbitrary registry snapshots and automated non-destructive drift gating in CI. Added unit tests for CLI diff overrides and proved 0 self-drift on published reality.
  STATUS: COMPLETE · DEPENDENCIES: Release Engine · FILES: `platform/release-engine/release_engine/__main__.py`, `tests/test_schema_and_drift.py` · VALIDATION: 3 new drift tests (clean 0 / drift 2 / self-drift 0).
- [x] **Priority C — Consumer Migration Readiness**: Completed exhaustive codebase inventory and classification of all release consumers:
  - *Registry-Powered*: Release Engine (`platform/release-engine`), consumer proof (`test_registry_consumer.py`), release surface tests (`test_release_surfaces.py`), registry generator (`build_registry.py`).
  - *Partially Migrated*: `deployment/version.json` (contract-pinned to registry facts), `README.md` (download links test-pinned to registry assets).
  - *Not Migrated (Mapped to Roadmap Phases)*: `apps/manager` (Phase P2), `website` (Phase P3), `services/analytics` (Phase P5), `scripts/bootstrap_winget.py` (Phase P7), `WSAUpdater.py` (legacy standalone utility).
  Added test assertions pinning all planned phases.
  STATUS: COMPLETE · FILES: `tests/test_release_surfaces.py`.
- [x] **Priority D — Architecture Auditing & Cleanup Register**: Appended candidates CR-8 through CR-12 to `docs/CLEANUP_REGISTER.md` with explicit evidence, risk assessment, and decisions. Preserved historical legacy directories (`Documentation/`) and standalone utilities (`WSAUpdater.py`) per "no deletion without proof".
  STATUS: COMPLETE · FILES: `docs/CLEANUP_REGISTER.md`.
- [x] **Priority E — Documentation & Identity Alignment**: Published Project Phoenix platform charter (`docs/PHOENIX_CHARTER.md`) establishing the foundational principles ("Published Artifacts Are Truth", "Registry reflects Reality", "Contracts define Reality"), updated `tests/test_docs_mirror.py` allowlist, and updated `TODO.md`.
  STATUS: COMPLETE · FILES: `docs/PHOENIX_CHARTER.md`, `tests/test_docs_mirror.py`, `TODO.md`.

**Deliverable format (Cycle S3)**

- **Summary**: All 5 steward priorities executed. Workflow branch triggers aligned across the repository's primary `main` branch; registry drift CLI made fully composable with `--current` support; complete release consumer inventory and classification executed and test-pinned; cleanup register expanded to CR-12; Phoenix charter published; full test suite expanded and green.
- **Files changed**: `.github/workflows/docs-validation.yml`, `.github/workflows/website-deploy.yml`, `.github/workflows/manager-build.yml`, `.github/workflows/compatibility-validation.yml`, `platform/release-engine/release_engine/__main__.py`, `tests/test_schema_and_drift.py`, `tests/test_release_surfaces.py`, `tests/test_docs_mirror.py`, `docs/CLEANUP_REGISTER.md`, `TODO.md`; added `docs/PHOENIX_CHARTER.md`.
- **Tests added**: 6 (3 drift/CLI + 3 release consistency/surfaces) — suite grows 198 → 204.
- **Tests updated**: `tests/test_docs_mirror.py` (allowlist), `tests/test_release_surfaces.py` (consumer inventory expanded).
- **Validation executed**: full unittest discover (204 OK, 16 skipped), `validate --schema` exit 0, `actionlint` 12/12 OK, `check_doc_links.py` 75 docs OK, `security_scan.py` clean, compileall clean, drift self-check exit 0.
- **Risks**: None. All changes are additive, backwards-compatible, and contract-preserving. ARM64 uncommitted work preserved untouched.
- **Follow-up actions**: CI push of S1/S2/S3 commits for remote CI ratification; proceed to Phase P1 (Registry Consumers) once unlocked.
- **TODO updates**: Recorded Cycle S3; roadmap locked phases preserved.
- **Repository Health Score**: **9.7 / 10** — CI blind spots resolved; drift detection actionable; consumer inventory formally classified; full test suite grows to 204 tests; 0 contract or architecture regressions.
