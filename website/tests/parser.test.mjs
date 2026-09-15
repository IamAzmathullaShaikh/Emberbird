import test from 'node:test';
import assert from 'node:assert/strict';

// Import the real production module so these tests can never drift from it.
import {
  detectArchitecture,
  detectRootFlavor,
  detectGAppsFlavor,
  formatBytes,
  formatDate
} from '../src/lib/parser.ts';

test('detectArchitecture resolves x64 and arm64 correctly', () => {
  assert.equal(detectArchitecture('WSA_build_x64_Magisk.7z'), 'x64');
  assert.equal(detectArchitecture('WSA_build_arm64_KernelSU.7z'), 'arm64');
  assert.equal(detectArchitecture('WSA_build_x86_64.7z'), 'x64');
  assert.equal(detectArchitecture('WSA_unknown_arch.zip'), 'unknown');
});

test('detectRootFlavor resolves Magisk, KernelSU, and NoRoot', () => {
  assert.equal(detectRootFlavor('WSA_x64_Magisk_GApps.7z'), 'Magisk');
  assert.equal(detectRootFlavor('WSA_x64_KernelSU_GApps.7z'), 'KernelSU');
  assert.equal(detectRootFlavor('WSA_x64_NoRoot_GApps.7z'), 'NoRoot');
  assert.equal(detectRootFlavor('WSA_x64_vanilla.7z'), 'NoRoot');
});

test('detectRootFlavor treats token-less WSA archives as Standard (Magisk)', () => {
  // Task 2.2: retail filenames carry no root token — absence of vanilla means rooted
  assert.equal(detectRootFlavor('WSA_2407.40000.4.0_x64.7z'), 'Magisk');
  assert.equal(detectRootFlavor('WSA_2311.40000.5.0_x64.7z'), 'Magisk');
});

test('detectRootFlavor keeps non-WSA names unknown', () => {
  assert.equal(detectRootFlavor('WSABuildsManager-Portable-0.2.2-x64.zip'), 'unknown');
  assert.equal(detectRootFlavor('random-tool.zip'), 'unknown');
});

test('detectGAppsFlavor resolves Pico, MindTheGapps, and NoGApps', () => {
  assert.equal(detectGAppsFlavor('WSA_x64_Magisk_GApps-Pico.7z'), 'GApps-Pico');
  assert.equal(detectGAppsFlavor('WSA_x64_Magisk_MindTheGapps.7z'), 'MindTheGapps');
  assert.equal(detectGAppsFlavor('WSA_x64_Magisk_NoGApps.7z'), 'NoGApps');
});

test('detectGAppsFlavor treats token-less WSA archives as GApps-Pico', () => {
  // Both release editions ship OpenGApps Pico — token-less retail names included
  assert.equal(detectGAppsFlavor('WSA_2407.40000.4.0_x64.7z'), 'GApps-Pico');
  assert.equal(detectGAppsFlavor('WSABuildsManager-Setup-0.2.2-x64.exe'), 'unknown');
});

test('formatBytes correctly formats various byte scales', () => {
  assert.equal(formatBytes(0), '0 B');
  assert.equal(formatBytes(1024), '1 KB');
  assert.equal(formatBytes(1048576), '1 MB');
  assert.equal(formatBytes(1342177280), '1.25 GB');
});

test('formatDate normalizes ISO timestamps to YYYY-MM-DD', () => {
  assert.equal(formatDate('2026-09-14T01:00:00Z'), '2026-09-14');
  assert.equal(formatDate(''), 'Unknown Date');
  assert.equal(formatDate('invalid'), 'Unknown Date');
});
