import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const repoRoot = path.resolve(import.meta.dirname, '../../..');
const versionJsonPath = path.join(repoRoot, 'deployment', 'version.json');

test('version metadata layer provides valid package id and semver', () => {
  assert.ok(fs.existsSync(versionJsonPath), 'deployment/version.json must exist');

  const content = fs.readFileSync(versionJsonPath, 'utf8');
  const data = JSON.parse(content);

  assert.ok(data.manager, 'Must contain manager metadata');
  assert.equal(data.manager.winget_package_id, 'WSABuilds.WSABuildsManager');
  assert.match(
    data.manager.version,
    /^[0-9]+\.[0-9]+\.[0-9]+$/,
    'Version must follow semver'
  );
  assert.equal(data.manager.channel, 'stable');
  assert.ok(Array.isArray(data.manager.target_architectures));
  assert.ok(data.manager.target_architectures.includes('x64'));
});

test('winget install command formats correctly', () => {
  const content = fs.readFileSync(versionJsonPath, 'utf8');
  const data = JSON.parse(content);
  const cmd = `winget install ${data.manager.winget_package_id}`;

  assert.equal(cmd, 'winget install WSABuilds.WSABuildsManager');
});

test('manifest folder matches version metadata exactly', () => {
  const content = fs.readFileSync(versionJsonPath, 'utf8');
  const data = JSON.parse(content);
  const version = data.manager.version;

  const manifestDir = path.join(
    repoRoot,
    'manifests',
    'w',
    'WSABuilds',
    'WSABuildsManager',
    version
  );

  assert.ok(fs.existsSync(manifestDir), `Manifest directory ${manifestDir} must exist`);

  const versionYaml = path.join(manifestDir, 'WSABuilds.WSABuildsManager.yaml');
  const installerYaml = path.join(
    manifestDir,
    'WSABuilds.WSABuildsManager.installer.yaml'
  );
  const localeYaml = path.join(
    manifestDir,
    'WSABuilds.WSABuildsManager.locale.en-US.yaml'
  );

  assert.ok(fs.existsSync(versionYaml), 'Version YAML must exist');
  assert.ok(fs.existsSync(installerYaml), 'Installer YAML must exist');
  assert.ok(fs.existsSync(localeYaml), 'Locale YAML must exist');
});
