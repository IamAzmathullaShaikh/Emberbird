import { test } from 'node:test';
import assert from 'node:assert/strict';

import { preflightUpgrade, executeUpgrade } from '../src/lib/ipc.ts';

// Zero-Mock contract: IPC wrappers reject outside the Tauri backend. A
// fabricated "can_upgrade: true" or "success: true" would be a lie about the
// real machine state, so tests assert rejection instead.
test('preflightUpgrade rejects in browser mode instead of faking readiness', async () => {
  await assert.rejects(
    () => preflightUpgrade(),
    /Tauri backend not detected/,
    'Preflight must never fabricate disk/dev-mode/virtualization readiness'
  );
});

test('executeUpgrade rejects in browser mode instead of faking a completed upgrade', async () => {
  await assert.rejects(
    () => executeUpgrade({
      package_path: 'C:\\Packages\\WSA-Release-2311',
      create_backup: true,
      backup_note: 'Preflight test run',
    }),
    /Tauri backend not detected/,
    'Upgrade execution must never report fabricated success'
  );
});
