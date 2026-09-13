import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const repoRoot = path.resolve(__dirname, '../../');
const sourceDocsDir = path.join(repoRoot, 'docs');
const targetContentDir = path.join(__dirname, '../src/content/docs');

const categoryOrder = {
  'getting-started': 1,
  'configuration': 2,
  'troubleshooting': 3,
  'community': 4
};

function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

function extractMetadata(content, defaultCategory) {
  const lines = content.split('\n');
  let title = 'Documentation Article';
  let description = 'WSABuilds technical guide.';
  let bodyLines = [];
  let inFrontmatter = false;
  let hasExistingFrontmatter = false;

  if (lines[0]?.trim() === '---') {
    hasExistingFrontmatter = true;
    inFrontmatter = true;
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (hasExistingFrontmatter && i > 0 && line.trim() === '---') {
      inFrontmatter = false;
      continue;
    }
    if (inFrontmatter) continue;

    if (!hasExistingFrontmatter && line.startsWith('# ')) {
      title = line.replace('# ', '').trim();
      // Look for next non-empty line as description
      for (let j = i + 1; j < lines.length; j++) {
        const nextLine = lines[j].trim();
        if (nextLine && !nextLine.startsWith('#') && !nextLine.startsWith('---')) {
          description = nextLine.replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1').slice(0, 160);
          break;
        }
      }
      continue;
    }
    bodyLines.push(line);
  }

  return {
    title,
    description,
    category: defaultCategory,
    order: categoryOrder[defaultCategory] || 10,
    body: bodyLines.join('\n').trim()
  };
}

function processDirectory(dir, category) {
  if (!fs.existsSync(dir)) return;
  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      processDirectory(fullPath, entry.name);
    } else if (entry.isFile() && entry.name.endsWith('.md') && entry.name !== 'README.md') {
      const content = fs.readFileSync(fullPath, 'utf-8');
      const meta = extractMetadata(content, category || 'getting-started');

      const targetSubdir = path.join(targetContentDir, category || 'getting-started');
      ensureDir(targetSubdir);

      const targetPath = path.join(targetSubdir, entry.name);
      const finalContent = `---
title: "${meta.title.replace(/"/g, '\"')}"
description: "${meta.description.replace(/"/g, '\"')}"
category: "${meta.category}"
order: ${meta.order}
---

${meta.body}
`;
      fs.writeFileSync(targetPath, finalContent, 'utf-8');
      console.log(`[+] Synced documentation: ${path.relative(repoRoot, fullPath)} -> ${path.relative(repoRoot, targetPath)}`);
    }
  }
}

console.log('[*] Importing documentation from repository root docs/ into website/src/content/docs/...');
ensureDir(targetContentDir);
processDirectory(sourceDocsDir, '');
console.log('[+] Documentation import complete.');
