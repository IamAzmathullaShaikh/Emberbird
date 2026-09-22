import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

import {
  DEFAULT_CDP_PORT,
  cdpEndpoint,
  describePages,
  isAttachedToApp,
  unattachedPageMessage,
  webview2DebugEnv,
  workerCdpPort,
} from '../e2e/fixtures/attach.ts';

// QG-4 was red because the suite asserted against a page Playwright had opened
// itself: `page.title()` returned "" and every locator found nothing, so nine
// tests failed for a reason unrelated to the product. These guards pin the two
// halves of that defect — the attach rule, and the harness wiring that decides
// whether a real window is ever reached.

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (rel) => readFileSync(path.join(ROOT, rel), 'utf8');

test('a blank or failed page is reported as detached', () => {
  for (const url of ['', '   ', 'about:blank', 'data:text/html,<p>x</p>', 'file:///C:/app/index.html', 'chrome-error://chromewebdata/']) {
    assert.equal(isAttachedToApp(url), false, `${JSON.stringify(url)} must not count as attached`);
  }
});

test('absent or malformed URLs are reported as detached rather than throwing', () => {
  for (const url of [null, undefined, 42, {}]) {
    assert.equal(isAttachedToApp(url), false);
  }
});

test('a served application document counts as attached', () => {
  for (const url of ['http://tauri.localhost/', 'https://tauri.localhost/index.html', 'http://localhost:5173/']) {
    assert.equal(isAttachedToApp(url), true, `${JSON.stringify(url)} must count as attached`);
  }
});

test('the detach diagnostic names the cause and the remedy', () => {
  const message = unattachedPageMessage('about:blank', 'C:\\build\\Emberbird Manager.exe');
  assert.match(message, /about:blank/);
  assert.match(message, /EMBERBIRD_E2E_APP/);
  assert.match(message, /tauri build/);
});

test('each worker gets its own debugging port', () => {
  assert.equal(workerCdpPort(0), DEFAULT_CDP_PORT);
  assert.equal(workerCdpPort(1), DEFAULT_CDP_PORT + 1);
  assert.notEqual(workerCdpPort(0), workerCdpPort(1));
  for (const malformed of [undefined, -1, 1.5, NaN]) {
    assert.equal(workerCdpPort(malformed), DEFAULT_CDP_PORT);
  }
});

test('the debugging switch the application is launched with matches the endpoint', () => {
  const env = webview2DebugEnv(9333);
  assert.match(
    env.WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS,
    /--remote-debugging-port=9333/,
  );
  assert.match(
    env.WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS,
    /--user-data-dir=/,
    'a fresh profile dir must be passed or a stale CI profile lock silently blocks WebView2 startup',
  );
  assert.equal(cdpEndpoint(9333), 'http://127.0.0.1:9333');
});

test('distinct workers get distinct WebView2 profile directories', async () => {
  const { webview2ProfileDir } = await import('../e2e/fixtures/attach.ts');
  const base = '/scratch/profiles';
  assert.notEqual(
    webview2ProfileDir(9222, base),
    webview2ProfileDir(9223, base),
  );
  assert.match(webview2ProfileDir(9222, base), /port-9222$/);
});

test('an empty page inventory is described honestly rather than hiding the fact', () => {
  assert.equal(describePages([]), '<no pages exposed over CDP>');
});

