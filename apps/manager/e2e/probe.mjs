import { chromium } from '@playwright/test';
import { spawn } from 'node:child_process';
import { writeFileSync } from 'node:fs';

const port = 9333;
const app = process.argv[2];
if (!app) { console.error('usage: node probe.mjs <exe>'); process.exit(2); }

const child = spawn(app, [], {
  stdio: 'ignore',
  env: { ...process.env, WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS: `--remote-debugging-port=${port}` },
});

const endpoint = `http://127.0.0.1:${port}`;
let browser = null;
for (let i = 0; i < 120 && !browser; i++) {
  try {
    const res = await fetch(`${endpoint}/json/version`);
    if (res.ok) browser = await chromium.connectOverCDP(endpoint);
  } catch { /* not up yet */ }
  if (!browser) await new Promise((r) => setTimeout(r, 500));
}
if (!browser) { console.error('no CDP'); child.kill(); process.exit(1); }

const ctx = browser.contexts()[0];
let page = null;
for (let i = 0; i < 90 && !page; i++) {
  page = ctx.pages().find((p) => !['about:', 'data:', 'chrome-error:', 'edge-error:'].some((pre) => p.url().startsWith(pre)));
  if (!page) await new Promise((r) => setTimeout(r, 500));
}
if (!page) { console.error('no app page'); child.kill(); process.exit(1); }

await page.waitForLoadState('domcontentloaded');
console.log('URL:', page.url());
console.log('TITLE:', await page.title());
console.log('VIEWPORT:', JSON.stringify(await page.evaluate(() => ({ w: window.innerWidth, h: window.innerHeight }))));

const tabs = await page.getByRole('tab').all();
for (const t of tabs) console.log('TAB:', JSON.stringify(await t.innerText()), 'visible:', await t.isVisible());

for (const name of ['Dashboard', 'Updates', 'Backups', 'Restore', 'Doctor', 'Licenses']) {
  const tab = page.getByRole('tab', { name, exact: true });
  if (!(await tab.count())) { console.log(`-- ${name}: NO TAB`); continue; }
  await tab.click();
  await page.waitForTimeout(1500);
  const text = await page.evaluate(() => document.body.innerText);
  writeFileSync(`probe-${name}.txt`, text, 'utf8');
  console.log(`-- ${name}: ${text.length} chars -> probe-${name}.txt`);
}

await browser.close().catch(() => {});
child.kill();
process.exit(0);
