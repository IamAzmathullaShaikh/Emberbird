/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ember: {
          obsidian: '#0A0A0B',
          charcoal: '#161618',
          ash: '#4A4A4A',
          glow: '#FF5F1F',
          highlight: '#FFB347',
        }
      }
    },
  },
  plugins: [],
}
