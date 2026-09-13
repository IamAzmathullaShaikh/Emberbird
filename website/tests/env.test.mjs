import test from 'node:test';
import assert from 'node:assert/strict';

function validateEnvironment(env) {
  const REQUIRED = ['SITE_URL', 'PUBLIC_GITHUB_REPO', 'PUBLIC_GITHUB_REPO_URL', 'PUBLIC_RELEASES_URL'];
  const missing = [];
  for (const key of REQUIRED) {
    const val = env[key];
    if (!val || typeof val !== 'string' || val.trim().length === 0) {
      missing.push(key);
    }
  }
  return { valid: missing.length === 0, missing };
}

test('validateEnvironment detects missing required variables', () => {
  const result = validateEnvironment({});
  assert.equal(result.valid, false);
  assert.equal(result.missing.length, 4);
});

test('validateEnvironment detects partial missing variables', () => {
  const result = validateEnvironment({
    SITE_URL: 'http://localhost:4321',
    PUBLIC_GITHUB_REPO: 'owner/repo'
  });
  assert.equal(result.valid, false);
  assert.deepEqual(result.missing, ['PUBLIC_GITHUB_REPO_URL', 'PUBLIC_RELEASES_URL']);
});

test('validateEnvironment passes when all variables are provided', () => {
  const result = validateEnvironment({
    SITE_URL: 'http://localhost:4321',
    PUBLIC_GITHUB_REPO: 'owner/repo',
    PUBLIC_GITHUB_REPO_URL: 'https://github.com/owner/repo',
    PUBLIC_RELEASES_URL: 'https://github.com/owner/repo/releases'
  });
  assert.equal(result.valid, true);
  assert.equal(result.missing.length, 0);
});
