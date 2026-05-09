import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        emerald: {
          50: "#f0f7f4",
          100: "#d9eee5",
          200: "#b3ddcb",
          300: "#8dccb1",
          400: "#66bb97",
          500: "#409a75",
          600: "#0f6b46",
          700: "#0c5538",
          800: "#093f2a",
          900: "#06291c"
        },
        background: "#f7fbf8",
        foreground: "#0e1b16"
      },
      borderRadius: {
        xl: "0.75rem",
        "2xl": "1rem"
      },
      boxShadow: {
        card: "0 10px 25px -15px rgba(15, 107, 70, 0.35)"
      }
    }
  },
  plugins: [require("tailwindcss-animate")]
};

export default config;
