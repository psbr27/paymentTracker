/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Category colors
        loan: '#EF4444',
        subscription: '#3B82F6',
        investment: '#22C55E',
        insurance: '#F97316',
        utility: '#A855F7',
        other: '#6B7280',
        // App colors
        primary: '#3B82F6',
        secondary: '#6B7280',
      },
    },
  },
  plugins: [],
}
