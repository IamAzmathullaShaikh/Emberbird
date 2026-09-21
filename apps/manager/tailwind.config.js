/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── Base palette (existing — do not remove) ─────────────────────────
        ember: {
          obsidian:  '#0A0A0B',
          charcoal:  '#161618',
          ash:       '#4A4A4A',
          glow:      '#FF5F1F',
          highlight: '#FFB347',
        },
        // ── Semantic aliases (Rule 21 — all views must use these) ─────────
        surface: {
          DEFAULT: '#0A0A0B',   // ember-obsidian
          raised:  '#161618',   // ember-charcoal
          sunken:  '#07070A',
        },
        accent: {
          DEFAULT: '#FF5F1F',   // ember-glow
          hover:   '#FF7A3D',
          active:  '#E54E0E',
        },
        'text': {
          primary:   '#F5F5F5',
          secondary: '#A1A1AA',
          muted:     '#4A4A4A',   // ember-ash
        },
        status: {
          pass:    '#22C55E',
          warn:    '#EAB308',
          fail:    '#EF4444',
          unknown: '#6B7280',
        },
        border: {
          DEFAULT: '#4A4A4A',
          focus:   '#FF5F1F',
          subtle:  'rgba(74,74,74,0.2)',
        },
      },
    },
  },
  plugins: [],
}
