/**
 * Playwright harness for the Emberbird Manager Tauri application.
 *
 * The application is a native window, so Playwright cannot launch it the way it
 * launches a browser. Instead the executable is started as a process with
 * WebView2's remote debugging endpoint enabled, and Playwright attaches over
 * CDP. The tests therefore drive the real window and the real Rust IPC bridge.
 *
 * `tauri-driver` is deliberately not used: it speaks WebDriver, which Playwright
 * cannot. Installing it changed nothing except CI time — the previous harness
 * spawned it in a fixture no spec requested, while the tests asserted against
 * Playwright's own blank page.
 *
 * Requires a compiled build: `npx tauri build`.
 */
import { chromium, test as base, type Browser, type Page } from '@playwright/test';
import { spawn, type ChildProcess } from 'node:child_process';
import { existsSync, mkdirSync } from 'node:fs';
import path from 'node:path';

import {
  APP_PAGE_TIMEOUT_MS,
  DIAGNOSTIC_TAIL_CHARS,
  cdpEndpoint,
  describeChildExit,
  describePages,
  isAttachedToApp,
  resolveAppBinary,
  unattachedPageMessage,
  webview2DebugEnv,
  webview2ProfileDir,
  workerCdpPort,
  type ChildObservation,
} from './attach';

const RELEASE_DIR = path.resolve('src-tauri', 'target', 'release');

export function resolveAppPath(): string {
  return resolveAppBinary(
    RELEASE_DIR,
    (candidate) => existsSync(candidate),
    process.env.EMBERBIRD_E2E_APP?.trim() || null,
  );
}

/**
 * Keeps the child's stdout/stderr drained and their last characters captured.
 * A process that writes more than the OS pipe buffer while nobody reads blocks
 * forever on the write and never reaches the webview — so the streams must
 * never sit full, even though their content is only needed for diagnostics.
 */
function captureChildStreams(child: ChildProcess): () => ChildObservation {
  let stdoutTail = '';
  let stderrTail = '';
  child.stdout?.on('data', (chunk: Buffer | string) => {
    stdoutTail = (stdoutTail + chunk.toString()).slice(-DIAGNOSTIC_TAIL_CHARS);
  });
  child.stderr?.on('data', (chunk: Buffer | string) => {
    stderrTail = (stderrTail + chunk.toString()).slice(-DIAGNOSTIC_TAIL_CHARS);
  });
  return () => ({
    exitCode: child.exitCode,
    signal: child.signalCode,
    stdoutTail,
    stderrTail,
  });
}

/** Poll until the application's WebView2 opens its debugging endpoint. */
async function waitForCdp(
  port: number,
  child: ChildProcess,
  observe: () => ChildObservation,
  timeoutMs = 45_000,
): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  let lastError = 'not listening';
  while (Date.now() < deadline) {
    if (child.exitCode !== null || child.signalCode !== null) {
      // The application died before it could serve CDP. Its own words (a
      // missing DLL, a policy block, a panic) explain the failure far better
      // than the endpoint poll's network error would.
      throw new Error(describeChildExit(observe()));
    }
    try {
      const response = await fetch(`${cdpEndpoint(port)}/json/version`);
      if (response.ok) return;
      lastError = `HTTP ${response.status}`;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(
    [
      `The application never exposed a CDP endpoint on ${cdpEndpoint(port)} (${lastError}).`,
      `Process status after ${timeoutMs}ms: exit code ${child.exitCode ?? 'none'}, signal ${child.signalCode ?? 'none'}.`,
    ].join('\n')
  );
}

interface AppSession {
  appPath: string;
  child: ChildProcess;
  browser: Browser;
  page: Page;
}

async function launchApplication(appPath: string, port: number): Promise<AppSession> {
  if (!existsSync(appPath)) {
    throw new Error(
      `No compiled application at ${appPath}. Run \`npx tauri build\`, or set EMBERBIRD_E2E_APP to the executable path.`
    );
  }

  // The per-worker profile directory must exist before WebView2 starts;
  // a missing parent directory is another silent-startup failure mode.
  mkdirSync(webview2ProfileDir(port), { recursive: true });

  const child = spawn(appPath, [], {
    stdio: 'pipe',
    env: { ...process.env, ...webview2DebugEnv(port) },
  });
  const observe = captureChildStreams(child);

  try {
    await waitForCdp(port, child, observe);

    const browser = await chromium.connectOverCDP(cdpEndpoint(port));
    const context = browser.contexts()[0];
    if (!context) {
      await browser.close().catch(() => {});
      throw new Error('Attached to CDP but it exposed no browser context.');
    }

    /**
     * The CDP endpoint answers before the webview has finished its first
     * navigation, so `context.pages()[0]` can still be about:blank. Take the
     * first page that is a real document, re-reading the context's page list
     * each poll instead of caching the startup snapshot.
     */
    const deadline = Date.now() + APP_PAGE_TIMEOUT_MS;
    let page: Page | null = null;
    let lastUrls: string[] = [];
    while (Date.now() < deadline) {
      const candidates = context.pages();
      lastUrls = candidates.map((candidate) => candidate.url());
      const found = candidates.find((candidate) => isAttachedToApp(candidate.url()));
      if (found) {
        page = found;
        break;
      }
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
    if (!page) {
      throw new Error(
        [
          `The application's webview never exposed a real document within ${APP_PAGE_TIMEOUT_MS}ms.`,
          `Pages over CDP: ${describePages(lastUrls)}`,
          `Expected a compiled build at: ${appPath}`,
        ].join('\n')
      );
    }
    return { appPath, child, browser, page };
  } catch (error) {
    // Every failure after spawn leaves the launched process behind; release
    // it so a failed worker does not leak a headless application.
    child.kill();
    throw error;
  }
}

export const test = base.extend<{ assertAppAttached: void }, { appSession: AppSession }>({
  // Worker-scoped: launching the application per test would dominate the run.
  appSession: [
    async ({}, use, workerInfo) => {
      const session = await launchApplication(resolveAppPath(), workerCdpPort(workerInfo.parallelIndex));
      try {
        await use(session);
      } finally {
        await session.browser.close().catch(() => {});
        session.child.kill();
      }
    },
    { scope: 'worker' },
  ],

  /** The application window itself, not a page Playwright opened. */
  page: async ({ appSession }, use) => {
    await use(appSession.page);
  },

  /**
   * Refuses to run against a blank page. Without this, a disconnected harness
   * fails with "element not found" and reads like a product defect.
   */
  assertAppAttached: [
    async ({ page, appSession }, use) => {
      const url = page.url();
      if (!isAttachedToApp(url)) {
        throw new Error(unattachedPageMessage(url, appSession.appPath));
      }
      await use();
    },
    { auto: true },
  ],
});

export { expect } from '@playwright/test';
