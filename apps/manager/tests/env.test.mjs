import { test } from 'node:test';
import assert from 'node:assert/strict';

import { validateManagerEnvironment } from '../src/lib/env.ts';

test('validateManagerEnvironment returns valid defaults if repo provided', () => {
  const cfg = validateManagerEnvironment({
    VITE_PUBLIC_GITHUB_REPO: 'TestOwner/TestRepo'
  });
  assert.equal(cfg.github_repo, 'TestOwner/TestRepo');
  assert.equal(cfg.repo_url, 'https://github.com/TestOwner/TestRepo');
  assert.equal(cfg.releases_url, 'https://github.com/TestOwner/TestRepo/releases');
});

test('validateManagerEnvironment throws explicit error on empty repo', () => {
  assert.throws(() => {
    validateManagerEnvironment({
      VITE_PUBLIC_GITHUB_REPO: '   '
    });
  }, /VITE_PUBLIC_GITHUB_REPO must be explicitly provided/);
});
