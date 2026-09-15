# Emberbird Cleanup Register — Cycle S1 (September 15, 2026)

**Scope**: Evidence-first continuous audit (Continuous Audit Mode mandate). **Zero deletions were executed in this cycle.** Every candidate below carries evidence and a decision; removals happen only in a follow-up cycle after the evidence is accepted by the owner.

**Baseline**: This register is an increment over `CLEANUP_REPORT.md` (2026-09-13, 776 files removed in 4 phases) and `REMOVED_ROOT_SOLUTIONS.md` (KernelSU/SuperSU forensic elimination). Those documents are the historical record; this register tracks what the S1 audit found *on top of* that state.

---

## Findings

### CR-1 — Issue form still offers KernelSU as a root-solution option — ACTION NOW (documentation defect)

- **Candidate**: `.github/ISSUE_TEMPLATE/compatibility_report.yml`, `root_flavor` dropdown
- **Evidence**: The form offers `"KernelSU"` as a selectable option. `REMOVED_ROOT_SOLUTIONS.md` proves KernelSU is forensically eliminated (no build path, no scripts, no binaries). A repository-wide search shows **zero** compatibility records in `compatibility/data/` use KernelSU — submissions selecting it could never describe a real, installable build.
- **Why safe to remove**: The option solicits reports for a product variant that cannot exist; every KernelSU submission would be invalid data entering the Compatibility Hub.
- **Decision**: **REMOVE-PROPOSED** (this cycle). The option is removed in S1 as a documentation-reality fix, not a functional deletion. Manager/website type unions (`root_flavor: 'Magisk' | 'KernelSU' | 'None'` in `apps/manager/src/lib/types.ts`) are retained this cycle: they are typed data readers that must tolerate historical third-party data, and changing them touches protected-subsystem code — recorded for the owner's decision.

### CR-2 — WORKFLOWS.md missing `runtime-compatibility.yml` — FIXED IN S1

- **Candidate**: `.github/WORKFLOWS.md` workflow inventory (11 of 12 documented)
- **Evidence**: `.github/workflows/` contains 12 workflow files; `runtime-compatibility.yml` had zero references in WORKFLOWS.md. The workflow is **active** (per GOVERNANCE.md Appendix D, push/PR/dispatch triggers).
- **Why safe**: Pure documentation addition; no code touched.
- **Decision**: **FIXED** — the missing table row was added in S1.

### CR-3 — Manager Rust layer embeds release-pair constants — DEFERRED (Phase 2 scope)

- **Candidate**: `apps/manager/src-tauri/src/*.rs` (`2311.40000.5.0` / `2407.40000.4.0` tag+version pairs in 8 files)
- **Evidence**: Registry Independence contract forbids hardcoded release intelligence in consumers. The Manager's Rust core embeds known tag/version pairs.
- **Why NOT removed now**: The Manager is a **protected subsystem**; migrating it to registry lookups is exactly **Phase 2 (Manager V2 on the registry)** per the locked roadmap. Removing the constants without the registry consumer in place would break the Manager with no replacement.
- **Decision**: **KEEP (tracked)** — deletion is contingent on Phase 2 implementation. This register entry is Phase 2's starting evidence.

### CR-4 — Build-time variables that look hardcoded but are legitimately so — KEEP (documented)

- **Candidates**: `MagiskOnWSA/scripts/apply_custom_model.sh`, `scripts/generate_release_metadata.py`, `scripts/e2e_clean_room.py` (`2407.40000.4.0`)
- **Evidence**: These are build/discovery inputs (baseline version for FE3 update discovery) and test-pinning values, not consumer release intelligence. `deployment/version.json` remains the declared baseline layer feeding them.
- **Decision**: **KEEP** — classification: build-time configuration, contractually the `deployment/` versioning layer's job until the registry fully assumes that role (future distribution phase).

### CR-5 — Untracked local residue — KEEP ON DISK (not repository content)

- **Candidates**: `package-identity-report.json`, `package-integrity-report.json`, `MagiskOnWSA/output/`, `dist_clean/`
- **Evidence**: `git ls-files` shows none are tracked; they are local build/validation outputs consumed by validators and the registry generator when present.
- **Decision**: **KEEP** — untracked working files; no repository action required. Never commit without the maintainer's explicit instruction.

### CR-6 — Documentation-scope gap for the registry tooling — CLOSED BY S1 TESTS

- **Candidate**: CI coverage question for `scripts/build_registry.py` + `platform/release-engine/`
- **Evidence**: `build.yml` runs `compileall` + `unittest discover -s tests`, which picks up all new engine/registry/consumer/guard tests with zero workflow changes; the `validate` CLI is exercised by tests (`test_release_engine.py::test_real_registry_satisfies_policy_guards` and the consumer suite). `docs-validation.yml` link-checks the new docs (verified green over the restructured README).
- **Decision**: **CLOSED** — no orphan tooling; all registry tooling is test-covered and CI-ratified. A dedicated workflow step invoking the `validate` CLI remains a P1 hardening candidate (tracked in TODO Part IV).

### CR-7 — `docs/README.md` hierarchy description drift — NOTED

- **Evidence**: `docs/README.md` describes `getting-started/` as containing quick-start/beginner/manual-install walkthroughs, but `UPGRADE_VALIDATION.md` and `WINDOWS_VALIDATION_LAB.md` live at the `docs/` root (the website mirror holds them under `getting-started/`). The mapping is now pinned by `tests/test_docs_mirror.py::PATH_MAP`, so the drift can no longer spread silently.
- **Decision**: **KEEP (noted)** — cosmetic; the authoritative structure map lives in the README Repository Structure section and the mirror guard. Optional cosmetic fix deferred to avoid churn in mirrored docs mid-cycle.

---

## Register statistics

| Metric | Count |
|---|---|
| Candidates identified | 7 |
| Removed this cycle | 0 (by design — evidence-first) |
| Fixed this cycle (doc-only) | 2 (CR-1 option removal, CR-2 WORKFLOWS row) |
| Kept with evidence | 4 (CR-3, CR-4, CR-5, CR-7) |
| Closed by test coverage | 1 (CR-6) |

## Root Solution Policy statement

Post-audit state: the repository's only root solutions are **Magisk (standard edition)** and **none (banking edition)** — confirmed by `build.sh`/`build_local.py` option surfaces and the complete absence of KernelSU/SuperSU in any active code path. The single residual solicitation surface (CR-1) is corrected in S1. Typed unions in manager/website code that merely *tolerate* the historical enum value are recorded for the owner's Phase 2 decision, per "do not remove functionality without proof."
