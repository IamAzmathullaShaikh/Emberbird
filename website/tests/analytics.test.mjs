import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const repoRoot = path.resolve(import.meta.dirname, '../../');
const metricsFile = path.join(repoRoot, 'website', 'src', 'data', 'analytics-metrics.json');

test('website imported analytics metrics exist and adhere to zero PII', () => {
  assert.ok(fs.existsSync(metricsFile), 'website analytics-metrics.json must exist');

  const content = fs.readFileSync(metricsFile, 'utf8');
  const data = JSON.parse(content);

  assert.equal(data.schema_version, '1.0.0');
  assert.equal(data.transparency_principles.zero_pii, true);
  assert.equal(data.transparency_principles.no_ip_logging, true);
  assert.equal(data.transparency_principles.no_cookies, true);
  assert.equal(data.transparency_principles.public_aggregates_only, true);

  // Verify release metrics
  assert.ok(data.release_metrics.total_releases > 0);
  assert.ok(data.release_metrics.total_downloads_aggregate > 0);
  assert.ok(data.release_metrics.latest_version);

  // Verify compatibility metrics
  assert.ok(data.compatibility_metrics.total_apps_tested > 0);

  // Verify distribution sums
  const rootTotal =
    data.root_flavor_distribution.magisk +
    data.root_flavor_distribution.kernelsu +
    data.root_flavor_distribution.none;
  assert.equal(rootTotal, 100);

  const archTotal =
    data.architecture_distribution.x64 +
    data.architecture_distribution.arm64;
  assert.equal(archTotal, 100);
});
