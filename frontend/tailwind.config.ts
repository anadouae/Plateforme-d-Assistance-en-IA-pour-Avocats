import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        sanad: {
          navy: "#0B1F4A",
          ivory: "#FDFFFF",
          gold: "#D2B589",
          stone: "#E8E4E0",
          cream: "#F5F0E8",
          slate: "#0B1F4A",
          blue: "#1A3A7A",
          green: "#0B1F4A",
          forest: "#0B1F4A",
          dark: "#06122E",
          muted: "#64748b",
          light: "#E8E4E0",
          border: "#E8E4E0",
          royal: "#0B1F4A",
          royalSoft: "#14306B",
        },
      },
      fontFamily: {
        sans: ["var(--font-cairo)", "Georgia", "Times New Roman", "serif"],
        display: ["var(--font-cairo)", "Georgia", "Times New Roman", "serif"],
        serif: ["var(--font-cairo)", "Georgia", "Times New Roman", "serif"],
        arabic: ["var(--font-cairo)", "Tahoma", "sans-serif"],
      },
      boxShadow: {
        luxe: "0 12px 40px rgba(11, 31, 74, 0.18)",
        gold: "0 8px 28px rgba(210, 181, 137, 0.4)",
        royal: "0 20px 60px rgba(11, 31, 74, 0.35)",
      },
      backgroundImage: {
        "gradient-conic": "conic-gradient(var(--tw-gradient-stops))",
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        "pulse-glow": "pulse-glow 3s ease-in-out infinite",
        shimmer: "shimmer 2.5s linear infinite",
        "scale-sway": "scale-sway 4s ease-in-out infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-12px)" },
        },
        "pulse-glow": {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "0.8" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "scale-sway": {
          "0%, 100%": { transform: "rotate(-2deg)" },
          "50%": { transform: "rotate(2deg)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
