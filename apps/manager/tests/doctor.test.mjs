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

test('ipc exposes runDoctorScan bound to the Rust command', () => {
  const ipc = fs.readFileSync(path.join(managerSrc, 'lib/ipc.ts'), 'utf8');
  assert.match(ipc, /runDoctorScan/, 'ipc exports the doctor scan wrapper');
  assert.match(
    ipc,
    /invokeTauri<DoctorProbe\[\]>\('run_doctor_scan'\)/,
    'wrapper invokes the run_doctor_scan backend command'
  );
});

test('DoctorView scans through the ipc wrapper and renders failures honestly', () => {
  const doctorPath = path.join(managerSrc, 'components/DoctorView.tsx');
  assert.ok(fs.existsSync(doctorPath), 'DoctorView.tsx component exists');
  const content = fs.readFileSync(doctorPath, 'utf8');
  assert.match(content, /runDoctorScan/, 'DoctorView scans through the typed ipc wrapper');
  assert.ok(
    !content.includes('@tauri-apps/api/core'),
    'DoctorView must not invoke Tauri directly'
  );
  assert.match(content, /Ember Doctor/, 'Renders Ember Doctor header');
  assert.match(content, /Actionable Remediations/, 'Includes Actionable Remediations section');
  assert.match(content, /scan failed/i, 'Renders an explicit scan-failure state (Zero-Mock law)');
  assert.match(content, /Retry Scan/, 'Offers a retry after a failed scan');
});

test('App component mounts DoctorView on activeTab doctor', () => {
  const appContent = fs.readFileSync(path.join(managerSrc, 'App.tsx'), 'utf8');
  assert.match(appContent, /import\s*\{\s*DoctorView\s*\}\s*from\s*'\.\/components\/DoctorView'/, 'App imports DoctorView');
  assert.match(appContent, /activeTab\s*===\s*'doctor'/, 'App switches to DoctorView');
});
