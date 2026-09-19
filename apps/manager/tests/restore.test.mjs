import { test } from 'node:test';
import assert from 'node:assert/strict';

import { restoreVhdxBackup } from '../src/lib/ipc.ts';

// Zero-Mock contract: outside a real Tauri backend there is no restore to run,
// so the wrapper must reject rather than fabricate a verified restoration.
test('restoreVhdxBackup rejects in browser mode instead of faking a restore', async () => {
  await assert.rejects(
    () => restoreVhdxBackup('backup_20260901_120000'),
    /Tauri backend not detected/,
    'Restore must surface the missing-backend error, never a fake verified restore'
  );
});
