/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.{html,js}",
    "./accounts/templates/**/*.{html,js}",
    "./home/templates/**/*.{html,js}",
    "./jobs/templates/**/*.{html,js}",
    "./static/js/**/*.{js,jsx}"
  ],
  theme: {
    extend: {
      colors: {
        primary: "#3b82f6",
        secondary: "#64748b",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};