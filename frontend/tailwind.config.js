/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "rgb(var(--canvas) / <alpha-value>)",
        surface: "rgb(var(--surface) / <alpha-value>)",
        ink: "rgb(var(--ink) / <alpha-value>)",
        muted: "rgb(var(--muted) / <alpha-value>)",
        line: "rgb(var(--line) / <alpha-value>)",
        primary: "rgb(var(--primary) / <alpha-value>)",
      },
      boxShadow: {
        card: "0 2px 8px rgba(15, 23, 42, .035), 0 12px 30px rgba(15, 23, 42, .035)",
      },
      borderRadius: {
        card: "16px",
      },
    },
  },
  plugins: [],
};
