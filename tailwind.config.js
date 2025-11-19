module.exports = {
  content: [
    "./templates/**/*.html",
    "./**/templates/**/*.html",
    "./static/js/**/*.js",
    "./static/css/**/*.css",
    "./**/*.html",
    "./messaging/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#42547C",
        accent: "#EFCE63",
        success: "#26B509",
        warning: "#F36E6E",
      },
      fontFamily: {
        montserrat: ["Montserrat", "sans-serif"],
        arimo: ["Arimo", "sans-serif"],
      },
    },
  },
  plugins: [],
};
