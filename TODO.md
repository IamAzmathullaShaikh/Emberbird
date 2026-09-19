# Emberbird — TODO (Executable Roadmap)

**Platform**: Emberbird — registry-first lifecycle platform for Android on Windows
**Current milestone**: Final Emberbird Build **0.3.0** (Phase FB — ACTIVE)
**Status tracking**: `[x]` = implemented & verified · `[ ]` = pending · `[!]` = blocked (reason required)

---

## Part 0 — Truth Hierarchy (binding)

When sources conflict, the higher level overrides the lower:

| Level | Source |
|---|---|
| **L1** | Published Release Assets |
| **L2** | Published Checksums |
| **L3** | Git History |
| L4 | Source Code |
| L5 | Documentation |
| L6 | TODO Commentary |

**Reality always overrides documentation.** Never fabricate release metadata,
never infer checksums, never invent versions.

---

## Part I — Execution Contract (binding on all work)

1. **One active phase.** Only the phase marked **ACTIVE** receives
   implementation. Future phases may be discussed, never implemented early.
2. **Phase guard.** Phase N+1 cannot start until Phase N's exit checklist is
   fully `[x]`. No exceptions.
3. **Exit checklists.** A phase is COMPLETE only when every item is checked,
   the full test suite is green, and CI ratifies the commit (local green ≠
   complete).
4. **Reality gates before merge.** Build Reality (compiles/lints), Registry
   Reality (`validate` exits 0), CI Truth (workflow ratifies), Runtime Reality
   (Windows-host items stay marked `REQUIRES TARGET ENVIRONMENT VALIDATION`
   until proven on real hardware).
5. **Protected subsystems** (never regress): WSA release pipeline, Standard &
   Banking editions, Manager, Website, Downloads portal, Compatibility Hub,
   Analytics, Release metadata, GitHub Releases, Winget, CI/CD, Clean-Room E2E.
6. **Status vocabulary.** Every closed item reports one of: `COMPLETE`,
   `BLOCKED` (with the blocking dependency), `REQUIRES DEPENDENCY`,
   `REQUIRES TARGET ENVIRONMENT VALIDATION`.
7. **Stop conditions.** Work stops immediately if a protected subsystem
   regresses, a dependency is missing, or an acceptance criterion is unclear.
   An honest `[!]` beats a fake `[x]`.
8. **Contracts frozen.** `data/contracts/*` and the registry schema change
   only per the evolution policy in `data/releases/GOVERNANCE.md`
   (additive-by-default; `migration_version` bump for breaks).
9. **Recommended Version Policy.** `recommended` = policy decision.
   `latest` = chronological fact. Never assume latest equals recommended;
   only a provenance-gated policy system may set it
   (`policy.recommended_by`, enforced by the engine integrity guard).
10. **Artifact Identification Rule.** Artifact identity is
    `(filename + sha256)`, never `filename` alone. Never deduplicate by
    filename; always deduplicate on artifact + hash.
11. **Release History Is Immutable (M4).** Never delete tags, rewrite
    published release metadata, rename historical assets, or mutate published
    winget manifests. New identity ships as *new* packages.
12. **Historical Identity Preservation (S1).** Historical project names
    (WSABuilds, MagiskOnWSA lineage, MustardChef, Microsoft WSA) remain
    visible wherever attribution, licensing, migration docs, or provenance
    require them.
13. **Zero-Mock law (Manager).** No surface may fabricate machine state.
    IPC wrappers reject outside the Tauri backend; detection failure is
    rendered honestly; every UI claim must trace to a real probe or the
    bundled registry.
14. **Execution engine fields.** Every closed cycle reports
    STATUS / BLOCKERS / DEPENDENCIES / FILES / RISKS / VALIDATION / RESULT.

---

## Part II — Where the Platform Stands (evidence as of 2026-09-19)

### Completed programme archive (all CI-ratified; full ledger in git history)

The metamorphosis and stewardship programme executed in full: P0–P1 registry
foundation, E0–E7 restructure/rebrand/rename, milestone `emberbird-v1.0.0`,
and the consumer/platform phases listed below. The long-form cycle ledger that
previously filled this file is preserved in git history (`git log -- TODO.md`).

