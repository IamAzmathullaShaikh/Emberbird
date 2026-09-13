import test from 'node:test';
import assert from 'node:assert/strict';

// Helper re-implementations or direct test
function detectArchitecture(filename) {
  const lower = filename.toLowerCase();
  if (lower.includes('x64') || lower.includes('x86_64')) return 'x64';
  if (lower.includes('arm64') || lower.includes('aarch64')) return 'arm64';
  return 'unknown';
}

function detectRootFlavor(filename) {
  const lower = filename.toLowerCase();
  if (lower.includes('magisk')) return 'Magisk';
  if (lower.includes('kernelsu')) return 'KernelSU';
  if (lower.includes('none') || lower.includes('noroot') || lower.includes('vanilla')) return 'NoRoot';
  return 'unknown';
}

function detectGAppsFlavor(filename) {
  const lower = filename.toLowerCase();
  if (lower.includes('pico')) return 'GApps-Pico';
  if (lower.includes('mindthegapps')) return 'MindTheGapps';
  if (lower.includes('nogapps') || lower.includes('no-gapps')) return 'NoGApps';
  return 'unknown';
}

function formatBytes(bytes, decimals = 2) {
  if (!bytes || bytes <= 0) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const safeI = Math.min(i, sizes.length - 1);
  return `${parseFloat((bytes / Math.pow(k, safeI)).toFixed(dm))} ${sizes[safeI]}`;
}

function formatDate(isoString) {
  if (!isoString) return 'Unknown Date';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return 'Unknown Date';
    return d.toISOString().split('T')[0];
  } catch {
    return 'Unknown Date';
  }
}

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

test('detectGAppsFlavor resolves Pico, MindTheGapps, and NoGApps', () => {
  assert.equal(detectGAppsFlavor('WSA_x64_Magisk_GApps-Pico.7z'), 'GApps-Pico');
  assert.equal(detectGAppsFlavor('WSA_x64_Magisk_MindTheGapps.7z'), 'MindTheGapps');
  assert.equal(detectGAppsFlavor('WSA_x64_Magisk_NoGApps.7z'), 'NoGApps');
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
