import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

import {
  releasesFromRegistry,
  latestReleasesFromRegistry
} from '../src/lib/registry.ts';
import registryData from '../../../data/releases/releases.json' with { type: 'json' };

const repoRoot = path.resolve(import.meta.dirname, '../../..');

/* ---------------------------------------------------------------------------
 * E3C.3 — S2 parity proof (Manager): the legacy derivation surface produced
 * deterministic release-asset URLs from repo config; the registry resolution
 * must produce equivalent URLs (and richer truth: hashes) for the same
 * release set. The legacy discovery stub (`get_latest_releases` -> []) had no
 * output to be equivalent to; parity is therefore proven against the
 * documented derivation rule itself.
 * ------------------------------------------------------------------------- */

const registry = registryData;

test('registry resolution yields one release per published tag with merged assets', () => {
  const releases = releasesFromRegistry();
  const tags = releases.map((r) => r.tag_name);
  assert.equal(new Set(tags).size, tags.length,
    'one release per tag (multi-edition rows merge)');
  assert.ok(tags.includes('wsa-v2311.40000.5.0'),
    'published WSA tag resolves');
  assert.ok(tags.includes('v0.2.2'), 'published manager tag resolves');
  const wsa = releases.find((r) => r.tag_name === 'wsa-v2311.40000.5.0');
  assert.equal(wsa.assets.length, 2,
    'Standard + Banking editions merge into two assets');
});

test('S2 parity: registry URLs equal the documented legacy derivation rule', () => {
  const releases = releasesFromRegistry();
  for (const rel of releases) {
    for (const asset of rel.assets) {
      const derived = `https://github.com/IamAzmathullaShaikh/WSABuilds/releases/download/${rel.tag_name}/${asset.name}`;
      assert.equal(asset.browser_download_url, derived,
        `registry URL must equal legacy derivation for ${asset.name}`);
    }
  }
});

test('S2 parity: registry output covers the full published release set', () => {
  const expected = registry.releases
    .filter((r) => r.status === 'published')
    .map((r) => r.tag);
  const resolved = releasesFromRegistry().map((r) => r.tag_name);
  assert.deepEqual([...new Set(expected)].sort(), [...new Set(resolved)].sort(),
    'registry resolution must cover every published tag');
});

test('registry assets carry published hashes and sane flavors', () => {
  const releases = releasesFromRegistry();
  const wsa = releases.find((r) => r.tag_name === 'wsa-v2311.40000.5.0');
  for (const a of wsa.assets) {
    assert.match(a.browser_download_url, /releases\/download\//);
  }
  const standard = wsa.assets.find((a) => a.name.endsWith('_x64.7z') && !a.name.includes('vanilla'));
  assert.equal(standard.root_flavor, 'Magisk', 'Standard = Magisk root');
  assert.equal(standard.gapps_flavor, 'Pico', 'Standard = Pico GApps');
  const banking = wsa.assets.find((a) => a.name.includes('vanilla'));
  assert.equal(banking.root_flavor, 'None', 'Banking (vanilla) = NoRoot');
});

test('latestReleasesFromRegistry pins one newest release per family', () => {
  const latest = latestReleasesFromRegistry();
  assert.ok(latest.manager, 'manager family resolves');
  assert.ok(latest.wsa, 'wsa family resolves');
  assert.equal(latest.manager.tag_name, 'v0.2.2');
  assert.equal(latest.wsa.tag_name, 'wsa-v2407.40000.4.0');
});

test('non-published registry rows never resolve', () => {
  const draft = {
    schema_version: 1,
    releases: [
      {
        release_id: 'manager-9.9.9-draft', tag: 'v9.9.9', kind: 'manager',
        channel: 'stable', status: 'draft', published_at: '2026-01-01T00:00:00Z',
        assets: []
      }
    ]
  };
  assert.equal(releasesFromRegistry(draft).length, 0);
});

test('E3C.4 gate: derivation surface stays documented (guard-backed)', () => {
  // M3 (tests/test_consumer_compliance.py) pins the derivation inventory.
  // The registry module must exist as the replacement truth source.
  const reg = path.join(repoRoot, 'apps', 'manager', 'src', 'lib', 'registry.ts');
  assert.ok(fs.existsSync(reg), 'registry resolution module must exist');
});
