/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,html}"
  ],
  theme: {
    extend: {
      colors: {
        atlas: {
          primary: '#3b82f6',
          secondary: '#10b981',
          dark: '#1f2937',
          light: '#f3f4f6'
        }
      }
    }
  },
  plugins: []
}
