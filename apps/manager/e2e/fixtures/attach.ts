/**
 * Pure helpers for attaching the E2E harness to the running application.
 *
 * Deliberately free of Playwright imports so the logic is unit-testable in
 * plain Node: the harness itself only runs on a machine with a compiled Tauri
 * build, which is not where these rules are worth checking.
 */

import { tmpdir } from 'node:os';
import { join } from 'node:path';

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

export function webview2DebugEnv(
  port: number = DEFAULT_CDP_PORT,
  profileBase: string = join(tmpdir(), 'emberbird-e2e-webview2'),
): Record<string, string> {
  return {
    WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS: `--remote-debugging-port=${port} --user-data-dir=${webview2ProfileDir(port, profileBase)}`,
  };
}

/**
 * Per-worker WebView2 profile directory. Reused CI runners can carry a stale
 * lock in the default profile folder under %LOCALAPPDATA%, and a locked
 * profile silently blocks WebView2 startup: the application process stays
 * alive (exit code none, signal none — observed on the 2026-09-22 CI run)
 * while no CDP endpoint ever appears. A fresh scratch directory removes that
 * failure class; the path must stay free of spaces for Chromium argument
 * parsing, which the OS temp dir guarantees on CI and typical dev hosts.
 */
export function webview2ProfileDir(
  port: number,
  base: string = join(tmpdir(), 'emberbird-e2e-webview2'),
): string {
  return join(base, `port-${port}`);
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

/**
 * How many trailing characters of the child's stdout/stderr the harness keeps
 * for failure diagnostics. Launch failures (missing WebView2 DLL, blocked
 * executable) print their cause in the first lines; the tail is enough.
 */
export const DIAGNOSTIC_TAIL_CHARS = 2_000;

/** Last `maxChars` characters of a captured stream, for failure diagnostics. */
export function tailOf(text: string | undefined, maxChars: number = DIAGNOSTIC_TAIL_CHARS): string {
  if (!text) return '';
  return text.length > maxChars ? text.slice(text.length - maxChars) : text;
}

/** What the harness observed about the spawned application process. */
export interface ChildObservation {
  exitCode: number | null;
  signal: NodeJS.Signals | null;
  stdoutTail?: string;
  stderrTail?: string;
}

/**
 * Explains why the application process ended before attaching. The 2026-09-22
 * CI failure was undiagnosable because the harness reported only the CDP
 * network error ("fetch failed") while the child's own words and exit code
 * went unobserved — the run log showed the endpoint check failing for 45
 * seconds with no hint whether the app was alive.
 */
export function describeChildExit(info: ChildObservation): string {
  const cause =
    info.exitCode !== null
      ? `exited with code ${info.exitCode}`
      : info.signal !== null
        ? `was killed by signal ${info.signal}`
        : 'ended';
  const lines = [`The application process ${cause} before exposing a CDP endpoint.`];
  for (const [name, tail] of [
    ['stdout', info.stdoutTail],
    ['stderr', info.stderrTail],
  ] as const) {
    const text = (tail ?? '').trim();
    lines.push(`${name}: ${text ? text : '<empty>'}`);
  }
  return lines.join('\n');
}
