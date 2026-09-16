# Emberbird CI/CD & GitHub Architecture

The `.github/` directory manages GitHub Actions workflows, community issue templates, pull request standards, and automation pipelines for the **Emberbird** platform.

---

## 1. Active CI/CD Workflows

| Workflow File | Name & Purpose | Triggers | Runner Environment |
|---|---|---|---|
| **`build.yml`** | Code Quality, ShellCheck, compileall, and offline unit test suite. | Push / PR on `master`, `main` | `ubuntu-latest` |
| **`registry-drift.yml`** | Registry Reality Sync (P1.1): regenerates the release registry from published GitHub reality and gates on drift via the Release Engine; opens/updates a `registry-drift` issue with the delta — never auto-commits. | Daily cron / workflow_dispatch | `ubuntu-latest` |
| **`docs-validation.yml`** | Markdown link integrity auditor and secret scanner. | Push / PR on `master`, `experimental`, `feature/*` | `ubuntu-22.04` |
| **`compatibility-validation.yml`** | Automated JSON schema validator for app compatibility submissions. | PR on `compatibility/data/**` | `ubuntu-latest` |
| **`manager-build.yml`** | Native desktop client typecheck, clippy, and Rust unit test suite. | Push / PR on `apps/manager/**` | `windows-latest` |
| **`website-deploy.yml`** | Static site generation, Pagefind search indexing, and Cloudflare Pages deployment. | Push on `master`, `website/**`, `docs/**`, `services/analytics/**` | `ubuntu-22.04` |
| **`winget-release.yml`** | Desktop manager packaging, portable ZIP archive bundling, and Winget manifest staging. | Push on `v*` tags | `windows-latest` |
| **`release.yml`** | 3-stage WSA package compilation, validation, and release publishing. | Push on `Windows_*`, `wsa-v*` tags | `ubuntu-latest` |
| **`validation.yml`** | Deep subsystem and package integrity testing suite. | Weekly cron / workflow_dispatch | `ubuntu-latest` & Windows |
| **`runtime-compatibility.yml`** | Executable GOVERNANCE.md Appendix D: runtime compatibility harness against a live WSA instance, plus report/submission schema validation. | Push / PR (harness paths) / workflow_dispatch | `ubuntu-latest` (live probes need a self-hosted WSA runner) |
| **`security.yml`** | Scheduled secret, credential, and path audit. | Weekly cron / workflow_dispatch | `ubuntu-latest` |
| **`update.yml`** | Automated update discovery for Microsoft FE3, Magisk, and GApps. | Scheduled cron | `ubuntu-latest` |
| **`upstream-sync.yml`** | Upstream repository tracking and synchronization. | Scheduled cron | `ubuntu-latest` |

---

## 2. Release Tag Namespaces

To prevent release collisions, tags are strictly segregated:
- **`Windows_*` / `wsa-v*`**: Triggers **WSA Subsystem Packaging** (`release.yml`).  
  *Example*: `Windows_11_2311.40000.5.0` or `wsa-v2311.40000.5.0`
- **`v*`**: Triggers **WSABuilds Manager Desktop Packaging** (`winget-release.yml`).  
  *Example*: `v0.2.0`

---

## 3. Required Repository Secrets

| Secret Name | Consuming Workflow | Purpose |
|---|---|---|
| **`GITHUB_TOKEN`** | `release.yml`, `winget-release.yml`, `registry-drift.yml` | Publishing release assets, archiving artifacts, and authenticated registry reality-sync (rate-limit headroom). |
| **`CLOUDFLARE_API_TOKEN`** | `website-deploy.yml` | Authenticating deployment to Cloudflare Pages. |
| **`CLOUDFLARE_ACCOUNT_ID`** | `website-deploy.yml` | Cloudflare account routing identifier. |

---

## 4. Community Templates

- **`.github/ISSUE_TEMPLATE/bug_report.yml`**: Structured bug reporting form with OS, hardware, and flavor selectors.
- **`.github/ISSUE_TEMPLATE/feature_request.yml`**: Feature suggestion form aligned with project scope.
- **`.github/ISSUE_TEMPLATE/compatibility_report.yml`**: App compatibility submission template.
- **`.github/PULL_REQUEST_TEMPLATE.md`**: Multi-engine verification checklist covering Python, website, desktop manager, and distribution validators.
