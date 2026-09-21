import { defineConfig } from 'astro/config';
import { loadEnv } from 'vite';
import { assertValidEnvironment } from './src/lib/env';

// Run environment validation check during build/startup
const env = loadEnv(process.env.NODE_ENV || '', process.cwd(), '');
const combinedEnv = { ...env, ...process.env };
assertValidEnvironment(combinedEnv);
const siteUrl = combinedEnv.SITE_URL;

// Tailwind runs through Astro's built-in PostCSS pipeline (postcss.config.mjs)
// rather than @astrojs/tailwind: that integration is abandoned upstream (its
// latest release peers on astro ^3 || ^4 || ^5 only), which is what forced the
// dependency upgrade in the first place.
export default defineConfig({
  site: siteUrl,
  output: 'static'
});
