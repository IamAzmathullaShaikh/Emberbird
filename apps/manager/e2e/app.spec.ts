/**
 * QG-4: Emberbird Manager E2E tests.
 *
 * Every locator here is anchored to verified product reality (source-traced
 * and probe-dumped against the compiled binary): tab labels come from
 * `Header.tsx` TABS, headings from the view components, the status card hook
 * from `StatusCard.tsx`. No `.or(...)` fallback soup — a strict-mode
 * violation is how the previous generation of specs died.
 *
 * REQUIRES TARGET ENVIRONMENT VALIDATION — must run on Windows with a
 * compiled Tauri binary (`custom-protocol` build; plain `cargo build` bakes
 * in the devUrl and the webview lands on chrome-error).
 * CI: see .github/workflows/manager-e2e.yml
 */
import { test, expect } from './fixtures/tauri';

/** Exact tab labels — Header.tsx TABS is the single source of truth. */
const TABS = ['Dashboard', 'Updates', 'Backups', 'Restore', 'Doctor', 'Licenses'] as const;

test.describe('Application Launch', () => {
  test('app title is Emberbird Manager', async ({ page }) => {
    expect(await page.title()).toBe('Emberbird Manager');
  });

  test('main navigation renders all 6 tabs', async ({ page }) => {
    for (const tab of TABS) {
      await expect(page.getByRole('tab', { name: tab, exact: true })).toBeVisible();
    }
  });

  test('status card renders without crashing', async ({ page }) => {
    // StatusCard carries a stable testid once the store probe resolves. The
    // transient pulse skeleton is NOT accepted as a terminal state: a card
    // that never mounts is a failure, not a loading state.
    await expect(page.getByTestId('status-card')).toBeVisible({ timeout: 15_000 });
  });

  test('the lifecycle badge renders the reconciled runtime state', async ({ page }) => {
    await page.getByRole('tab', { name: 'Dashboard', exact: true }).click();
    await expect(page.getByTestId('lifecycle-badge')).toBeVisible({ timeout: 15_000 });
    // The badge must resolve past its loading placeholder: the backend runs
    // real reconciliation (persisted-trail recovery + live detection) before
    // answering. A badge stuck on "Checking lifecycle…" means the IPC command
    // never returned — a failure, not a loading state.
    await expect(page.getByTestId('lifecycle-badge')).not.toHaveText('Checking lifecycle…', {
      timeout: 30_000,
    });
  });
});

test.describe('Navigation', () => {
  test('clicking Doctor tab shows the Ember Doctor view', async ({ page }) => {
    await page.getByRole('tab', { name: 'Doctor', exact: true }).click();
    // DoctorView renders the "Ember Doctor" heading in BOTH its loaded and
    // its scan-error states; only the initial in-flight state lacks it.
    await expect(page.getByRole('heading', { name: 'Ember Doctor' })).toBeVisible({
      timeout: 30_000,
    });
  });

  test('clicking Licenses tab shows the legal view', async ({ page }) => {
    await page.getByRole('tab', { name: 'Licenses', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Legal & Open Source Licenses' })).toBeVisible({
      timeout: 10_000,
    });
  });

  test('app does not crash when navigating between all tabs', async ({ page }) => {
    for (const tab of TABS) {
      await page.getByRole('tab', { name: tab, exact: true }).click();
      // ErrorBoundary renders "<label> encountered an error" on a crash.
      await expect(page.getByText('encountered an error')).not.toBeVisible();
    }
  });
});

test.describe('Doctor Flow', () => {
  test('initial diagnostic scan completes and leaves the loading state', async ({ page }) => {
    await page.getByRole('tab', { name: 'Doctor', exact: true }).click();
    // DoctorView auto-runs the scan on mount: "Running system diagnostics..."
    // must resolve into either the results board or the honest scan-error
    // card. A stuck spinner is a failure — the real scan takes seconds, not
    // minutes, so a long timeout here only fires on a genuine hang.
    await expect(page.getByText('Running system diagnostics...')).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByText('Running system diagnostics...')).toBeHidden({
      timeout: 60_000,
    });
    await expect(page.getByRole('heading', { name: 'Ember Doctor' })).toBeVisible();
  });
});
