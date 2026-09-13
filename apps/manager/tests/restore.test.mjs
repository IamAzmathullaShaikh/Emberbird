import { test } from 'node:test';
import assert from 'node:assert/strict';

import { restoreVhdxBackup } from '../src/lib/ipc.ts';

test('restoreVhdxBackup verifies candidate and returns restored path and checksum', async () => {
  const candidateId = 'backup_20260901_120000';
  const result = await restoreVhdxBackup(candidateId);

  assert.equal(result.success, true);
  assert.equal(result.candidate_id, candidateId);
  assert.ok(result.restored_path, 'Must report restored destination path');
  assert.match(
    result.restored_sha256,
    /^[a-f0-9]{64}$/,
    'Restored SHA-256 must match valid hash format'
  );
  assert.ok(
    result.message.includes('verified'),
    'Restore message must confirm integrity verification'
  );
});
