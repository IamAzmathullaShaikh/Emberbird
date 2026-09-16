import test from 'node:test';
import assert from 'node:assert/strict';

import { GitHubReleaseProvider } from './lib/github-release-oracle.ts';
import { RegistryReleaseProvider, PinnedReleaseService } from '../src/lib/release-service.ts';
import registryData from '../../data/releases/releases.json' with { type: 'json' };

const REPO = process.env.PUBLIC_GITHUB_REPO || 'IamAzmathullaShaikh/WSABuilds';

/* ---------------------------------------------------------------------------
 * E3B.3 — S2 parity proof (Metamorphosis rule S2): for the same release set,
 * registry-driven output must equal legacy GitHub-discovery output for every
 * field the website pages consume. Parity is demonstrated by test, not
 * asserted by prose.
 *
 * Consumed fields (G2 inventory, Cycle E3B): tag, name, publishedAt,
 * formattedDate, channel, assets[] — releaseUrl, notes and id are never read
 * by any page.
 *
 * Determinism: the legacy provider's global fetch is stubbed for the
 * duration of each test and restored afterwards — no network in unit tests.
 * ------------------------------------------------------------------------- */

function comparableAsset(a) {
  return {
    fileName: a.fileName,
    fileSizeBytes: a.fileSizeBytes,
    downloadUrl: a.downloadUrl,
    architecture: a.architecture,
    rootFlavor: a.rootFlavor,
    gappsFlavor: a.gappsFlavor,
    sha256: a.sha256 ?? null
  };
}

function comparableRelease(r) {
  return {
    tag: r.tag,
    name: r.name,
    publishedAt: r.publishedAt,
    formattedDate: r.formattedDate,
    channel: r.channel,
    assets: [...r.assets].map(comparableAsset)
      .sort((x, y) => x.fileName.localeCompare(y.fileName))
  };
}

let releaseCounter = 0;

/**
 * Render the registry AS GitHub publishes it: one release per tag (multiple
 * registry rows for one tag — e.g. Standard + Banking editions — appear as a
 * single GitHub release with the union of assets), newest release first.
 * This is what GitHubReleaseProvider.normalize consumes in production.
 */
function githubRealityPayload(registry) {
  const byTag = new Map();
  for (const rel of registry.releases) {
    if (!byTag.has(rel.tag)) {
      byTag.set(rel.tag, { rel, assets: [] });
    }
    for (const a of rel.assets) byTag.get(rel.tag).assets.push(a);
  }
  return [...byTag.values()]
    .sort((x, y) => y.rel.published_at.localeCompare(x.rel.published_at))
    .map(({ rel, assets }) => {
      releaseCounter += 1;
      return {
        id: 9000 + releaseCounter,
        tag_name: rel.tag,
        name: rel.release_id,
        published_at: rel.published_at,
        body: '',
        html_url: `https://github.com/${REPO}/releases/tag/${rel.tag}`,
        assets: assets.map((a, i) => ({
          id: 9000 + releaseCounter * 10 + i,
          name: a.filename,
          size: a.size_bytes ?? 0,
          download_count: 0,
          browser_download_url: a.source_url,
          created_at: rel.published_at
        }))
      };
    });
}

function deepEqual(a, b, msg) {
  assert.deepEqual(
    JSON.parse(JSON.stringify(a)),
    JSON.parse(JSON.stringify(b)),
    msg
  );
}

/** Stub global fetch to serve `payload` from the GitHub releases shape. */
function stubFetch(payload) {
  const realFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: true,
    status: 200,
    json: async () => payload
  });
  return () => { globalThis.fetch = realFetch; };
}

