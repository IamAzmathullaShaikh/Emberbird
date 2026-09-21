import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const managerSrc = join(__dirname, '..', 'src');

test('ipc exposes downloadAndStageRelease bound to the Rust command', () => {
  const code = readFileSync(join(managerSrc, 'lib/ipc.ts'), 'utf8');
  assert.ok(
    code.includes("downloadAndStageRelease"),
    'ipc must export the download+stage wrapper'
  );
  assert.ok(
    code.includes("'download_and_stage_release'"),
    'wrapper must invoke the download_and_stage_release backend command'
  );
  assert.ok(
    code.includes("'stage-progress'"),
    'wrapper must listen to stage-progress events for live download feedback'
  );
});

test('resolveEditionAsset maps registry truth to real published assets', async () => {
  const { resolveEditionAsset } = await import('../src/lib/registry.ts').catch(
    () => import(join(managerSrc, 'lib/registry.ts'))
  );
  // The registry publishes a standard edition; its asset identity must carry
  // a tag, a filename, and a registry SHA-256 (Artifact Identification Rule).
  const standard = resolveEditionAsset('standard');
  assert.ok(standard, 'registry must resolve a standard edition asset');
  assert.ok(standard.release_tag.length > 0, 'asset must carry its release tag');
  assert.match(standard.filename, /\.7z$/, 'WSA packages are published as 7z archives');
  assert.match(standard.sha256, /^[a-f0-9]{64}$/, 'registry hash must be a sha256 hex digest');
  assert.ok(standard.size_bytes > 0, 'asset must carry its published size');
});

test('StatusCard installs through the registry loop with no fabricated paths', () => {
  const code = readFileSync(join(managerSrc, 'components/StatusCard.tsx'), 'utf8');
  assert.ok(
    code.includes('downloadAndStageRelease'),
    'quick install must go through download -> verify -> extract -> register'
  );
  assert.ok(
    code.includes('resolveEditionAsset'),
    'edition cards must resolve their asset from registry truth'
  );
  assert.ok(
    code.includes('staged.manifest_path'),
    'registration must use the staged manifest, not a guessed path'
  );
  assert.ok(
    !code.includes('C:\\\\Emberbird'),
    'no fabricated default install paths may remain'
  );
});

test('UpdateView stages registry assets instead of suggesting fake paths', () => {
  const code = readFileSync(join(managerSrc, 'components/UpdateView.tsx'), 'utf8');
  assert.ok(
    code.includes('handleDownloadAndStage'),
    'update flow must offer download & stage from the registry'
  );
  assert.ok(
    code.includes('resolveEditionAsset'),
    'download buttons must resolve published assets from the registry'
  );
  assert.ok(
    !code.includes('C:\\\\Emberbird'),
    'no fabricated suggested paths may remain'
  );
});
