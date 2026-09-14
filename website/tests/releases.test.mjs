import test from 'node:test';
import assert from 'node:assert/strict';

import { classifyReleaseTag, PinnedReleaseService } from '../src/lib/release-service.ts';
import { detectRootFlavor, detectGAppsFlavor, detectArchitecture } from '../src/lib/parser.ts';

test('classifyReleaseTag separates manager and wsa channels by tag prefix', () => {
  assert.equal(classifyReleaseTag('v0.2.2'), 'manager');
  assert.equal(classifyReleaseTag('v1.0.0'), 'manager');
  assert.equal(classifyReleaseTag('wsa-v2311.40000.5.0'), 'wsa');
  assert.equal(classifyReleaseTag('wsa-v2407.40000.4.0'), 'wsa');
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
