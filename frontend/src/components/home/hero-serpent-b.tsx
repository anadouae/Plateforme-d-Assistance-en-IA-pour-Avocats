"use client";

import { motion, useReducedMotion } from "framer-motion";

/**
 * Hero B v2 — rideaux cinéma + lueur dorée (plus sobre, moins « serpent / bille »).
 */
export function HeroSerpentBackdrop() {
  const reduce = useReducedMotion();

  if (reduce) return null;

  return (
    <div className="pointer-events-none absolute inset-0 z-[2] overflow-hidden" aria-hidden>
      {/* Rideaux qui s'écartent */}
      <motion.div
        className="absolute inset-y-0 left-0 w-1/2 bg-gradient-to-r from-[#050d28] via-[#071033]/95 to-transparent"
        initial={{ x: 0 }}
        animate={{ x: "-102%" }}
        transition={{ duration: 1.05, ease: [0.76, 0, 0.24, 1] }}
      />
      <motion.div
        className="absolute inset-y-0 right-0 w-1/2 bg-gradient-to-l from-[#050d28] via-[#071033]/95 to-transparent"
        initial={{ x: 0 }}
        animate={{ x: "102%" }}
        transition={{ duration: 1.05, ease: [0.76, 0, 0.24, 1] }}
      />

      {/* Liserés bleu / orange discrets sur les bords */}
      <motion.div
        className="absolute inset-y-0 left-0 w-px bg-gradient-to-b from-transparent via-[#4C7CFF]/70 to-transparent"
        initial={{ opacity: 0, scaleY: 0.2 }}
        animate={{ opacity: 1, scaleY: 1 }}
        transition={{ duration: 0.8, delay: 0.5 }}
      />
      <motion.div
        className="absolute inset-y-0 right-0 w-px bg-gradient-to-b from-transparent via-[#FF6A00]/60 to-transparent"
        initial={{ opacity: 0, scaleY: 0.2 }}
        animate={{ opacity: 1, scaleY: 1 }}
        transition={{ duration: 0.8, delay: 0.55 }}
      />

      {/* Halo doré fixe — pas de bille qui roule */}
      <motion.div
        className="lr-hero-orbit absolute left-1/2 top-[42%] h-48 w-48 -translate-x-1/2 -translate-y-1/2 rounded-full"
        initial={{ opacity: 0, scale: 0.85 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.2, delay: 0.35, ease: "easeOut" }}
      />
    </div>
  );
}

export function useHeroRevealDelay() {
  const reduce = useReducedMotion();
  return reduce ? 0 : 0.42;
}
