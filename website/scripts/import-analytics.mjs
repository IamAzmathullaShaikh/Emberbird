import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const repoRoot = path.resolve(__dirname, '../../');
const sourceMetricsFile = path.join(repoRoot, 'services', 'analytics', 'metrics.json');
const targetContentDir = path.join(__dirname, '../src/content/analytics');
const targetFile = path.join(targetContentDir, 'metrics.json');

const PII_FORBIDDEN_KEYS = new Set([
  'ip',
  'ip_address',
  'client_ip',
  'user_id',
  'username',
  'email',
  'device_id',
  'mac_address',
  'telemetry_id',
  'cookie',
  'session_id',
]);

function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

function assertZeroPii(obj, prefix = '') {
  for (const [key, value] of Object.entries(obj)) {
    const fullPath = prefix ? `${prefix}.${key}` : key;
    if (PII_FORBIDDEN_KEYS.has(key.toLowerCase())) {
      throw new Error(`PII Violation: Forbidden key '${fullPath}' found in analytics payload.`);
    }
    if (value && typeof value === 'object') {
      if (Array.isArray(value)) {
        value.forEach((item, idx) => {
          if (item && typeof item === 'object') {
            assertZeroPii(item, `${fullPath}[${idx}]`);
          }
        });
      } else {
        assertZeroPii(value, fullPath);
      }
    }
  }
}

function validateAnalyticsPayload(raw) {
  const data = JSON.parse(raw);

  const requiredSections = [
    'schema_version',
    'last_updated',
    'transparency_principles',
    'release_metrics',
    'compatibility_metrics',
    'root_flavor_distribution',
    'architecture_distribution',
    'version_adoption',
  ];

  for (const section of requiredSections) {
    if (data[section] === undefined) {
      throw new Error(`Analytics data is missing required section '${section}'`);
    }
  }

  if (!data.transparency_principles.zero_pii) {
    throw new Error('Analytics transparency principle zero_pii must be true');
  }

  assertZeroPii(data);
  return data;
}

console.log('[*] Importing analytics metrics from services/analytics/ into website/src/content/analytics/...');
ensureDir(targetContentDir);

if (!fs.existsSync(sourceMetricsFile)) {
  console.error(`[-] Source metrics file not found: ${sourceMetricsFile}`);
  process.exit(1);
}

try {
  const raw = fs.readFileSync(sourceMetricsFile, 'utf-8');
  const validated = validateAnalyticsPayload(raw);

  fs.writeFileSync(targetFile, JSON.stringify(validated, null, 2) + '\n', 'utf-8');
  console.log(`[+] Successfully imported analytics metrics to ${targetFile}`);
  console.log(`[+] Verified Privacy-First Zero-PII Compliance.`);
} catch (err) {
  console.error(`[-] Failed to import analytics: ${err.message}`);
  process.exit(1);
}
