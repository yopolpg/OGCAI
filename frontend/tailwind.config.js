/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#090d16',
        surface: '#0f172a',
        'surface-card': 'rgba(15, 23, 42, 0.75)',
        'surface-border': 'rgba(51, 65, 85, 0.6)',
        'accent-cyan': '#38bdf8',
        'accent-emerald': '#34d399',
        'accent-purple': '#a855f7',
        'accent-yellow': '#fbbf24',
        'accent-pink': '#f472b6',
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}
