// frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}", // Scan React components
    "./public/index.html",       // Scan the main HTML file
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
