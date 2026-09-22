/**
 * QG-4: Install flow E2E.
 *
 * Ground truth (verified against source and the running app): the Quick
 * Setup panel — edition cards, resolved registry asset, wizard entry — is
 * rendered ONLY while the runtime state is `NOT_INSTALLED`
 * (QuickSetupPanel.tsx returns null otherwise). Rather than assert one
 * host's state, this spec asserts the contract itself: panel visible iff
 * the status surface reports "Not Installed". A clean CI runner (nothing
 * installed) exercises the full branch; an installed host exercises the
 * inverse.
 *
 * REQUIRES TARGET ENVIRONMENT VALIDATION — Windows + compiled Tauri binary.
 */
import { test, expect } from './fixtures/tauri';

test.describe('Install Flow', () => {
  test('Quick Setup panel visibility matches the reported runtime state', async ({ page }) => {
    // The worker-scoped app session shares one page; StatusCard only mounts
    // on the Dashboard tab. Navigate deterministically before asserting.
    await page.getByRole('tab', { name: 'Dashboard', exact: true }).click();
    await expect(page.getByTestId('status-card')).toBeVisible({ timeout: 15_000 });

    // The status surface renders the state label verbatim (state.ts labels).
    // Exact match so "Partially Installed"/"Installed (Outdated)" don't hit.
    const notInstalled = await page
      .getByText('Not Installed', { exact: true })
      .first()
      .isVisible()
      .catch(() => false);

    const quickSetupHeading = page.getByRole('heading', {
      name: 'Quick Setup & One-Click Installer',
    });

    if (notInstalled) {
      // Full branch: the panel and both registry edition cards render.
      await expect(quickSetupHeading).toBeVisible({ timeout: 10_000 });
      await expect(page.getByText('Standard Edition', { exact: true })).toBeVisible();
      await expect(page.getByText('Banking Edition', { exact: true })).toBeVisible();
    } else {
      // Inverse contract: no phantom installer for a present runtime —
      // the panel must not render at all (Zero-Mock law).
      await expect(quickSetupHeading).toHaveCount(0);
    }
  });
});
