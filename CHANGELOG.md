# Changelog

All notable changes to Emberbird are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.2] — 2026-09-21 — *Frontend Excellence & Quality Gate Release*

### Emberbird Manager

#### Added
- **Design System 2.0** — `src/components/ui/`: Card, Badge, Button, Alert, Spinner primitives built on semantic Tailwind tokens. CSS custom properties (`src/design-tokens.css`) with `prefers-reduced-motion` and `forced-colors` (Windows High Contrast) media queries.
- **Installer Wizard** — 5-step modal overlay (Edition → Preflight → Download → Install → Done) with live system requirement checks and SHA-256 verified download progress.
- **i18n Architecture** — `src/lib/i18n.ts` with 30 English string keys, `t()` interpolation function, and `detectAndSetLocale()` for future locale additions.
- **Vitest Component Tests** — 37 tests across 5 files: ErrorBoundary, Toast, StageProgress, i18n, UI primitives.
- **Playwright E2E Foundation** — `e2e/` directory with Tauri WebDriver fixtures, app launch/navigation/doctor/install-flow test specs. `manager-e2e.yml` CI workflow.
- **tauri-specta type safety** — `#[derive(specta::Type)]` on all IPC-boundary Rust structs. `tests/test_type_drift.py` structural guard (7 tests).
- **Automated Winget PR** — `submit-winget-pr` job in `winget-release.yml` using `vedantmgoyal9/winget-releaser`. Requires `WINGET_TOKEN` secret; graceful fallback if absent.
- **Release script** — `scripts/release.ps1` one-click release automation with full test battery and version consistency validation.
- **Git LFS** — tracking rules for `*.msix`, `*.appxbundle`, `*.exe`, `*.msi` installer binaries.
- **Developer tooling** — `pyproject.toml` (ruff, coverage, pytest), `scripts/run_coverage.ps1`, `.editorconfig`, `apps/manager/src-tauri/rustfmt.toml`.

#### Changed
- **Zustand state management** — all 8 manager views use `useEmberStore`; zero prop drilling. `StatusCard`, `UpdateView`, `BackupView`, `RestoreView`, `ReleaseCard`, `Header`, `App` accept no props.
- **Doctor scan speed** — PRB-01, PRB-04, PRB-10, PRB-12 replaced with native Win32 API calls (eliminating 4 PowerShell/cmd spawns); ~1.1–1.5 s per-scan speedup.
- **ESLint enforcement** — `--max-warnings 0` hard gate. `useCallback` wrapping for async hooks; `addNotification` replaces all `console.error` in production code paths.
- **CI pipeline** — `manager-build.yml` adds Vitest step, Tauri NSIS packaging gate, `cargo fmt --check`. `website-deploy.yml` removes `|| true` suppressions from typecheck and audit gates.
- **Accessibility** — skip-to-content link, `role="main"`, `role="tab"` + `aria-selected` on nav, `aria-expanded` on hamburger, `role="alert"` on Toast error notifications.

#### Fixed
- Timer leaks in `DoctorView` (copyTimerRef), `StatusCard`, `UpdateView` — all `setTimeout`/`setInterval` handles cleaned up on unmount.
- 10 TypeScript errors in `ReleaseCard`, `BackupView`, `RestoreView` (props → store migration).
- `react-hooks/exhaustive-deps` warnings in `BackupView`, `RestoreView`, `UpdateView`.

---

## [0.2.1] — 2026 — *Registry & Winget Foundation*

### Emberbird Manager
- Initial Winget manifest submission (`WSABuilds.WSABuildsManager`).
- Release registry integration with `data/releases/releases.json`.
- Doctor scan (12 probes PRB-01 through PRB-12).
- Backup/Restore VHDX system.

---

## [0.2.0] — 2026 — *Emberbird Manager Initial Release*

### Emberbird Manager
- First public release as standalone Tauri v2 desktop application.
- WSA detection, status display, one-click install/update flow.
- Multi-edition support: Standard and Banking.
- NSIS installer packaging.
- Winget manifest: `WSABuilds.WSABuildsManager 0.2.0`.

---

## [Pre-0.2.0] — Legacy WSABuilds

- MagiskOnWSA lineage (MustardChef attribution preserved per Rule 12).
- WSABuilds packaging scripts and compatibility hub.
- Multiple WSA release generations: 2207 through 2407.
