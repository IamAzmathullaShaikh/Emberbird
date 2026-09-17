import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const managerSrc = path.resolve(import.meta.dirname, '../src');

test('NavigationTab type includes doctor screen and DoctorReport interfaces', () => {
  const typesContent = fs.readFileSync(path.join(managerSrc, 'lib/types.ts'), 'utf8');
  assert.match(typesContent, /'doctor'/, 'NavigationTab union includes doctor');
  assert.match(typesContent, /interface DoctorProbe/, 'Defines DoctorProbe interface');
  assert.match(typesContent, /interface DoctorReportData/, 'Defines DoctorReportData interface');
});

test('Header component defines doctor navigation tab', () => {
  const headerContent = fs.readFileSync(path.join(managerSrc, 'components/Header.tsx'), 'utf8');
  assert.match(headerContent, /id:\s*'doctor'/, 'Header includes doctor tab');
  assert.match(headerContent, /label:\s*'Doctor'/, 'Header tab label is Doctor');
});

test('DoctorView component defines all diagnostic probes PRB-01 through PRB-12', () => {
  const doctorPath = path.join(managerSrc, 'components/DoctorView.tsx');
  assert.ok(fs.existsSync(doctorPath), 'DoctorView.tsx component exists');
  const content = fs.readFileSync(doctorPath, 'utf8');
  for (let i = 1; i <= 12; i++) {
    const probeId = `PRB-${String(i).padStart(2, '0')}`;
    assert.match(content, new RegExp(probeId), `DoctorView defines ${probeId}`);
  }
  assert.match(content, /Ember Doctor/, 'Renders Ember Doctor header');
  assert.match(content, /Actionable Remediations/, 'Includes Actionable Remediations section');
});

test('App component mounts DoctorView on activeTab doctor', () => {
  const appContent = fs.readFileSync(path.join(managerSrc, 'App.tsx'), 'utf8');
  assert.match(appContent, /import\s*\{\s*DoctorView\s*\}\s*from\s*'\.\/components\/DoctorView'/, 'App imports DoctorView');
  assert.match(appContent, /activeTab\s*===\s*'doctor'/, 'App switches to DoctorView');
});