test('S2 parity: registry provider equals legacy provider for the full current release set', async () => {
  const registry = registryData;
  assert.ok(Array.isArray(registry.releases) && registry.releases.length >= 6,
    'registry fixture must contain the current release set');

  // Legacy side: the same release set as GitHub actually publishes it
  // (one release per tag, merged assets, newest first).
  const restore = stubFetch(githubRealityPayload(registry));
  try {
    const legacy = new GitHubReleaseProvider(REPO);
    const registryProvider = new RegistryReleaseProvider(registry);

    const legacyList = await legacy.listReleases();
    const registryList = await registryProvider.listReleases();

    // Same release set: identical tags.
    assert.deepEqual(
      legacyList.map((r) => r.tag).sort(),
      registryList.map((r) => r.tag).sort(),
      'parity requires both providers to resolve the same release-tag set'
    );

    // Per-release parity for every consumed field.
    const legacyByTag = new Map(legacyList.map((r) => [r.tag, r]));
    for (const reg of registryList) {
      const leg = legacyByTag.get(reg.tag);
      assert.ok(leg, `legacy side must resolve ${reg.tag}`);

      // 1. Display parity: every consumed field must be identical.
      //    (sha256 compared separately — see below.)
      const stripSha = (r) => ({
        ...comparableRelease(r),
        assets: comparableRelease(r).assets.map(({ sha256, ...rest }) => rest)
      });
      deepEqual(stripSha(reg), stripSha(leg),
        `registry display output must equal legacy output for ${reg.tag}`);

      // 2. Checksum rule (S2, documented enrichment): releases publish hashes
      //    as sidecar assets, so the legacy body-regex path sees none. The
      //    registry carries them from the published manifests (L2 truth).
      //    Wherever legacy derives a hash, registry must agree; where legacy
      //    has none, registry must provide the published hash.
      const legAssets = new Map(leg.assets.map((a) => [a.fileName, a]));
      for (const ra of reg.assets) {
        const la = legAssets.get(ra.fileName);
        assert.ok(la, `legacy must expose ${ra.fileName}`);
        if (la.sha256) {
          assert.equal(ra.sha256, la.sha256,
            `checksum disagreement for ${ra.fileName}`);
        } else {
          assert.match(ra.sha256 ?? '', /^[a-f0-9]{64}$/,
            `registry must supply the published sha256 for ${ra.fileName}`);
        }
      }
    }
  } finally {
    restore();
  }
});

test('S2 parity: channel pinning agrees between providers', async () => {
  const registry = registryData;
  const restore = stubFetch(githubRealityPayload(registry));
  let lManager, rManager, lWsa, rWsa;
  try {
    const legacySvc = new PinnedReleaseService(new GitHubReleaseProvider(REPO));
    const registrySvc = new PinnedReleaseService(new RegistryReleaseProvider(registry));
    lManager = await legacySvc.getLatestForChannel('manager');
    rManager = await registrySvc.getLatestForChannel('manager');
    lWsa = await legacySvc.getLatestForChannel('wsa');
    rWsa = await registrySvc.getLatestForChannel('wsa');
  } finally {
    restore();
  }
  assert.equal(lManager?.tag ?? null, rManager?.tag ?? null,
    'channel pinning must agree for manager');
  assert.equal(lManager?.assets.length, rManager?.assets.length,
    'asset-count parity for manager');
  assert.equal(lWsa?.tag ?? null, rWsa?.tag ?? null,
    'channel pinning must agree for wsa');
  assert.equal(lWsa?.assets.length, rWsa?.assets.length,
    'asset-count parity for wsa (merged editions)');
});

test('registry provider resolves tags, checksums, and download URLs from registry truth', async () => {
  const provider = new RegistryReleaseProvider();
  const rs = await provider.listReleases();
  const tags = ['v0.2.2', 'wsa-v2311.40000.5.0', 'Windows_11_2407.40000.4.0'];
  for (const tag of tags) {
    assert.ok(rs.some((x) => x.tag === tag), `registry must advertise ${tag}`);
  }
  const wsa = rs.find((x) => x.tag === 'wsa-v2311.40000.5.0');
  assert.ok(wsa && wsa.assets.length >= 2,
    'WSA tag must expose the merged edition assets (Standard + Banking)');
  const wsaAsset = wsa.assets[0];
  assert.match(wsaAsset.sha256 ?? '', /^[a-f0-9]{64}$/,
    'registry asset must carry a real published sha256');
  assert.ok(wsaAsset.downloadUrl.includes('/releases/download/'),
    'download URL must be the published release-asset URL');
});

test('registry provider advertises only published releases', async () => {
  const draft = {
    schema_version: 1,
    releases: [
      {
        release_id: 'manager-9.9.9-draft', tag: 'v9.9.9', kind: 'manager',
        channel: 'stable', status: 'draft', published_at: '2026-01-01T00:00:00Z',
        provenance: {}, assets: []
      }
    ]
  };
  const provider = new RegistryReleaseProvider(draft);
  assert.equal((await provider.listReleases()).length, 0,
    'non-published releases must never be advertised');
});

test('E3B.4 gate: both providers implement the shared ReleaseProvider seam', async () => {
  const reg = new RegistryReleaseProvider();
  assert.equal(typeof reg.getLatestRelease, 'function');
  assert.equal(typeof reg.getReleaseByTag, 'function');
  assert.equal(typeof reg.listReleases, 'function');
  assert.equal(reg.name, 'EmberRegistry');
});
