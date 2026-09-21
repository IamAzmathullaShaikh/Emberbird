# Emberbird CI/CD & GitHub Architecture

The `.github/` directory manages GitHub Actions workflows, community issue templates, pull request standards, and automation pipelines for the **Emberbird** platform.

---

## 1. Active CI/CD Workflows

| Workflow File | Name & Purpose | Triggers | Runner Environment |
|---|---|---|---|
| **`build.yml`** | Code Quality, ShellCheck, compileall, and offline unit test suite. | Push / PR on `master`, `main` | `ubuntu-latest` |
| **`registry-drift.yml`** | Registry Reality Sync (P1.1): regenerates the release registry from published GitHub reality and gates on drift via the Release Engine; opens/updates a `registry-drift` issue with the delta — never auto-commits. | Daily cron / workflow_dispatch | `ubuntu-latest` |
| **`docs-validation.yml`** | Markdown link integrity auditor. | Push / PR on `master`, `experimental`, `feature/*` | `ubuntu-22.04` |
| **`compatibility-validation.yml`** | Automated JSON schema validator for app compatibility submissions. | PR on `compatibility/data/**` | `ubuntu-latest` |
| **`manager-build.yml`** | Native desktop client typecheck, clippy, ESLint, Vitest, and Rust unit test suite. Includes `cargo fmt --check` and `tauri build` packaging gate. | Push / PR on `apps/manager/**` | `windows-latest` |
| **`manager-e2e.yml`** | End-to-end Playwright + Tauri WebDriver test suite for critical user journeys (QG-4). Builds the release binary, installs `tauri-driver`, and runs E2E specs. | Push on `master`, `main`, `apps/manager/**` / workflow_dispatch | `windows-latest` |
| **`website-deploy.yml`** | Static site generation, Pagefind search indexing, and Cloudflare Pages deployment. | Push on `master`, `website/**`, `docs/**`, `services/analytics/**` | `ubuntu-22.04` |
| **`winget-release.yml`** | Desktop manager packaging, portable ZIP archive bundling, Winget manifest staging, and automated PR to `microsoft/winget-pkgs` (DX-2). | Push on `v*` tags | `windows-latest` |
| **`release.yml`** | 3-stage WSA package compilation, validation, and release publishing. | Push on `Windows_*`, `wsa-v*` tags | `ubuntu-latest` |
| **`runtime-compatibility.yml`** | Executable GOVERNANCE.md Appendix D: runtime compatibility harness against a live WSA instance, plus report/submission schema validation. | Push / PR (harness paths) / workflow_dispatch | `ubuntu-latest` (live probes need a self-hosted WSA runner) |
| **`gitleaks.yml`** | Secret and credential leak detection using Gitleaks (DX-1), plus the preserved hardcoded developer-machine-path / username gate. Runs on every push/PR and weekly full-history scan. | Push (all branches) / PR / weekly cron | `ubuntu-latest` |
| **`update.yml`** | Automated update discovery for Microsoft FE3, Magisk, and GApps. | Scheduled cron | `ubuntu-latest` |
| **`upstream-sync.yml`** | Upstream repository tracking and synchronization. | Scheduled cron | `ubuntu-latest` |

### Removed workflows (deliberate, not silently dropped)

Two redundant workflows have been removed, and each had unique coverage that was
folded into a surviving workflow rather than dropped:

- **The scheduled secret/credential/path audit** — DX-1 requires the Gitleaks
  workflow to *replace* the bespoke regex scanning, but the old file was left
  behind when Gitleaks was added, so the replacement was never completed. Its
  two checks that Gitleaks cannot perform (hardcoded developer machine paths and
  the author username) moved into the Gitleaks workflow as a hard-failure step.
- **The weekly subsystem validation suite** — fully duplicated: its
  package-identity step repeated the build workflow's identity job, and its four
  package validators are already exercised by the offline unit suite the build
  workflow runs (and against real built packages by the release workflow).

The per-cycle record of these removals lives in the `TODO.md` ledger.

---

## 2. Release Tag Namespaces

To prevent release collisions, tags are strictly segregated:
- **`Windows_*` / `wsa-v*`**: Triggers **WSA Subsystem Packaging** (`release.yml`).  
  *Example*: `Windows_11_2311.40000.5.0` or `wsa-v2311.40000.5.0`
- **`v*`**: Triggers **Emberbird Manager Desktop Packaging** (`winget-release.yml`).  
  *Example*: `v0.2.0`

---

## 3. Required Repository Secrets

| Secret Name | Consuming Workflow | Purpose |
|---|---|---|
| **`GITHUB_TOKEN`** | `release.yml`, `winget-release.yml`, `registry-drift.yml` | Publishing release assets, archiving artifacts, and authenticated registry reality-sync (rate-limit headroom). |
| **`CLOUDFLARE_API_TOKEN`** | `website-deploy.yml` | Authenticating deployment to Cloudflare Pages. |
| **`CLOUDFLARE_ACCOUNT_ID`** | `website-deploy.yml` | Cloudflare account routing identifier. |
| **`WINGET_TOKEN`** | `winget-release.yml` | PAT with `public_repo` scope for automated PR submission to `microsoft/winget-pkgs` (DX-2). Optional — if absent, manifests are uploaded as artifacts for manual submission. |

---

## 4. Community Templates

- **`.github/ISSUE_TEMPLATE/bug_report.yml`**: Structured bug reporting form with OS, hardware, and flavor selectors.
- **`.github/ISSUE_TEMPLATE/feature_request.yml`**: Feature suggestion form aligned with project scope.
- **`.github/ISSUE_TEMPLATE/compatibility_report.yml`**: App compatibility submission template.
- **`.github/PULL_REQUEST_TEMPLATE.md`**: Multi-engine verification checklist covering Python, website, desktop manager, and distribution validators.
