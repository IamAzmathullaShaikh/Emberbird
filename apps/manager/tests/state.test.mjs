import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  getSubsystemStatePresentation,
  projectSubsystemStatus,
  normalizeStatusPayload,
} from '../src/lib/state.ts';

const ALL_STATES = ['NOT_INSTALLED', 'INSTALLED', 'INSTALLED_OUTDATED', 'PARTIALLY_INSTALLED', 'UNKNOWN'];

function makeStatus(overrides = {}) {
  return normalizeStatusPayload({
    installed: true,
    package_version: '2311.40000.5.0',
    developer_mode_enabled: true,
    virtualization_enabled: true,
    is_running: false,
    install_path: 'C:/Program Files/WindowsApps/WSA',
    vhdx_path: 'C:/LocalCache/userdata.vhdx',
    state: 'INSTALLED',
    state_evidence: ['Installed version 2311.40000.5.0 satisfies the supported baseline.'],
    ...overrides,
  });
}

test('every authoritative state has a distinct, non-empty presentation', () => {
  const seen = new Set();
  for (const state of ALL_STATES) {
    const p = getSubsystemStatePresentation(state);
    assert.ok(p.label && p.label.length > 0, `${state} must have a label`);
    assert.ok(p.guidance && p.guidance.length > 0, `${state} must have guidance`);
    seen.add(p.label);
  }
  assert.equal(seen.size, ALL_STATES.length, 'state labels must be mutually distinct');
});

test('fresh machine: NOT_INSTALLED never shows a version or a Running badge', () => {
  const status = makeStatus({
    installed: false,
    package_version: null,
    install_path: null,
    vhdx_path: null,
    state: 'NOT_INSTALLED',
    state_evidence: ['Package is not registered with Windows.'],
  });
  const projected = projectSubsystemStatus(status);
  assert.equal(projected.presentation.label, 'Not Installed');
  assert.equal(projected.versionLabel, '—', 'no version may be displayed');
  assert.equal(projected.runningLabel, null, 'no Running/Stopped badge may be displayed');
  assert.equal(projected.presentation.usable, false);
});

test('WSA installed: state, version and running badge all agree', () => {
  const status = makeStatus({
    installed: true,
    package_version: '2311.40000.5.0',
    state: 'INSTALLED',
    is_running: true,
  });
  const projected = projectSubsystemStatus(status);
  assert.equal(projected.presentation.label, 'Installed');
  assert.equal(projected.versionLabel, '2311.40000.5.0');
  assert.equal(projected.runningLabel, 'Running');
  assert.equal(projected.presentation.usable, true);
});

test('broken installation: PARTIALLY_INSTALLED may show version but is not usable', () => {
  const status = makeStatus({
    installed: true,
    state: 'PARTIALLY_INSTALLED',
    state_evidence: ['Package is registered but required components are missing: userdata.vhdx.'],
  });
  const projected = projectSubsystemStatus(status);
  assert.equal(projected.presentation.label, 'Partially Installed');
  assert.equal(projected.versionLabel, '2311.40000.5.0', 'registered package version is factual');
  assert.equal(projected.presentation.usable, false, 'broken install must not enable actions');
});

test('orphaned userdata.vhdx with no package: labeled as orphaned data, never as installed', () => {
  const status = makeStatus({
    installed: false,
    package_version: null,
    install_path: null,
    state: 'NOT_INSTALLED',
    state_evidence: [
      'Package is not registered with Windows.',
      'A userdata.vhdx exists on disk (orphaned data, not an installation).',
    ],
  });
  const projected = projectSubsystemStatus(status);
  assert.equal(projected.presentation.label, 'Not Installed');
  assert.ok(
    projected.vhdxLabel.includes('orphaned data'),
    `orphaned VHDX must be labeled as data, got: ${projected.vhdxLabel}`
  );
  assert.equal(projected.presentation.usable, false);
});

test('version mismatch: INSTALLED_OUTDATED is usable and surfaces the version', () => {
  const status = makeStatus({
    installed: true,
    package_version: '2308.40000.2.0',
    state: 'INSTALLED_OUTDATED',
    state_evidence: ['Installed version 2308.40000.2.0 is older than the supported baseline 2311.40000.5.0.'],
  });
  const projected = projectSubsystemStatus(status);
  assert.equal(projected.presentation.label, 'Installed (Outdated)');
  assert.equal(projected.versionLabel, '2308.40000.2.0');
  assert.equal(projected.presentation.usable, true);
});

test('no contradictory pairs can be constructed: version shown iff state allows it', () => {
  const contradictions = [];
  for (const state of ALL_STATES) {
    const p = getSubsystemStatePresentation(state);
    const status = makeStatus({ state, package_version: p.mayShowVersion ? '1.2.3.4' : null });
    const projected = projectSubsystemStatus(status);
    const showsVersion = projected.versionLabel !== '—';
    if (showsVersion !== p.mayShowVersion) {
      contradictions.push(`${state}: expected mayShowVersion=${p.mayShowVersion}, got version label "${projected.versionLabel}"`);
    }
    if (!p.mayShowVersion && projected.runningLabel !== null) {
      contradictions.push(`${state}: Running/Stopped badge shown without a registered state`);
    }
  }
  assert.deepEqual(contradictions, [], `contradictory projections found: ${contradictions.join('; ')}`);
});

test('legacy payloads without a state field are normalized, never crash', () => {
  const legacy = { installed: true, package_version: '9.9.9.9' };
  const normalized = normalizeStatusPayload(legacy);
  assert.equal(normalized.state, 'INSTALLED');
  assert.ok(Array.isArray(normalized.state_evidence));

  const empty = normalizeStatusPayload(null);
  assert.equal(empty, null);
  const projected = projectSubsystemStatus(null);
  assert.equal(projected.presentation.label, 'Unknown');
});
