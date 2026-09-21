# Changelog

All notable changes to Emberbird are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Automated Winget PR submission via `winget-release.yml` (DX-2)
- Gitleaks secret scanning CI workflow (DX-1)

---

## [0.2.2] — 2026-09-21 — *Frontend Excellence & Quality Gate Release*

### Emberbird Manager

#### Added
- **Design System 2.0** — `src/components/ui/`: Card, Badge, Button, Alert, Spinner primitives. CSS custom properties (`src/design-tokens.css`) with `prefers-reduced-motion` and Windows High Contrast support.
- **Installer Wizard** — 5-step modal (Edition → Preflight → Download → Install → Done) with SHA-256 verified downloads.
- **i18n Architecture** — `src/lib/i18n.ts` with 30 English string keys and interpolation.
- **Vitest Component Tests** — 37+ tests across 5+ files.
- **Playwright E2E Foundation** — Tauri WebDriver fixtures + test specs + `manager-e2e.yml` CI.
- **Type Safety (specta)** — `#[derive(specta::Type)]` on all IPC structs + `test_type_drift.py` guard.
- **Automated Winget PR** — `submit-winget-pr` job via `vedantmgoyal9/winget-releaser`.
- **Release script** — `scripts/release.ps1` one-click release automation.
- **Accessibility audit** — axe-core automated tests, skip-to-content, ARIA roles.

#### Changed
- **Zustand state** — zero prop drilling across all 8 views.
- **Doctor scan** — 4 probes use native Win32 API (~1.5s speedup).
- **ESLint** — `--max-warnings 0` hard gate.
- **CI** — Vitest + Tauri NSIS build step in `manager-build.yml`; `|| true` removed from `website-deploy.yml`.

#### Fixed
- Timer leaks in DoctorView, StatusCard, UpdateView.
- 10 TypeScript errors in ReleaseCard, BackupView, RestoreView.
- `react-hooks/exhaustive-deps` warnings in BackupView, RestoreView, UpdateView.

---

## [0.2.1] — 2026 — *Registry & Winget Foundation*

### Emberbird Manager
- Initial Winget manifest (`WSABuilds.WSABuildsManager`).
- Release registry integration.
- Doctor scan (12 probes PRB-01 through PRB-12).
- Backup/Restore VHDX system.

---

## [0.2.0] — 2026 — *Emberbird Manager Initial Release*

### Emberbird Manager
- First public release as standalone Tauri v2 desktop application.
- WSA detection, status display, install/update flow.
- Multi-edition: Standard and Banking.
- NSIS installer, Winget manifest `WSABuilds.WSABuildsManager 0.2.0`.

---

## [Pre-0.2.0] — Legacy WSABuilds

- MagiskOnWSA lineage (MustardChef attribution per Rule 12).
- WSABuilds packaging and compatibility hub.
- Multiple WSA release generations: 2207 through 2407.
