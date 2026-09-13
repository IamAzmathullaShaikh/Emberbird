import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const repoRoot = path.resolve(__dirname, '../../');
const sourceDataDir = path.join(repoRoot, 'compatibility', 'data');
const targetContentDir = path.join(__dirname, '../src/content/compatibility');

function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

console.log('[*] Importing compatibility records from repository compatibility/data/ into website/src/content/compatibility/...');
ensureDir(targetContentDir);

if (!fs.existsSync(sourceDataDir)) {
  console.log(`[-] Source directory ${sourceDataDir} not found.`);
  process.exit(1);
}

const entries = fs.readdirSync(sourceDataDir, { withFileTypes: true });
let importedCount = 0;

for (const entry of entries) {
  if (entry.isFile() && entry.name.endsWith('.json') && entry.name !== '.gitkeep') {
    const srcFile = path.join(sourceDataDir, entry.name);
    const destFile = path.join(targetContentDir, entry.name);

    try {
      const raw = fs.readFileSync(srcFile, 'utf-8');
      const parsed = jsonValidation(raw, entry.name);

      fs.writeFileSync(destFile, JSON.stringify(parsed, null, 2) + '\n', 'utf-8');
      importedCount++;
      console.log(`[+] Imported compatibility record: ${entry.name}`);
    } catch (err) {
      console.error(`[-] Error importing ${entry.name}:`, err.message);
      process.exit(1);
    }
  }
}

function jsonValidation(content, filename) {
  const data = JSON.parse(content);
  const required = ['app_name', 'package_id', 'category', 'compatibility_status', 'play_integrity_required'];
  for (const field of required) {
    if (data[field] === undefined) {
      throw new Error(`Record ${filename} is missing required field '${field}'`);
    }
  }
  return data;
}

console.log(`[+] Compatibility import complete. Total records imported: ${importedCount}`);
