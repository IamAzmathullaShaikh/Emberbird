/**
 * Pure helpers for attaching the E2E harness to the running application.
 *
 * Deliberately free of Playwright imports so the logic is unit-testable in
 * plain Node: the harness itself only runs on a machine with a compiled Tauri
 * build, which is not where these rules are worth checking.
 */

/**
 * WebView2 is Chromium-based and therefore honours Chromium's debugging
 * switch, which is how Playwright reaches the application at all.
 */
export const DEFAULT_CDP_PORT = 9222;

/**
 * Binary names a release build may produce: `tauri build`'s bundler renames
 * to the product name on some paths, while `--no-bundle` and plain cargo
 * leave the crate name (`emberbird-manager.exe`). Verified empirically
 * 2026-09-22: `npx tauri build --no-bundle` prints "Built application at:
 * ...emberbird-manager.exe".
 */
export const APP_BINARY_CANDIDATES = ['Emberbird Manager.exe', 'emberbird-manager.exe'] as const;

/**
 * Resolve the application binary: the E2E override wins, then the first
 * candidate that exists. With no build at all the primary candidate is
 * returned so diagnostics name a concrete expected path.
 */
export function resolveAppBinary(
  releaseDir: string,
  exists: (candidate: string) => boolean,
  override: string | null,
  join: (dir: string, name: string) => string = (dir, name) => `${dir}/${name}`,
): string {
  if (override) return override;
  for (const name of APP_BINARY_CANDIDATES) {
    const candidate = join(releaseDir, name);
    if (exists(candidate)) return candidate;
  }
  return join(releaseDir, APP_BINARY_CANDIDATES[0]);
}

/**
 * Pages that are not the application: a detached browser, or a load failure.
 * Playwright's own fixtures hand every test a blank page, and asserting UI
 * against one produces failures that look like product bugs.
 */
const NON_APP_PAGE_PREFIXES = ['about:', 'data:', 'chrome-error:', 'edge-error:', 'file:'];

export function webview2DebugEnv(port: number = DEFAULT_CDP_PORT): Record<string, string> {
  return { WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS: `--remote-debugging-port=${port}` };
}

export function cdpEndpoint(port: number = DEFAULT_CDP_PORT): string {
  return `http://127.0.0.1:${port}`;
}

/**
 * Each Playwright worker launches its own application instance, so each needs
 * its own debugging port. Defensive about the index because Playwright omits it
 * in some single-worker configurations.
 */
export function workerCdpPort(parallelIndex: number | undefined, base: number = DEFAULT_CDP_PORT): number {
  const index = typeof parallelIndex === 'number' && Number.isInteger(parallelIndex) && parallelIndex > 0
    ? parallelIndex
    : 0;
  return base + index;
}

/**
 * True only when a page is showing a real document. A blank or failed page is
 * reported as detached so the harness can refuse to run rather than produce
 * nine unrelated assertion failures.
 */
export function isAttachedToApp(url: string | null | undefined): boolean {
  if (typeof url !== 'string') return false;
  const value = url.trim().toLowerCase();
  if (value === '') return false;
  return !NON_APP_PAGE_PREFIXES.some((prefix) => value.startsWith(prefix));
}

/**
 * How long the harness waits for the application's webview to expose a real
 * document. The CDP endpoint answers before the webview finishes its first
 * navigation, so "endpoint is up" and "app content exists" are different events.
 */
export const APP_PAGE_TIMEOUT_MS = 45_000;

/** Human-readable inventory of the pages a context exposed, for diagnostics. */
export function describePages(urls: ReadonlyArray<string | null | undefined>): string {
  if (urls.length === 0) return '<no pages exposed over CDP>';
  return urls
    .map((url, index) => `${index + 1}. ${url && url.trim() ? url : '<blank>'}`)
    .join('; ');
}

/** Actionable failure text, because "element not found" explains nothing here. */
export function unattachedPageMessage(url: string | null | undefined, appPath: string): string {
  return [
    `The E2E harness is not attached to the application (page URL: ${url && url.trim() ? url : '<none>'}).`,
    'Asserting UI against a blank page can only fail for the wrong reason.',
    `Expected a compiled build at: ${appPath}`,
    'Build it with `npx tauri build`, or set EMBERBIRD_E2E_APP to the executable path.',
  ].join('\n');
}
