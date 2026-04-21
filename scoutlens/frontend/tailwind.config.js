/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: "#1a1a2e",
          light: "#16213e",
          dark: "#0f0f1a",
        },
        teal: {
          DEFAULT: "#16a085",
          light: "#1abc9c",
          dark: "#0e8c73",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
