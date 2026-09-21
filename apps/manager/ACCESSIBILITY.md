# Emberbird Manager Accessibility Checklist

## Automated Tests (CI-verified)
- [x] axe-core scan: 0 violations on all UI primitive components (Badge, Button, Alert, Spinner, Card)
- [x] axe-core scan: 0 violations on StageProgressBar
- [x] axe-core scan: 0 violations on all component variants
- [x] `aria-valuenow`, `aria-valuemin`, `aria-valuemax` on all progress bars
- [x] `role="alert"` on error notifications (Toast, Alert)
- [x] `role="status"` on Spinner
- [x] `role="dialog"` + `aria-modal` on InstallerWizard modal
- [x] `role="tab"` + `aria-selected` on navigation tabs
- [x] `aria-expanded` + `aria-label` on hamburger menu button
- [x] Skip-to-main-content link (`sr-only focus:not-sr-only`)
- [x] `role="main"` + `id="main-content"` on page body
- [x] `prefers-reduced-motion` CSS support
- [x] `forced-colors: active` (Windows High Contrast) CSS support

## Manual Tests (requires hardware)
- [ ] NVDA + Chrome: full keyboard navigation through all 6 tabs
- [ ] NVDA + Chrome: Install Wizard modal keyboard trap (Tab cycles inside modal)
- [ ] NVDA + Chrome: Toast notifications announced on appearance
- [ ] Narrator + Edge: equivalent coverage
- [ ] Windows Magnifier: no content clipped at 200% zoom
- [ ] High Contrast mode: all text/border contrast verified visually

## WCAG 2.1 AA Compliance Status
| Criterion | Status | Notes |
|---|---|---|
| 1.1.1 Non-text Content | ✅ Automated | Icon buttons have aria-label |
| 1.3.1 Info and Relationships | ✅ Automated | Semantic roles on all UI |
| 1.3.3 Sensory Characteristics | ✅ Automated | Not relying on color alone |
| 1.4.1 Use of Color | ✅ Automated | Status uses icon + color |
| 1.4.4 Resize Text | ⚠️ Manual | Test at 200% zoom |
| 1.4.11 Non-text Contrast | ✅ Automated | axe-core (color-contrast advisory) |
| 2.1.1 Keyboard | ✅ Automated | All interactive elements keyboard-accessible |
| 2.1.2 No Keyboard Trap | ⚠️ Manual | Modal focus trap needs NVDA verification |
| 2.4.1 Bypass Blocks | ✅ Automated | Skip-to-content link |
| 2.4.3 Focus Order | ⚠️ Manual | Tab order verification |
| 4.1.2 Name, Role, Value | ✅ Automated | axe-core validates ARIA |
| 4.1.3 Status Messages | ✅ Automated | aria-live on notifications |
