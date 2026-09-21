/** QG-4: Install flow E2E. REQUIRES TARGET ENVIRONMENT VALIDATION. */
import { test, expect } from './fixtures/tauri';

test.describe('Install Flow', () => {
  test('Quick Setup Wizard section is visible on dashboard', async ({ page }) => {
    await expect(
      page.getByText('Quick Setup Wizard')
        .or(page.getByText('Standard Edition'))
        .or(page.getByText('Edition'))
    ).toBeVisible({ timeout: 10_000 });
  });

  test('edition selector shows Standard and Banking options', async ({ page }) => {
    await expect(page.getByText('Standard').first()).toBeVisible({ timeout: 5_000 });
    await expect(page.getByText('Banking').first()).toBeVisible({ timeout: 5_000 });
  });
});
