import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

const siteUrl = process.env.SITE_URL;
if (!siteUrl) {
  throw new Error('Configuration error: SITE_URL environment variable is required.');
}

export default defineConfig({
  site: siteUrl,
  output: 'static',
  integrations: [tailwind()]
});
