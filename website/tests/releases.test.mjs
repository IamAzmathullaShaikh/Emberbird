import test from 'node:test';
import assert from 'node:assert/strict';

import { classifyReleaseTag, PinnedReleaseService, GitHubReleaseProvider } from '../src/lib/release-service.ts';
import { detectRootFlavor, detectGAppsFlavor, detectArchitecture } from '../src/lib/parser.ts';

test('classifyReleaseTag separates manager and wsa channels by tag prefix', () => {
  assert.equal(classifyReleaseTag('v0.2.2'), 'manager');
  assert.equal(classifyReleaseTag('v1.0.0'), 'manager');
  assert.equal(classifyReleaseTag('wsa-v2311.40000.5.0'), 'wsa');
  assert.equal(classifyReleaseTag('wsa-v2407.40000.4.0'), 'wsa');
  assert.equal(classifyReleaseTag('Windows_11_2407.40000.4.0'), 'wsa');
  assert.equal(classifyReleaseTag('Windows_11_2311.40000.5.0'), 'wsa');
  // Bare/unprefixed tags default to the manager channel
  assert.equal(classifyReleaseTag('release-2026'), 'manager');
});

test('WSA Standard Edition asset classifies as Magisk root and Pico GApps', () => {
  const name = 'WSA_2407.40000.4.0_x64.7z';
  assert.equal(detectArchitecture(name), 'x64');
  assert.equal(detectRootFlavor(name), 'Magisk');
  assert.equal(detectGAppsFlavor(name), 'GApps-Pico');
});

test('WSA Banking Edition asset (vanilla) classifies as NoRoot and Pico GApps', () => {
  const name = 'WSA_2407.40000.4.0_x64_vanilla.7z';
  assert.equal(detectArchitecture(name), 'x64');
  assert.equal(detectRootFlavor(name), 'NoRoot');
  assert.equal(detectGAppsFlavor(name), 'GApps-Pico');
});

test('WSA classification does not leak into manager asset names', () => {
  // Manager portable archives must stay flavor-unknown for root/gapps
  assert.equal(detectRootFlavor('WSABuildsManager-Portable-0.2.2-x64.zip'), 'unknown');
  assert.equal(detectGAppsFlavor('WSABuildsManager-Portable-0.2.2-x64.zip'), 'unknown');
  assert.equal(detectRootFlavor('WSABuildsManager-Setup-0.2.2-x64.exe'), 'unknown');
});

