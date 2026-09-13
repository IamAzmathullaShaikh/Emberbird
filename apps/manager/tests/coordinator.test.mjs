import { test } from 'node:test';
import assert from 'node:assert/strict';

import { preflightUpgrade, executeUpgrade } from '../src/lib/ipc.ts';

test('preflightUpgrade reports system readiness and 25GB disk requirement', async () => {
  const preflight = await preflightUpgrade();

  assert.equal(typeof preflight.windows_version_ok, 'boolean');
  assert.equal(typeof preflight.dev_mode_ok, 'boolean');
  assert.equal(typeof preflight.virtualization_ok, 'boolean');
  assert.equal(typeof preflight.disk_space_ok, 'boolean');
  assert.equal(typeof preflight.can_upgrade, 'boolean');

  // Verify 25 GB constant (25 * 1024 * 1024 * 1024)
  assert.equal(preflight.required_disk_bytes, 26843545600);
  assert.ok(preflight.free_disk_bytes > 0, 'Free disk bytes must be positive');
});

test('executeUpgrade runs orchestrated pipeline with safety backup metadata', async () => {
  const result = await executeUpgrade({
    package_path: 'C:\\Packages\\WSA-Release-2311',
    create_backup: true,
    backup_note: 'Preflight test run',
  });

  assert.equal(result.success, true);
  assert.ok(result.backup_metadata, 'Backup metadata should be created when requested');
  assert.ok(result.installed_manifest, 'Installed manifest path should be reported');
  assert.ok(result.message.includes('completed'), 'Message should indicate successful upgrade');
});
