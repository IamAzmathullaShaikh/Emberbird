import { test } from 'node:test';
import assert from 'node:assert/strict';

import { detectWsaStatus } from '../src/lib/ipc.ts';

// Zero-Mock contract: outside a real Tauri backend there is no OS state to
// report, so detection must reject — the UI renders "Detection Failed" from
// this rejection rather than a fabricated status object.
test('detectWsaStatus rejects in browser mode instead of fabricating status', async () => {
  await assert.rejects(
    () => detectWsaStatus(),
    /Tauri backend not detected/,
    'Status detection must surface Detection Failed outside the Tauri backend'
  );
});
