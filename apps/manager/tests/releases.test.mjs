import { test } from 'node:test';
import assert from 'node:assert/strict';

import { compareVersions, isNewerVersion, cleanVersionString } from '../src/lib/semver.ts';

test('cleanVersionString strips v prefix and whitespace', () => {
  assert.equal(cleanVersionString('v2311.40000.5.0'), '2311.40000.5.0');
  assert.equal(cleanVersionString('V2.0.1 '), '2.0.1');
  assert.equal(cleanVersionString(''), '0.0.0.0');
});

test('compareVersions accurately evaluates semantic versions', () => {
  assert.equal(compareVersions('2311.40000.5.0', '2311.40000.5.0'), 0);
  assert.equal(compareVersions('2311.40000.6.0', '2311.40000.5.0'), 1);
  assert.equal(compareVersions('2310.40000.5.0', '2311.40000.5.0'), -1);
});

test('isNewerVersion returns true only when target is strictly higher', () => {
  assert.equal(isNewerVersion('2311.40000.5.0', '2311.40000.6.0'), true);
  assert.equal(isNewerVersion('2311.40000.5.0', '2311.40000.5.0'), false);
  assert.equal(isNewerVersion('2311.40000.5.0', '2310.40000.5.0'), false);
});