test('page inventory keeps real URLs and error pages verbatim, blanks marked', () => {
  const described = describePages(['about:blank', 'http://tauri.localhost/', null]);
  assert.match(described, /1\. about:blank/);
  assert.match(described, /2\. http:\/\/tauri\.localhost\//);
  assert.match(described, /3\. <blank>/);
});

/**
 * Comments may name what the harness deliberately avoids, so only executable
 * lines are checked. A raw `includes` matched the prose explaining the removal.
 */
function stripComments(source) {
  return source
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .split('\n')
    .filter((line) => !/^\s*(\/\/|#)/.test(line))
    .join('\n');
}

test('the harness never spawns a WebDriver bridge Playwright cannot speak', () => {
  assert.ok(
    !stripComments(read('e2e/fixtures/tauri.ts')).includes('tauri-driver'),
    'the harness spawns tauri-driver, which speaks WebDriver and cannot drive a Playwright page'
  );
  assert.ok(
    !stripComments(read('../../.github/workflows/manager-e2e.yml')).includes('tauri-driver'),
    'the E2E workflow installs tauri-driver, which nothing in the suite can use'
  );
});

test('every E2E spec takes its page from the attaching harness', () => {
  for (const spec of ['e2e/app.spec.ts', 'e2e/install-flow.spec.ts']) {
    const body = read(spec);
    assert.match(
      body,
      /from '\.\/fixtures\/tauri'/,
      `${spec} must import the attaching harness so its page is the application window`
    );
  }
});

test('the E2E workflow compiles the application the harness attaches to', () => {
  const workflow = read('../../.github/workflows/manager-e2e.yml');
  assert.match(workflow, /tauri build/, 'the E2E workflow must build the application before attaching');
});

// The binary-name drift that only a real CI build would have exposed:
// `tauri build --no-bundle` produces the crate name (emberbird-manager.exe),
// while the bundler may rename to the product name. Verified empirically
// 2026-09-22; these guards keep both names resolveable.

import { resolveAppBinary, APP_BINARY_CANDIDATES } from '../e2e/fixtures/attach.ts';

test('the harness resolves every binary name a release build may produce', () => {
  assert.ok(
    APP_BINARY_CANDIDATES.includes('emberbird-manager.exe'),
    'the crate-name binary produced by tauri build --no-bundle must be a candidate',
  );
  assert.ok(
    APP_BINARY_CANDIDATES.includes('Emberbird Manager.exe'),
    'the product-name binary a bundled build may produce must be a candidate',
  );
});

test('with no build present the resolver still names a concrete expected path', () => {
  const resolved = resolveAppBinary('C:/app/target/release', () => false, null);
  assert.ok(
    resolved.endsWith(APP_BINARY_CANDIDATES[0]),
    `expected the primary candidate, got: ${resolved}`,
  );
});

test('an existing crate-name binary wins when the product-name binary is absent', () => {
  const resolved = resolveAppBinary(
    'C:/app/target/release',
    (candidate) => candidate.endsWith('emberbird-manager.exe'),
    null,
  );
  assert.ok(resolved.endsWith('emberbird-manager.exe'));
});

test('the E2E binary override always wins over candidates', () => {
  assert.equal(
    resolveAppBinary('C:/app/target/release', () => true, 'C:/custom/app.exe'),
    'C:/custom/app.exe',
  );
});

test('stream tails keep only the last DIAGNOSTIC_TAIL_CHARS characters', async () => {
  const { tailOf, DIAGNOSTIC_TAIL_CHARS: limit } = await import('../e2e/fixtures/attach.ts');
  assert.equal(tailOf(undefined), '');
  assert.equal(tailOf(''), '');
  assert.equal(tailOf('short'), 'short');
  const long = 'x'.repeat(limit + 10);
  assert.equal(tailOf(long).length, limit);
});

test('a child exit code is reported with its own output, not just the CDP error', async () => {
  const { describeChildExit } = await import('../e2e/fixtures/attach.ts');
  const text = describeChildExit({
    exitCode: 0xc0000135,
    signal: null,
    stdoutTail: '',
    stderrTail: 'Failed to load WebView2Loader.dll',
  });
  assert.match(text, /exited with code/);
  assert.match(text, /Failed to load WebView2Loader\.dll/);
});

test('a signal kill and a silent death are both explained', async () => {
  const { describeChildExit } = await import('../e2e/fixtures/attach.ts');
  assert.match(
    describeChildExit({ exitCode: null, signal: 'SIGTERM', stdoutTail: 'boot ok', stderrTail: '' }),
    /killed by signal SIGTERM/,
  );
  const silent = describeChildExit({ exitCode: null, signal: null, stdoutTail: '', stderrTail: '' });
  assert.match(silent, /ended before exposing a CDP endpoint/);
  assert.match(silent, /stdout: <empty>/);
});

test('the harness drains child stdio and fails fast on child exit', () => {
  const source = read('e2e/fixtures/tauri.ts');
  assert.match(
    source,
    /captureChildStreams/,
    'waitForCdp must drain stdout/stderr or a chatty app blocks on a full pipe and never serves CDP',
  );
  assert.match(
    source,
    /child\.exitCode !== null \|\| child\.signalCode !== null/,
    'the CDP poll must notice a dead child instead of spinning out its full timeout',
  );
  assert.match(
    source,
    /catch \(error\) \{[\s\S]*?child\.kill\(\);[\s\S]*?throw error;/,
    'a failed launch must not leak the spawned application process',
  );
});
