/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
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
};
