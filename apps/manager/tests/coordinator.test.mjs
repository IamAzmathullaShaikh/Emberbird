import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import { preflightUpgrade, executeUpgrade } from '../src/lib/ipc.ts';

const __dirname = dirname(fileURLToPath(import.meta.url));

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

// Zero-Mock contract (tri-state preflight): a probe that cannot observe the
// host must surface as UNVERIFIED — never as a green pass, and never as a
// silently substituted "typical" value.
test('unverifiable preflight probes are typed as tri-state and rendered UNVERIFIED', () => {
  const types = readFileSync(resolve(__dirname, '../src/lib/types.ts'), 'utf-8');
  assert.match(types, /windows_version_ok: boolean \| null/, 'build verdict must be tri-state');
  assert.match(types, /windows_build: number \| null/, 'build number must be nullable');
  assert.match(types, /disk_space_ok: boolean \| null/, 'disk verdict must be tri-state');
  assert.match(types, /free_disk_bytes: number \| null/, 'free space must be nullable');

  const view = readFileSync(resolve(__dirname, '../src/components/UpdateView.tsx'), 'utf-8');
  assert.ok(view.includes('UNVERIFIED'), 'an unknown probe must be labelled UNVERIFIED');
  assert.ok(!view.includes('Req: 25 GB'), 'the disk requirement must come from preflight truth');
});

test('preflight probes never substitute assumed values for unreadable host state', () => {
  const rust = readFileSync(resolve(__dirname, '../src-tauri/src/coordinator.rs'), 'utf-8');
  assert.ok(!rust.includes('22631'), 'Windows build must not fall back to an assumed number');
  assert.ok(
    !rust.includes('50 * 1024 * 1024 * 1024'),
    'disk space must not fall back to an assumed value'
  );
  assert.match(rust, /fn verify_requirement/, 'requirement evaluation must be tri-state');
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
