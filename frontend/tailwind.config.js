/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        dark: {
          900: "#0b1020",
          800: "#111827",
          700: "#1f2937",
          600: "#374151",
        },
      },
    },
  },
  plugins: [],
};