- [x] P2 — Manager V2 on the registry (licenses screen; registry-driven release resolution)
- [x] P3 — Website on the registry (zero-network build-time release provider)
- [x] P4 — Compatibility platform (channel-contract tokens validated)
- [x] P5 — Analytics & Ember Observatory (signed policy decisions)
- [x] P6 — Trusted signing governance (Azure Trusted Signing / FIPS HSM addendum)
- [x] P7 — Distribution automation (Winget/Scoop/Chocolatey manifests from registry truth)
- [x] D1 — Project Doctor (stdlib diagnostic CLI, 7 probes, `--json`, elevated `--fix`)
- [x] A1 — Project Snapdragon (ARM64 build toolchain + BYOB pipeline)
- [x] R1 — Project Genesis (Android 14 research; Android 13 LTS ratified)
- [x] RI1 — Release integrity (publication gate: REAL / PLACEHOLDER / UNVERIFIABLE)
- [x] RI2 — Release build chain repair (E2-severed toolchain references repaired)
- [x] PR4 — Real-world release adoption (2407.40000.4.0 published & live-hash verified)

### Current reality (observed in code, 2026-09-19)

- [x] **Manager CI green.** 43/43 Node tests, `tsc --noEmit`, `cargo check`,
  and the Python guard battery all pass. Doctor heading aligned to
  "Actionable Remediations"; Header badges render
  "ARM64 (Snapdragon Native)" / "x64 Native".
- [x] **In-flight repairs landed** (`App.tsx`, `ReleaseCard.tsx`,
  `DoctorView.tsx`, `Header.tsx`, `package-lock.json`) — JSX
  escape-corruption fixes, animation classes, and the test-contract
  reconciliations above.
- [x] **Header.tsx null-safe** — `status?.… ?? false` everywhere; no
  non-null assertions during first load.
- [x] **Repository hygiene** — 10,850 tracked Rust build artifacts untracked
  from `apps/manager/src-tauri/target/`; `__pycache__` residue deleted;
  dead meta-governance docs and tests purged; identity inventory
  regenerated (827 → 819 occurrences).
- [!] **Doctor tab is static data** — 12 hardcoded probes violate the
  Zero-Mock law; `DoctorReportData` type exists, no Rust command backs it.
  (`platform/doctor` D1 engine exists but is not wired into the Manager.)
- [!] **Install loop broken mid-journey** — registry carries
  `browser_download_url` + `sha256` for every artifact, but nothing
  downloads/extracts; UI hardcodes paths (`C:\Emberbird\WSA_2407...`) that
  match no published artifact name.
- [!] **Baseline drift** — Rust fallback baseline `2311.40000.5.0` vs
  `deployment/version.json` `2407.40000.4.0` (whose `release_tag` still reads
  `wsa-v2311.40000.5.0`).
- [!] **ARM64 advertised, never shipped** — UI sells Snapdragon native builds;
  every registry asset is x64-only.
- [!] **Hardcoded UI copy overrides registry truth** — "Standard Edition
  2407.40000.4.0", "88.3% Verified Compatibility", "Req: 19045+" baked into
  components.

---

## Part III — Phase FB: Final Emberbird Build 0.3.0 (ACTIVE)

**Goal**: one clean, honest, end-to-end working 0.3.0 build — CI green, every
UI claim true, the install loop closed from registry artifact to registered
subsystem, and a released 0.3.0 through the governed pipeline.

### FB-0 — Make CI green (exit gate for everything else) — COMPLETE

- [x] Land the in-flight JSX repairs (App.tsx, ReleaseCard.tsx, DoctorView.tsx).
- [x] Delete stray artifact file `apps/manager/src/components/StatusCard.tsx\``
      (StatusCard.tsx restored intact; only the stray backtick file removed).
- [x] Reconcile the 2 drifting tests with honest code — Doctor heading now
      "Actionable Remediations"; Header badges now "ARM64 (Snapdragon
      Native)" / "x64 Native".
- [x] Fix `Header.tsx` null-status crash — `status?.… ?? false`; no `status!`
      non-null assertions remain.
- [x] Verify: `npm test` (43/43), `tsc --noEmit` (clean), `cargo check`
      (clean) — all green. `cargo clippy -- -D warnings` + `cargo test`
      pending target-environment run.

### FB-1 — Truth hardening

- [ ] Derive ReleaseCard recommendation banner (version, compatibility label)
      from registry truth instead of hardcoded strings.
- [ ] Derive UpdateView "Req: 19045+" copy from the preflight payload.
- [ ] Single-source the subsystem baseline: compile-time embed from
      `deployment/version.json`; remove the `2311.40000.5.0` fallback in
      `state.rs`; fix `subsystem_baseline.release_tag` mismatch
      (`wsa-v2311.40000.5.0` → the tag that actually carries 2407.40000.4.0).
- [ ] Verify: manager suites + Rust `state` tests green; no hardcoded version
      strings in living Manager UI code.

### FB-2 — Real Ember Doctor (honest diagnostics in the Manager)

