import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import { assertValidEnvironment } from './src/lib/env';

// Run environment validation check during build/startup
const siteUrl = process.env.SITE_URL;
if (!siteUrl) {
  throw new Error('Configuration error: SITE_URL environment variable is required.');
}

export default defineConfig({
  site: siteUrl,
  output: 'static',
  integrations: [tailwind()]
});
