import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

// QG-4 surfaced this the hard way. The E2E suite asserted the document title
// "Emberbird Manager" — matching tauri.conf.json's productName and window
// title — while index.html still shipped the superseded "WSABuilds Manager".
// Every surface that names the product must agree, so a rename can never leave
// one behind again. The assertion string is read out of the spec rather than
// duplicated here, so this is a real cross-check and not a second copy of the
// same constant.

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (rel) => readFileSync(path.join(ROOT, rel), 'utf8');

const PRODUCT_NAME = 'Emberbird Manager';
const SUPERSEDED_NAMES = ['WSABuilds Manager', 'WSA Manager'];

function documentTitle() {
  const match = read('index.html').match(/<title>\s*([^<]*?)\s*<\/title>/);
  assert.ok(match, 'index.html declares no <title>');
  return match[1];
}

test('the document title and the native window title agree', () => {
  const conf = JSON.parse(read('src-tauri/tauri.conf.json'));
  const doc = documentTitle();

  assert.equal(
    doc,
    conf.productName,
    'index.html <title> and tauri.conf.json productName disagree — the webview and the native window would name the product differently'
  );

  const windowTitles = (conf.app?.windows ?? []).map((w) => w.title).filter(Boolean);
  assert.ok(windowTitles.length, 'tauri.conf.json declares no window title');
  for (const title of windowTitles) {
    assert.equal(title, doc, 'a native window title disagrees with the document title');
  }
});

test('the E2E suite asserts the title the application actually ships', () => {
  const spec = read('e2e/app.spec.ts');
  const asserted = [...spec.matchAll(/page\.title\(\)\)\s*\.toBe\(\s*'([^']+)'\s*\)/g)].map((m) => m[1]);

  assert.ok(asserted.length, 'the E2E suite no longer asserts the document title');
  for (const title of asserted) {
    assert.equal(
      title,
      documentTitle(),
      'the E2E suite asserts a document title the application does not ship'
    );
  }
});

test('no shipped surface still declares a superseded product name', () => {
  const surfaces = [
    ['index.html', read('index.html')],
    ['src-tauri/tauri.conf.json', read('src-tauri/tauri.conf.json')],
  ];

  for (const [rel, body] of surfaces) {
    for (const stale of SUPERSEDED_NAMES) {
      assert.ok(
        !body.includes(stale),
        `${rel} still declares the superseded product name "${stale}"`
      );
    }
  }
});

test('the product name is the one the package identity uses', () => {
  const pkg = JSON.parse(read('package.json'));
  assert.ok(
    pkg.name.startsWith('emberbird'),
    `package name "${pkg.name}" does not match the advertised product name "${PRODUCT_NAME}"`
  );

  const conf = JSON.parse(read('src-tauri/tauri.conf.json'));
  assert.equal(pkg.version, conf.version, 'package.json and tauri.conf.json version disagree');
});
