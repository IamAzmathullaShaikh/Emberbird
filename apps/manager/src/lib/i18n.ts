/**
 * Emberbird i18n — string extraction and locale resolution.
 * Phase 1: English-only. Infrastructure ready for future locales.
 * Rule 17 (Anti-Hardcoding): no user-facing English strings hardcoded in component logic.
 */

export type Locale = 'en';
export type TranslationKey = keyof typeof EN_STRINGS;

export const EN_STRINGS = {
  'nav.dashboard': 'Dashboard',
  'nav.updates': 'Updates',
  'nav.backup': 'Backup',
  'nav.restore': 'Restore',
  'nav.doctor': 'Doctor',
  'nav.licenses': 'Licenses',
  'nav.menu.label': 'Navigation menu',
  'action.refresh': 'Refresh',
  'action.retry': 'Retry',
  'action.cancel': 'Cancel',
  'action.confirm': 'Confirm',
  'action.copy': 'Copy',
  'action.close': 'Close',
  'action.scan': 'Run Scan',
  'status.installed': 'Installed',
  'status.not_installed': 'Not Installed',
  'status.outdated': 'Installed (Outdated)',
  'status.partial': 'Partially Installed',
  'status.unknown': 'Unknown',
  'status.running': 'Running',
  'status.stopped': 'Stopped',
  'error.boundary.title': '{label} encountered an error',
  'error.boundary.retry': 'Retry',
  'error.boundary.copy_diagnostic': 'Copy Diagnostic',
  'error.ipc_not_available': 'Tauri backend not detected',
  'install.wizard.title': 'Quick Setup Wizard',
  'install.edition.standard': 'Standard Edition',
  'install.edition.banking': 'Banking Edition',
  'install.button.install': 'Install',
  'doctor.title': 'Ember Doctor',
  'doctor.scan.run': 'Run Full Scan',
  'doctor.probe.copy_fix': 'Copy Fix',
  'toast.dismiss': 'Dismiss',
  'loading.status': 'Loading status\u2026',
  'loading.releases': 'Querying Release Registry\u2026',
} as const;

let currentLocale: Locale = 'en';
const LOCALE_STRINGS: Record<Locale, typeof EN_STRINGS> = { en: EN_STRINGS };

export function getLocale(): Locale { return currentLocale; }
export function setLocale(locale: Locale): void { currentLocale = locale; }

export function t(key: TranslationKey, vars?: Record<string, string>): string {
  let str = LOCALE_STRINGS[currentLocale][key] as string;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      str = str.replace(`{${k}}`, v);
    }
  }
  return str;
}

export function detectAndSetLocale(): void {
  // OS locale detection — currently English only; extend when more locales ship
  const preferred = typeof navigator !== 'undefined' ? navigator.language.split('-')[0] : 'en';
  void preferred; // future: setLocale(preferred as Locale)
}