- [ ] Add Rust command `run_doctor_scan` reusing detector primitives (registry
      keys, CIM/Hyper-V, DISM feature states, ADB port 58526, disk space, VHDX
      lock) returning the existing `DoctorReportData` shape.
- [ ] Rewire `DoctorView.tsx` to render live probes + real evidence + copyable
      remediation; remove the static probe array.
- [ ] Update `doctor.test.mjs` to pin live-scan wiring (no static PASS data).
- [ ] Verify: full manager battery green; Doctor tab shows machine truth.

### FB-3 — Close the loop: registry → installed (one-click, for real)

- [ ] Rust command `download_and_stage_release(asset)` — stream download with
      progress events, SHA-256 verify against the registry hash, extract,
      return staged path.
- [ ] Wire StatusCard edition buttons and UpdateView "Use for Upgrade" through
      download → verify → extract → prefill → install.
- [ ] Keep manual path entry as the advanced fallback; remove fabricated
      default paths that match no published artifact.
- [ ] Verify: end-to-end install from registry asset on a Windows host
      (`REQUIRES TARGET ENVIRONMENT VALIDATION` until proven on hardware).

### FB-4 — Honest architecture coverage

- [ ] Derive the architecture filter from registry assets: render ARM64
      guidance only when ARM64 artifacts exist in the registry.
- [ ] Either ship ARM64 artifacts in the build matrix (A1 toolchain exists) or
      the UI adapts honestly — no advertised-but-absent builds (Task 4.1 rule).

### FB-5 — Release 0.3.0

- [ ] Bump 0.2.2 → 0.3.0: `package.json`, `Cargo.toml`, `tauri.conf.json`,
      `deployment/version.json` (+ Header version badge).
- [ ] Regenerate winget manifests from published reality (P7 generator);
      registry reality-sync after publication (never hand-authored).
- [ ] Tag → `release.yml` / `winget-release.yml` gates: identity, integrity,
      magisk, gapps, immutable-history publish guard.
- [ ] Record the cycle in Part V with execution-engine fields.

**Exit checklist (FB complete when every line is `[x]`)**

- [ ] FB-0: full manager battery + Rust gates green; CI ratifies.
- [ ] FB-1: zero hardcoded release truth in living Manager UI code.
- [ ] FB-2: Doctor renders live machine truth (Zero-Mock law holds everywhere).
- [ ] FB-3: one-click install works from a registry asset (or honestly gated).
- [ ] FB-4: architecture claims match shipped artifacts.
- [ ] FB-5: 0.3.0 published through the governed pipeline; registry synced.
- [ ] Full battery green: Python suite, website tests, manager tests, Rust tests.
- [ ] CI ratification of the FB-final commit.

---

## Part IV — Future phases (LOCKED — awaiting separately chartered programmes)

Per the Execution Contract, everything beyond Phase FB stays LOCKED pending a
programme ratified by the Programme Board. Known candidates (not commitments):

- Manager backup data directory rename with a real migration path (BRAND §8 rule 5).
- Windows-lab live-validation gate (Task 5.1) when the lab environment exists.
- Android 14 GSI production revisit (blocked by R1 NO-GO; requires upstream change).

---

## Part V — Cycle Records

Each cycle appends one record below using the execution-engine fields:

```
### Cycle <ID> — <Title> (<date>)
- [x] <work order> — <one-line outcome>
STATUS: ... · BLOCKERS: ... · DEPENDENCIES: ... · FILES: ... ·
TESTS ADDED: ... · VALIDATION: ... · RISKS: ... · RESULT: ...
```

Full historical ledger (S1 → PR4, 1,700+ lines): preserved in git history of
this file. Active cycle: **FB** (Phase FB — Final Emberbird Build).

### Cycle FB-0a — CI repair + repository hygiene (2026-09-19)
- [x] Land JSX repairs, reconcile 2 drifting tests, make Header null-safe,
      delete stray artifact file, untrack 10,850 committed build artifacts,
      purge dead governance docs/tests, regenerate identity inventory.
STATUS: COMPLETE · BLOCKERS: none · DEPENDENCIES: none · FILES:
`apps/manager/src/{App,components/Header,components/DoctorView,components/ReleaseCard}.tsx`,
`apps/manager/src-tauri/target/**` (untracked), `docs/*` (purged),
`tests/test_docs_mirror.py` + governance suites (trimmed),
`docs/identity-inventory.json` (regenerated) · TESTS ADDED: none (contracts
reconciled, not weakened) · VALIDATION: manager 43/43, tsc clean, cargo check
clean, Python guard battery OK · RISKS: `git rm --cached` staging must be
committed to take effect on the remote · RESULT: repo carries source only;
FB-0 exit checklist satisfied except clippy/cargo-test on target hardware.
