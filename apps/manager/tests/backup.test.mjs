import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  createVhdxBackup,
  listBackupCandidates,
  pruneBackups,
} from '../src/lib/ipc.ts';

test('createVhdxBackup returns successful metadata structure with SHA-256 and size', async () => {
  const result = await createVhdxBackup('Test pre-upgrade backup');

  assert.equal(result.success, true);
  assert.equal(result.error, null);
  assert.ok(result.metadata, 'Metadata must be present on success');

  const meta = result.metadata;
  assert.ok(meta.id.startsWith('backup_'), 'Backup ID must have backup_ prefix');
  assert.equal(meta.description, 'Test pre-upgrade backup');
  assert.equal(typeof meta.file_size_bytes, 'number');
  assert.ok(meta.file_size_bytes > 0, 'Backup size must be positive');
  assert.match(
    meta.sha256,
    /^[a-f0-9]{64}$/,
    'Checksum must be a valid 64-char hex SHA-256'
  );
  assert.equal(meta.status, 'completed');
});

test('listBackupCandidates returns sorted candidates with validity flags', async () => {
  const candidates = await listBackupCandidates();

  assert.ok(Array.isArray(candidates));
  assert.ok(candidates.length > 0, 'Should have mock candidates in registry');

  for (const candidate of candidates) {
    assert.ok(candidate.id, 'Candidate must have an ID');
    assert.ok(candidate.timestamp, 'Candidate must have an ISO timestamp');
    assert.ok(candidate.wsa_version, 'Candidate must specify WSA version');
    assert.equal(typeof candidate.is_valid, 'boolean');
    assert.match(
      candidate.sha256,
      /^[a-f0-9]{64}$/,
      'SHA-256 must be a 64-char hex string'
    );
  }

  // Verify descending sort order by timestamp
  for (let i = 0; i < candidates.length - 1; i++) {
    const tCurrent = new Date(candidates[i].timestamp).getTime();
    const tNext = new Date(candidates[i].next?.timestamp || candidates[i + 1].timestamp).getTime();
    assert.ok(
      tCurrent >= tNext,
      'Candidates must be sorted descending by timestamp'
    );
  }
});

test('pruneBackups executes retention policy and returns pruned candidate IDs', async () => {
  const pruned = await pruneBackups(1);

  assert.ok(Array.isArray(pruned));
  assert.ok(pruned.length > 0, 'Pruning should remove older backups exceeding retention limit');
});
