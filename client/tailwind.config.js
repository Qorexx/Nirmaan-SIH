/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        mplads: {
          blue: '#0F2C59',
          navy: '#1A365D',
          gold: '#D69E2E',
          saffron: '#FF9933',
          emerald: '#10B981',
          bg: '#F8FAFC'
        }
      }
    },
  },
  plugins: [],
}
