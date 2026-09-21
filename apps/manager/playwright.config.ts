import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 120_000,
  retries: 1,
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
