import { test } from 'node:test';
import assert from 'node:assert/strict';

import { detectWsaStatus } from '../src/lib/ipc.ts';

test('detectWsaStatus returns complete subsystem status structure in mock environment', async () => {
  const status = await detectWsaStatus();

  assert.equal(typeof status.installed, 'boolean');
  assert.equal(typeof status.developer_mode_enabled, 'boolean');
  assert.equal(typeof status.virtualization_enabled, 'boolean');
  assert.equal(typeof status.is_running, 'boolean');

  if (status.installed) {
    assert.ok(status.package_version, 'Installed WSA must have a package version');
    assert.ok(status.install_path, 'Installed WSA must report an install path');
    assert.ok(status.vhdx_path, 'Installed WSA must report a VHDX path');
  }
});
