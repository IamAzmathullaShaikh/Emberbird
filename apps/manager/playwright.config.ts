import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 120_000,
  retries: 1,
  // Each worker launches its own Emberbird instance against WebView2, so
  // parallel workers would race on the same user-data directory. One worker
  // keeps the gate deterministic.
  workers: 1,
  use: {
    trace: 'on-first-retry',
  },
  reporter: [['html', { outputFolder: 'e2e-report' }], ['list']],
  projects: [
    {
      name: 'emberbird-tauri',
      testMatch: '**/*.spec.ts',
    },
  ],
});
