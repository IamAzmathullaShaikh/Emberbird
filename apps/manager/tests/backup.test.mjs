import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  createVhdxBackup,
  listBackupCandidates,
  pruneBackups,
} from '../src/lib/ipc.ts';

// Zero-Mock contract: ipc.ts throws outside a real Tauri backend instead of
// returning fabricated success data. The browser/Node test environment has no
// backend, so every IPC wrapper must reject — never resolve with fake data.
const BROWSER_MODE_ERROR = /Tauri backend not detected/;

test('createVhdxBackup rejects in browser mode instead of faking a backup', async () => {
  await assert.rejects(
    () => createVhdxBackup('Test pre-upgrade backup'),
    BROWSER_MODE_ERROR,
    'Backup creation must never report fabricated success outside the Tauri backend'
  );
});

test('listBackupCandidates rejects in browser mode instead of faking a registry', async () => {
  await assert.rejects(
    () => listBackupCandidates(),
    BROWSER_MODE_ERROR,
    'Backup listing must surface Detection Failed, not synthetic candidates'
  );
});

test('pruneBackups rejects in browser mode instead of faking a retention run', async () => {
  await assert.rejects(
    () => pruneBackups(1),
    BROWSER_MODE_ERROR,
    'Pruning must never report fabricated deletions'
  );
});
