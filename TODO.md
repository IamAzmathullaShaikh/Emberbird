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
