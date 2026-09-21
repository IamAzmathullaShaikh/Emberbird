import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const websiteRoot = path.resolve(import.meta.dirname, '..');

function read(rel) {
  return fs.readFileSync(path.join(websiteRoot, rel), 'utf8');
}

function astroSources() {
  const srcRoot = path.join(websiteRoot, 'src');
  return fs
    .readdirSync(srcRoot, { recursive: true })
    .map((entry) => path.join('src', entry.toString()))
    .filter((rel) => rel.endsWith('.astro'))
    .map((rel) => ({ rel, content: read(rel) }));
}

// Pagefind switches to marker-only indexing the moment *any* page declares
// `data-pagefind-body`: from then on it indexes only pages carrying the marker.
// Declaring it on two isolated elements therefore silently excluded the other 16
// pages, including every documentation page. It belongs on the shared content
// root, exactly once.
test('data-pagefind-body is declared once, on the shared layout content root', () => {
  const layoutRel = path.join('src', 'layouts', 'Layout.astro');
  const layout = read(layoutRel);
  const matches = layout.match(/data-pagefind-body(?=[\s>])/g) || [];
  assert.equal(matches.length, 1, `${layoutRel} must declare data-pagefind-body exactly once`);

  const offenders = astroSources()
    .filter(({ rel, content }) => rel !== layoutRel && /data-pagefind-body(?=[\s>])/.test(content))
    .map(({ rel }) => rel);
  assert.deepEqual(
    offenders,
    [],
    'a second data-pagefind-body nests an index region and re-triggers marker-only indexing; ' +
      'the layout already marks the content root for every page'
  );
});

// The loader must stay out of the bundler's hands. `pagefind.js` is written into
// dist/ by the post-build step, so a bundled dynamic import gets wrapped as
// `__vitePreload(() => import(spec), __VITE_PRELOAD__)`, and with a computed
// specifier Vite never substitutes that identifier — a ReferenceError that the
// loader's own catch used to swallow, leaving a silently dead search.
test('the pagefind loader is inlined verbatim so the bundler cannot rewrite it', () => {
  const modal = read(path.join('src', 'components', 'SearchModal.astro'));

  const scriptBlock = modal.match(/<script is:inline>([\s\S]*?)<\/script>/);
  assert.ok(
    scriptBlock,
    'the search loader must use is:inline: Astro emits it untouched, whereas a processed script is bundled'
  );

  // Only the executable body is analysed, not the surrounding prose about it.
  const loader = scriptBlock[1];
  const specifiers = [...loader.matchAll(/\bimport\s*\(([^)]*)\)/g)].map((m) => m[1].trim());

  assert.equal(specifiers.length, 1, 'expected exactly one dynamic import in the loader');
  // The previous loader computed the specifier with `['/pagefind/pagefind.js'].join('')`
  // to defeat static analysis, which is precisely what made Vite emit an
  // undefined __VITE_PRELOAD__ reference. A plain string literal cannot be
  // rewritten that way.
  assert.equal(
    specifiers[0],
    "'/pagefind/pagefind.js'",
    `the index must be imported by a plain string-literal specifier, got: ${specifiers[0]}`
  );
});

// Verifies the indexing contract end to end against a real build. `npm test` runs
// before the build, so locally this skips when dist/ is absent; the source guards
// above always run. Set PAGEFIND_REQUIRE_BUILD=1 (as the deploy workflow does in
// its post-build verification step) to demand a build and fail loudly without
// one, which is what stops this gate from passing vacuously in CI.
const BUILD_REQUIRED = process.env.PAGEFIND_REQUIRE_BUILD === '1';

test('every built page is present in the pagefind index', (t) => {
  const distDir = path.join(websiteRoot, 'dist');
  const entryFile = path.join(distDir, 'pagefind', 'pagefind-entry.json');
  if (!fs.existsSync(entryFile)) {
    if (BUILD_REQUIRED) {
      assert.fail(
        `PAGEFIND_REQUIRE_BUILD is set but no search index exists at ${entryFile}. ` +
          'Run `npm run build` first: the site would otherwise ship with dead search.'
      );
    }
    t.skip('no dist/ build present; run `npm run build` first');
    return;
  }

  const htmlPages = fs
    .readdirSync(distDir, { recursive: true })
    .map((entry) => entry.toString())
    .filter((rel) => rel.endsWith('.html'));

  const entry = JSON.parse(fs.readFileSync(entryFile, 'utf8'));
  const pageCount = Object.values(entry.languages).reduce((sum, lang) => sum + lang.page_count, 0);

  assert.ok(htmlPages.length > 0, 'expected at least one built HTML page');
  assert.equal(
    pageCount,
    htmlPages.length,
    `pagefind indexed ${pageCount} page(s) but ${htmlPages.length} HTML page(s) were built. ` +
      'A page is missing from search — check that it renders through Layout.astro, whose ' +
      'data-pagefind-body marker is what opts a page in. Exclude a page deliberately with ' +
      'data-pagefind-ignore rather than letting it drop out silently.'
  );
});
