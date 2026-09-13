import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  calculateStats,
  getCategories,
  filterRecords,
  getStatusBadgeClass
} from '../src/lib/compatibility/service.ts';

const mockRecords = [
  {
    app_name: 'App Alpha',
    package_id: 'com.alpha.bank',
    category: 'Banking & UPI',
    compatibility_status: 'Working',
    play_integrity_required: true,
    tested_wsa_version: '2311.40000.5.0',
    tested_root_flavor: 'Magisk Stable',
    workaround_steps: [],
    verification_status: 'verified'
  },
  {
    app_name: 'App Beta',
    package_id: 'com.beta.chat',
    category: 'Social & Communication',
    compatibility_status: 'Workaround Required',
    play_integrity_required: false,
    tested_wsa_version: '2311.40000.5.0',
    tested_root_flavor: 'Magisk Stable',
    workaround_steps: ['Step 1'],
    verification_status: 'unverified'
  },
  {
    app_name: 'App Gamma',
    package_id: 'com.gamma.game',
    category: 'Gaming',
    compatibility_status: 'Broken',
    play_integrity_required: true,
    tested_wsa_version: '2311.40000.5.0',
    tested_root_flavor: 'No Root',
    workaround_steps: [],
    verification_status: 'unverified'
  }
];

test('calculateStats aggregates correctly', () => {
  const stats = calculateStats(mockRecords);
  assert.equal(stats.total, 3);
  assert.equal(stats.working, 1);
  assert.equal(stats.workaround, 1);
  assert.equal(stats.broken, 1);
  assert.equal(stats.playIntegrityRequired, 2);
});

test('getCategories returns sorted unique categories', () => {
  const categories = getCategories(mockRecords);
  assert.deepEqual(categories, ['Banking & UPI', 'Gaming', 'Social & Communication']);
});

test('filterRecords filters by category', () => {
  const filtered = filterRecords(mockRecords, { category: 'Gaming' });
  assert.equal(filtered.length, 1);
  assert.equal(filtered[0].app_name, 'App Gamma');
});

test('filterRecords filters by compatibility status', () => {
  const filtered = filterRecords(mockRecords, { status: 'Working' });
  assert.equal(filtered.length, 1);
  assert.equal(filtered[0].app_name, 'App Alpha');
});

test('filterRecords filters by search query on name and package ID', () => {
  const byName = filterRecords(mockRecords, { searchQuery: 'beta' });
  assert.equal(byName.length, 1);
  assert.equal(byName[0].app_name, 'App Beta');

  const byPkg = filterRecords(mockRecords, { searchQuery: 'gamma.game' });
  assert.equal(byPkg.length, 1);
  assert.equal(byPkg[0].app_name, 'App Gamma');
});

test('filterRecords filters by play integrity requirement', () => {
  const filtered = filterRecords(mockRecords, { playIntegrityOnly: true });
  assert.equal(filtered.length, 2);
});

test('getStatusBadgeClass returns accurate theme tokens', () => {
  const workingBadge = getStatusBadgeClass('Working');
  assert.ok(workingBadge.text.includes('emerald'));

  const workaroundBadge = getStatusBadgeClass('Workaround Required');
  assert.ok(workaroundBadge.text.includes('amber'));

  const brokenBadge = getStatusBadgeClass('Broken');
  assert.ok(brokenBadge.text.includes('rose'));
});
