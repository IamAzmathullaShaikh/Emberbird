/**
 * Tauri WebDriver fixture for Playwright E2E tests.
 * 
 * Requires: a compiled release build + `tauri-driver` installed globally.
 * Build: `npm run tauri build` before running E2E tests.
 */
import { test as base } from '@playwright/test';
import { spawn } from 'child_process';
import path from 'path';

export interface TauriFixtures {
  app: { pid: number; webdriverUrl: string };
}

export const test = base.extend<TauriFixtures>({
  app: async ({}, use) => {
    const WEBDRIVER_PORT = 4444;
    const driver = spawn('tauri-driver', ['--port', String(WEBDRIVER_PORT)], { stdio: 'pipe' });

    await new Promise<void>((resolve) => {
      driver.stdout?.on('data', (data: Buffer) => {
        if (data.toString().includes('listening')) resolve();
      });
      setTimeout(resolve, 3000);
    });

    await use({ pid: driver.pid ?? 0, webdriverUrl: `http://localhost:${WEBDRIVER_PORT}` });
    driver.kill();
  },
});

export { expect } from '@playwright/test';
