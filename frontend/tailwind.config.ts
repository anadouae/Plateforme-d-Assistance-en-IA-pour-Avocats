import type { Config } from "tailwindcss";

/** Palette refonte Sanad (sanad-redesign.html) */
const ink = "#0E1526";
const inkSoft = "#3B4459";
const parchment = "#F7F5F0";
const gold = "#C7973F";
const goldSoft = "#E8C97C";
const emerald = "#1F6F54";
const emeraldSoft = "#57A88C";

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
          navy: ink,
          ivory: "#FFFFFF",
          gold,
          goldSoft,
          stone: "#E9E6DF",
          cream: parchment,
          slate: ink,
          blue: "#1c274a",
          green: emerald,
          forest: emerald,
          emerald,
          emeraldSoft,
          dark: ink,
          muted: inkSoft,
          light: parchment,
          border: "rgba(14,21,38,0.08)",
          royal: ink,
          royalSoft: "#1c274a",
          ink,
          inkSoft,
          parchment,
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "var(--font-cairo)", "system-ui", "sans-serif"],
        display: ["var(--font-fraunces)", "var(--font-cairo)", "Georgia", "serif"],
        serif: ["var(--font-fraunces)", "var(--font-cairo)", "Georgia", "serif"],
        mono: ["var(--font-plex-mono)", "ui-monospace", "monospace"],
        arabic: ["var(--font-cairo)", "Tahoma", "sans-serif"],
      },
      borderRadius: {
        "sanad-lg": "28px",
        "sanad-md": "18px",
        "sanad-sm": "12px",
      },
      boxShadow: {
        luxe: "0 20px 60px -20px rgba(14,21,38,0.25)",
        gold: "0 8px 28px rgba(199,151,63,0.35)",
        royal: "0 20px 60px rgba(14,21,38,0.28)",
        "sanad-sm": "0 8px 24px -12px rgba(14,21,38,0.18)",
      },
      backgroundImage: {
        "gradient-conic": "conic-gradient(var(--tw-gradient-stops))",
        "sanad-ink": "linear-gradient(155deg, #0E1526, #1c274a)",
        "sanad-gold": "linear-gradient(155deg, #E8C97C, #C7973F)",
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        "pulse-glow": "pulse-glow 3s ease-in-out infinite",
        shimmer: "shimmer 2.5s linear infinite",
        "scale-sway": "scale-sway 4s ease-in-out infinite",
        "blob-drift": "blob-drift 26s ease-in-out infinite",
        rise: "rise 0.5s cubic-bezier(0.2, 0.9, 0.25, 1)",
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
        "blob-drift": {
          "0%": { transform: "translate(0,0) scale(1)" },
          "33%": { transform: "translate(40px,-30px) scale(1.08)" },
          "66%": { transform: "translate(-30px,20px) scale(0.95)" },
          "100%": { transform: "translate(0,0) scale(1)" },
        },
        rise: {
          from: { opacity: "0", transform: "translateY(14px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
