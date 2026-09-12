import type { Config } from "tailwindcss";

/** Palette LexHub — bleu royal + accent */
const ink = "#0A1228";
const inkSoft = "#4A5568";
const parchment = "#EEF1F8";
const gold = "#FF6A00"; /* TEST orange vif */
const goldSoft = "#FFB07A";
const emerald = "#1F6F54";
const emeraldSoft = "#57A88C";
const royal950 = "#071033";
const royal900 = "#0B1A4D";
const royal800 = "#12307A";
const royal700 = "#1B3F9C";
const royalGlow = "#4C7CFF";

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
          ivory: "#FBFCFE",
          gold,
          goldSoft,
          stone: "#DCE4F5",
          cream: parchment,
          slate: ink,
          blue: royal800,
          green: emerald,
          forest: emerald,
          emerald,
          emeraldSoft,
          dark: ink,
          muted: inkSoft,
          light: parchment,
          border: "rgba(10,18,40,0.09)",
          royal: royal900,
          royalSoft: royal700,
          royalGlow,
          ink,
          inkSoft,
          parchment,
        },
        // Alias marque (préférer lexhub-* dans le nouveau code)
        lexhub: {
          navy: ink,
          ivory: "#FBFCFE",
          gold,
          goldSoft,
          stone: "#DCE4F5",
          cream: parchment,
          slate: ink,
          blue: royal800,
          green: emerald,
          forest: emerald,
          emerald,
          emeraldSoft,
          dark: ink,
          muted: inkSoft,
          light: parchment,
          border: "rgba(10,18,40,0.09)",
          royal: royal900,
          royalSoft: royal700,
          royalGlow,
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
        "lexhub-lg": "28px",
        "lexhub-md": "18px",
        "lexhub-sm": "12px",
      },
      boxShadow: {
        luxe: "0 20px 60px -20px rgba(7,16,51,0.32)",
        gold: "0 8px 28px rgba(201,168,74,0.35)",
        royal: "0 20px 60px rgba(11,26,77,0.35)",
        "royal-glow": "0 0 40px rgba(76,124,255,0.35)",
        "sanad-sm": "0 8px 24px -12px rgba(11,26,77,0.2)",
      },
      backgroundImage: {
        "gradient-conic": "conic-gradient(var(--tw-gradient-stops))",
        "sanad-ink": `linear-gradient(155deg, ${royal700}, ${royal900})`,
        "sanad-gold": `linear-gradient(155deg, ${goldSoft}, ${gold})`,
        "sanad-royal": `linear-gradient(165deg, ${royal900} 0%, ${royal950} 55%, ${ink} 100%)`,
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
