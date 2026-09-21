/**
 * Tailwind v3 pipeline.
 *
 * This replaces `@astrojs/tailwind`, which is abandoned upstream and pins
 * `astro` to `^3 || ^4 || ^5`, blocking the security upgrade. Astro applies
 * this PostCSS config automatically; `src/styles/global.css` already carries
 * the `@tailwind base/components/utilities` directives.
 */
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {}
  }
};
