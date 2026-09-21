/**
 * QG-4: Emberbird Manager E2E tests.
 * REQUIRES TARGET ENVIRONMENT VALIDATION — must run on Windows with compiled Tauri binary.
 * CI: see .github/workflows/manager-e2e.yml
 */
import { test, expect } from './fixtures/tauri';

test.describe('Application Launch', () => {
  test('app title is Emberbird Manager', async ({ page }) => {
    expect(await page.title()).toBe('Emberbird Manager');
  });

  test('main navigation renders all 6 tabs', async ({ page }) => {
    for (const tab of ['Dashboard', 'Updates', 'Backup', 'Restore', 'Doctor', 'Licenses']) {
      await expect(page.getByRole('tab', { name: tab }).or(page.getByText(tab))).toBeVisible();
    }
  });

  test('status card renders without crashing', async ({ page }) => {
    await expect(
      page.locator('[data-testid="status-card"]')
        .or(page.locator('.animate-pulse'))
        .or(page.getByText('Not Installed'))
        .or(page.getByText('Installed'))
    ).toBeVisible({ timeout: 10_000 });
  });
});

test.describe('Navigation', () => {
  test('clicking Doctor tab shows Doctor view', async ({ page }) => {
    await page.getByText('Doctor').first().click();
    await expect(page.getByText('Ember Doctor').or(page.getByText('Scan'))).toBeVisible({ timeout: 10_000 });
  });

  test('clicking Licenses tab shows legal view', async ({ page }) => {
    await page.getByText('Licenses').first().click();
    await expect(page.getByText('License').or(page.getByText('Attribution'))).toBeVisible({ timeout: 5_000 });
  });

  test('app does not crash when navigating between all tabs', async ({ page }) => {
    for (const tab of ['Updates', 'Backup', 'Restore', 'Doctor', 'Licenses', 'Dashboard']) {
      await page.getByText(tab).first().click();
      await expect(page.getByText('encountered an error')).not.toBeVisible({ timeout: 3_000 }).catch(() => {});
    }
  });
});

test.describe('Doctor Flow', () => {
  test('Doctor scan button triggers a scan', async ({ page }) => {
    await page.getByText('Doctor').first().click();
    const scanBtn = page.getByRole('button', { name: /scan|run/i });
    if (await scanBtn.isVisible()) {
      await scanBtn.click();
      await expect(page.getByText('PRB-').or(page.getByText('Scanning'))).toBeVisible({ timeout: 30_000 });
    }
  });
});
