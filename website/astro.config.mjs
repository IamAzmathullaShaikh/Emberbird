import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import { loadEnv } from 'vite';
import { assertValidEnvironment } from './src/lib/env';

// Run environment validation check during build/startup
const env = loadEnv(process.env.NODE_ENV || '', process.cwd(), '');
const combinedEnv = { ...env, ...process.env };
assertValidEnvironment(combinedEnv);
const siteUrl = combinedEnv.SITE_URL;

export default defineConfig({
  site: siteUrl,
  output: 'static',
  integrations: [tailwind()]
});
