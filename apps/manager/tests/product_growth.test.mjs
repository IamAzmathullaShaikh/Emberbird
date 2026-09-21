import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import { installWsaPackage } from '../src/lib/ipc.ts';
import {
  latestReleasesFromRegistry,
  releasesFromRegistry,
  recommendedWsaAsset,
  recommendedWsaLabel,
} from '../src/lib/registry.ts';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

test('installWsaPackage rejects in browser mode instead of faking an install', async () => {
  // Zero-Mock contract: outside a real Tauri backend there is no package to
  // register, so the wrapper must reject rather than fabricate success.
  await assert.rejects(
    () => installWsaPackage('C:\\Emberbird\\WSA_2407.40000.4.0_x64_Release-Magisk'),
    /Tauri backend not detected/,
    'Installation must never report fabricated registration success'
  );
});

test('Observatory recommended release is resolved from registry truth', () => {
  const latest = latestReleasesFromRegistry();
  assert.ok(latest.wsa, 'WSA release family must be present');
  assert.equal(latest.wsa.tag_name, 'wsa-v2407.40000.4.0');

  const allWsa = releasesFromRegistry().filter((r) => r.channel === 'wsa');
  assert.ok(allWsa.length >= 2, 'Must include published WSA releases');
});

test('recommended WSA asset is the policy edition at its registry version', () => {
  const asset = recommendedWsaAsset();
  assert.ok(asset, 'recommended asset must resolve from the registry');
  assert.equal(asset.edition, 'standard', 'Standard Edition is the policy recommendation');
  assert.equal(asset.release_tag, 'wsa-v2407.40000.4.0');
  assert.equal(
    recommendedWsaLabel(),
    `Standard Edition ${asset.wsa_version}`,
    'label must name the recommended edition with the registry version'
  );
});

test('StatusCard defines Quick Setup Wizard and edition options', () => {
  const code = readFileSync(resolve(__dirname, '../src/components/StatusCard.tsx'), 'utf-8');
  assert.ok(code.includes('Quick Setup') && code.includes('One-Click Installer'), 'StatusCard must define quick installer');
  assert.ok(code.includes('Standard Edition'), 'Must offer Standard Edition');
  assert.ok(code.includes('Banking Edition'), 'Must offer Banking Edition');
  assert.ok(code.includes('installWsaPackage'), 'Must invoke installWsaPackage IPC');
});

test('Header version badge derives from the built app identity, never a literal', () => {
  const code = readFileSync(resolve(__dirname, '../src/components/Header.tsx'), 'utf-8');
  assert.ok(
    code.includes("from '@tauri-apps/api/app'"),
    'Header must read the running app version from Tauri'
  );
  assert.ok(
    !/v0\.\d+\.\d+/.test(code),
    'no release version literal may live in living UI code'
  );
});

test('Header defines architecture intelligence and Snapdragon native badge', () => {
  const code = readFileSync(resolve(__dirname, '../src/components/Header.tsx'), 'utf-8');
  assert.ok(code.includes('ARM64 (Snapdragon Native)'), 'Must detect Snapdragon native arch');
  assert.ok(code.includes('x64 Native'), 'Must detect x64 native arch');
});

test('ReleaseCard defines Observatory recommendation and architecture filter', () => {
  const code = readFileSync(resolve(__dirname, '../src/components/ReleaseCard.tsx'), 'utf-8');
  assert.ok(code.includes('Observatory Recommended'), 'Must surface Observatory badge');
  assert.ok(
    code.includes('recommendedWsaLabel'),
    'Must derive the recommended edition label from registry truth (FB-1: no hardcoded release versions in UI)'
  );
  assert.ok(
    !code.includes('Standard Edition 2407.40000.4.0'),
    'Recommended label must be registry-derived, never hardcoded'
  );
  assert.ok(code.includes('Architecture Filter:'), 'Must provide architecture filter');
  assert.ok(code.includes('Snapdragon X Elite'), 'Must detail Snapdragon compatibility');
});

test('RestoreView defines Emergency 1-Click Rollback and Storage Relocation Guide', () => {
  const code = readFileSync(resolve(__dirname, '../src/components/RestoreView.tsx'), 'utf-8');
  assert.ok(code.includes('Emergency Rollback'), 'Must offer Emergency Rollback');
  assert.ok(code.includes('Revert to Last Known Good State'), 'Must identify last known good state');
  assert.ok(code.includes('Storage Relocation'), 'Must provide storage relocation guide');
  assert.ok(code.includes('New-Item -ItemType Junction'), 'Must provide junction command for multi-drive setups');
});
