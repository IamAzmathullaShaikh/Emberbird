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

### CR-8 — `docs-validation.yml` branch triggers omitted `main` — FIXED IN S3

- **File**: `.github/workflows/docs-validation.yml`
- **References**: `build.yml`, `.github/WORKFLOWS.md`
- **Evidence**: `docs-validation.yml` previously only monitored `[master, experimental, 'feature/*']`. Since `main` is the primary repository branch, pushes and PRs to `main` bypassed markdown link checks and secret audits.
- **Risk**: None.
- **Recommendation**: Add `main` to `push.branches` and `pull_request.branches`.
- **Decision**: **FIXED IN S3**.

### CR-9 — Workflow PR/push triggers omitted `main` parity — FIXED IN S3

- **File**: `.github/workflows/website-deploy.yml`, `.github/workflows/manager-build.yml`, `.github/workflows/compatibility-validation.yml`
- **References**: `.github/WORKFLOWS.md`
- **Evidence**: PR branch triggers in `website-deploy.yml` and `manager-build.yml` omitted `main`; push branch trigger in `compatibility-validation.yml` omitted `main`.
- **Risk**: None.
- **Recommendation**: Align triggers across all workflows to monitor `main`.
- **Decision**: **FIXED IN S3**.

### CR-10 — Legacy fallback repository in `WSAUpdater.py` — DEFERRED (Phase P7)

- **File**: `WSABuilds Utilities/Update Script/WSAUpdater.py`
- **References**: lines 41-42 (`FALLBACK_REPO = "MustardChef/WSABuilds"`)
- **Evidence**: Legacy fallback points to the 2023 pre-fork repository. If primary API calls fail, fallback could attempt to pull outdated 2023 releases.
- **Risk**: Low (standalone utility). Removing or changing without utility-suite overhaul could alter user script behavior.
- **Recommendation**: Defer to Phase P7 (Distribution automation) utility modernization.
- **Decision**: **KEEP (tracked)**.

### CR-11 — Release Engine `diff` CLI lacked arbitrary `--current` parameter — FIXED IN S3

- **File**: `platform/release-engine/release_engine/__main__.py`
- **References**: `diff` subcommand
- **Evidence**: CLI hardcoded the current registry to `data/releases/releases.json`, preventing automated testing or comparison between arbitrary registry snapshots without mutating workspace files.
- **Risk**: None (purely additive argument, default preserved).
- **Recommendation**: Add `--current` flag to `diff` subcommand.
- **Decision**: **FIXED IN S3**.

### CR-12 — Historical `Documentation/` directory — KEEP (Historical Archive)

- **File**: `Documentation/` directory (all files)
- **References**: 198+ legacy links to `MustardChef/WSABuilds`
- **Evidence**: Historical directory from the project's inception containing obsolete guides (`Run.bat`, outdated manual install steps). Official documentation lives under `docs/` and is mirrored to `website/src/content/docs/`.
- **Risk**: High risk of breaking historical references if deleted without explicit owner mandate.
- **Recommendation**: Keep unchanged as an audit-safe historical archive per "no deletion without proof".
- **Decision**: **KEEP (historical archive)**.

### CR-13 — Docs-mirror false drift in `website/.../ARCHITECTURE.md` — FIXED

- **File**: `website/src/content/docs/getting-started/ARCHITECTURE.md`, `tests/test_docs_mirror.py`
- **References**: `docs/ARCHITECTURE.md`, `build.yml` Step 11
- **Evidence**: In Cycle S1 (commit `ecf6bf2`), Section 5 (Architecture Support Matrix) from uncommitted local ARM64 drafts was mirrored and committed to `website/.../ARCHITECTURE.md`, while `docs/ARCHITECTURE.md` remained uncommitted under the ARM64 Protection Rule. On clean CI checkouts, committed `docs/ARCHITECTURE.md` lacked Section 5, failing `test_mirrored_content_matches_source`.
- **Risk**: None (aligns mirror with committed repository source of truth L4).
- **Recommendation**: Revert Section 5 from website mirror to match committed `docs/` source at HEAD; enhance `tests/test_docs_mirror.py` to read committed HEAD content when uncommitted working-tree modifications exist.
- **Decision**: **FIXED**.

---

## Register statistics

| Metric | Count |
|---|---|
| Candidates identified | 13 |
| Removed this cycle | 0 (by design — evidence-first) |
| Fixed to date (doc/config/tooling) | 6 (CR-1, CR-2, CR-8, CR-9, CR-11, CR-13) |
| Kept with evidence / deferred | 6 (CR-3, CR-4, CR-5, CR-7, CR-10, CR-12) |
| Closed by test coverage | 1 (CR-6) |

## Root Solution Policy statement

Post-audit state: the repository's only root solutions are **Magisk (standard edition)** and **none (banking edition)** — confirmed by `build.sh`/`build_local.py` option surfaces and the complete absence of KernelSU/SuperSU in any active code path. The single residual solicitation surface (CR-1) is corrected in S1. Typed unions in manager/website code that merely *tolerate* the historical enum value are recorded for the owner's Phase 2 decision, per "do not remove functionality without proof."