test('normalize filters metadata sidecars out of the packages table', async () => {
  // Task 2.2: .json validation reports and .txt checksums are published on the
  // release but must never appear as download rows.
  const mockPayload = [
    {
      id: 301,
      tag_name: 'Windows_11_2407.40000.4.0',
      name: 'WSA 2407.40000.4.0',
      published_at: '2026-09-13T20:00:00Z',
      body: '',
      html_url: 'https://example.com/releases/Windows_11_2407.40000.4.0',
      assets: [
        {
          id: 401,
          name: 'WSA_2407.40000.4.0_x64.7z',
          size: 1000,
          browser_download_url: 'https://example.com/download/WSA_2407.40000.4.0_x64.7z'
        },
        {
          id: 402,
          name: 'WSA_2407.40000.4.0_x64_vanilla.7z',
          size: 1000,
          browser_download_url: 'https://example.com/download/WSA_2407.40000.4.0_x64_vanilla.7z'
        },
        {
          id: 403,
          name: 'checksums.txt',
          size: 200,
          browser_download_url: 'https://example.com/download/checksums.txt'
        },
        {
          id: 404,
          name: 'magisk-validation-report-standard.json',
          size: 150,
          browser_download_url: 'https://example.com/download/magisk-validation-report-standard.json'
        },
        {
          id: 405,
          name: 'WSA_2407.40000.4.0_x64.7z.sha256',
          size: 100,
          browser_download_url: 'https://example.com/download/WSA_2407.40000.4.0_x64.7z.sha256'
        }
      ]
    }
  ];

  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async () => ({
      ok: true,
      status: 200,
      json: async () => mockPayload
    });

    const provider = new GitHubReleaseProvider('test-owner/test-repo');
    const release = await provider.getLatestRelease();

    assert.ok(release, 'WSA release must resolve');
    assert.deepEqual(
      release.assets.map((a) => a.fileName),
      ['WSA_2407.40000.4.0_x64.7z', 'WSA_2407.40000.4.0_x64_vanilla.7z'],
      'Only the two real packages may appear as download rows'
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('PinnedReleaseService resolves each channel to its own release', async () => {
  const managerRelease = {
    id: 1,
    tag: 'v0.2.2',
    name: 'Manager 0.2.2',
    publishedAt: '2026-09-14T09:30:25Z',
    formattedDate: '2026-09-14',
    notes: '',
    releaseUrl: 'https://example.com/v0.2.2',
    assets: [],
    channel: 'manager'
  };
  const wsaRelease = {
    id: 2,
    tag: 'wsa-v2311.40000.5.0',
    name: 'WSA 2311.40000.5.0',
    publishedAt: '2026-09-13T23:06:31Z',
    formattedDate: '2026-09-13',
    notes: '',
    releaseUrl: 'https://example.com/wsa-v2311.40000.5.0',
    assets: [],
    channel: 'wsa'
  };

  const stubProvider = {
    name: 'StubProvider',
    async getLatestRelease() {
      return managerRelease; // the releases/latest trap: newest release is Manager
    },
    async getReleaseByTag(tag) {
      return tag === 'wsa-v2311.40000.5.0' ? wsaRelease : null;
    },
    async listReleases() {
      return [managerRelease, wsaRelease]; // API order: manager first (newest publish)
    }
  };

  const service = new PinnedReleaseService(stubProvider, 0);
  const manager = await service.getLatestForChannel('manager');
  const wsa = await service.getLatestForChannel('wsa');

  assert.equal(manager?.tag, 'v0.2.2', 'manager channel must resolve to the manager release');
  assert.equal(wsa?.tag, 'wsa-v2311.40000.5.0', 'wsa channel must resolve to the wsa release, not releases/latest');
});

test('PinnedReleaseService getLatestForChannel returns null when channel absent', async () => {
  const stubProvider = {
    name: 'StubProvider',
    async getLatestRelease() {
      return null;
    },
    async getReleaseByTag() {
      return null;
    },
    async listReleases() {
      return [];
    }
  };

  const service = new PinnedReleaseService(stubProvider, 0);
  assert.equal(await service.getLatestForChannel('wsa'), null);
  assert.equal(await service.getLatestForChannel('manager'), null);
});

test('GitHubReleaseProvider getLatestRelease queries /releases?per_page=20 and targets WSA release', async () => {
  const originalFetch = globalThis.fetch;
  let requestedUrl = '';

  const mockPayload = [
    {
      id: 101,
      tag_name: 'v0.2.2',
      name: 'WSABuilds Manager v0.2.2',
      published_at: '2026-09-14T10:00:00Z',
      body: 'Desktop manager release',
      html_url: 'https://example.com/releases/v0.2.2',
      assets: []
    },
    {
      id: 102,
      tag_name: 'Windows_11_2407.40000.4.0',
      name: 'Windows Subsystem For Android 2407.40000.4.0',
      published_at: '2026-09-13T20:00:00Z',
      body: 'WSA retail release with Magisk and vanilla builds',
      html_url: 'https://example.com/releases/Windows_11_2407.40000.4.0',
      assets: [
        {
          id: 201,
          name: 'WSA_2407.40000.4.0_x64.7z',
          size: 1000,
          download_count: 50,
          browser_download_url: 'https://example.com/download/WSA_2407.40000.4.0_x64.7z',
          created_at: '2026-09-13T20:05:00Z'
        }
      ]
    }
  ];

  try {
    globalThis.fetch = async (url) => {
      requestedUrl = url.toString();
      return {
        ok: true,
        status: 200,
        json: async () => mockPayload
      };
    };

    const provider = new GitHubReleaseProvider('test-owner/test-repo');
    const latest = await provider.getLatestRelease();

    assert.ok(requestedUrl.includes('/repos/test-owner/test-repo/releases?per_page=20'), 'Must query /releases?per_page=20');
    assert.equal(latest?.tag, 'Windows_11_2407.40000.4.0', 'Must target WSA release instead of manager v0.2.2');
    assert.equal(latest?.channel, 'wsa');
    assert.equal(latest?.assets.length, 1);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('PinnedReleaseService getLatestRelease resolves to wsa channel', async () => {
  const wsaRelease = {
    id: 2,
    tag: 'wsa-v2407.40000.4.0',
    name: 'WSA 2407.40000.4.0',
    publishedAt: '2026-09-13T23:06:31Z',
    formattedDate: '2026-09-13',
    notes: '',
    releaseUrl: 'https://example.com/wsa-v2407.40000.4.0',
    assets: [],
    channel: 'wsa'
  };

  const stubProvider = {
    name: 'StubProvider',
    async getLatestRelease() {
      return wsaRelease;
    },
    async getReleaseByTag() {
      return null;
    },
    async listReleases() {
      return [wsaRelease];
    }
  };

  const service = new PinnedReleaseService(stubProvider, 0);
  const resolved = await service.getLatestRelease();
  assert.equal(resolved?.tag, 'wsa-v2407.40000.4.0');
});

