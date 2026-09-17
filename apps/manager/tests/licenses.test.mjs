import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const managerSrc = path.resolve(import.meta.dirname, '../src');

test('NavigationTab type includes licenses screen', () => {
  const typesContent = fs.readFileSync(path.join(managerSrc, 'lib/types.ts'), 'utf8');
  assert.match(typesContent, /'licenses'/, 'NavigationTab union includes licenses');
});

test('Header component defines licenses navigation tab', () => {
  const headerContent = fs.readFileSync(path.join(managerSrc, 'components/Header.tsx'), 'utf8');
  assert.match(headerContent, /id:\s*'licenses'/, 'Header includes licenses tab');
  assert.match(headerContent, /label:\s*'Licenses'/, 'Header tab label is Licenses');
});

test('LicensesView component defines legal and attribution disclosures', () => {
  const licensesPath = path.join(managerSrc, 'components/LicensesView.tsx');
  assert.ok(fs.existsSync(licensesPath), 'LicensesView.tsx component exists');
  const content = fs.readFileSync(licensesPath, 'utf8');
  assert.match(content, /AGPL-3\.0/, 'Discloses AGPL-3.0 platform license');
  assert.match(content, /GPL-3\.0/, 'Discloses Magisk GPL-3.0 license');
  assert.match(content, /CC-BY-NC-ND-4\.0/, 'Discloses documentation CC license');
  assert.match(content, /WSABuilds/, 'Preserves MustardChef / WSABuilds attribution');
});
