"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import { Lock, Scale } from "lucide-react";
import { AnimatedButton } from "@/components/motion/animated-button";
import { useTranslations } from "@/store/locale";

export function HeroParallax() {
  const t = useTranslations().hero;

  return (
    <section className="hero-parallax-section relative overflow-hidden">
      <Image
        src="/hero-cabinet.png"
        alt=""
        fill
        priority
        sizes="100vw"
        className="object-cover object-center"
      />

      <motion.div
        className="pointer-events-none absolute inset-0 z-[1]"
        initial={{ opacity: 0.85 }}
        animate={{ opacity: 1 }}
        style={{
          background: `
            linear-gradient(
              105deg,
              rgba(34, 45, 82, 0.92) 0%,
              rgba(34, 45, 82, 0.82) 38%,
              rgba(34, 45, 82, 0.55) 68%,
              rgba(34, 45, 82, 0.35) 100%
            ),
            linear-gradient(
              to top,
              rgba(34, 45, 82, 0.75) 0%,
              transparent 45%
            )
          `,
        }}
      />

      {/* Soft floating gold orbs */}
      <motion.div
        aria-hidden
        className="pointer-events-none absolute -left-20 top-24 z-[2] h-56 w-56 rounded-full bg-sanad-gold/20 blur-3xl"
        animate={{ y: [0, 24, 0], opacity: [0.35, 0.55, 0.35] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        aria-hidden
        className="pointer-events-none absolute -right-10 bottom-32 z-[2] h-64 w-64 rounded-full bg-sanad-gold/15 blur-3xl"
        animate={{ y: [0, -20, 0], opacity: [0.25, 0.45, 0.25] }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
      />

      <div className="hero-parallax-overlay relative z-10">
        <div className="mx-auto flex h-full max-w-4xl flex-col justify-center px-4 pt-20 sm:px-6 lg:px-8">
          <motion.div
            className="relative z-10 mx-auto max-w-2xl text-center lg:text-left"
            initial={{ opacity: 0, y: 48 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
          >
            <motion.div
              className="glass-badge mb-6 inline-flex items-center gap-2"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2, duration: 0.6 }}
              whileHover={{ scale: 1.04 }}
            >
              <Scale className="h-3.5 w-3.5 text-sanad-gold" />
              {t.badge}
            </motion.div>

            <h1 className="font-display text-4xl font-semibold leading-[1.08] tracking-tight text-sanad-ivory sm:text-5xl lg:text-6xl">
              <motion.span
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3, duration: 0.7 }}
                className="block drop-shadow-[0_2px_12px_rgba(34,45,82,0.8)]"
              >
                {t.title}
              </motion.span>
              <motion.span
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.45, duration: 0.7 }}
                className="mt-2 block bg-gradient-to-r from-sanad-gold via-[#f0e0c8] to-sanad-gold bg-[length:200%_auto] bg-clip-text text-transparent drop-shadow-sm"
                style={{ animation: "shimmer 3.5s linear infinite" }}
              >
                {t.subtitle}
              </motion.span>
            </h1>

            <motion.p
              className="mt-6 text-lg leading-relaxed text-sanad-ivory/90 drop-shadow-[0_1px_8px_rgba(34,45,82,0.7)]"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6, duration: 0.7 }}
            >
              {t.description}
            </motion.p>

            <motion.div
              className="mt-9 flex flex-wrap justify-center gap-4 lg:justify-start"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.75, duration: 0.6 }}
            >
              <AnimatedButton href="/register" variant="gold">
                {t.ctaRegister}
              </AnimatedButton>
              <AnimatedButton href="/login" variant="outline">
                {t.ctaLogin}
              </AnimatedButton>
              <AnimatedButton href="/about" variant="ghost">
                {t.ctaAbout}
              </AnimatedButton>
            </motion.div>

            <motion.p
              className="mt-6 flex items-center justify-center gap-2 text-xs text-sanad-ivory/70 lg:justify-start"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.9 }}
            >
              <Lock className="h-3.5 w-3.5 text-sanad-gold" />
              {t.secure}
            </motion.p>
          </motion.div>
        </div>
      </div>

      <div className="absolute bottom-0 left-0 right-0 z-20 overflow-hidden border-t border-sanad-gold/20 bg-sanad-navy/80 py-3 backdrop-blur-xl">
        <motion.div
          className="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-6 px-4 text-xs text-sanad-ivory/60 sm:justify-between sm:px-8"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1 }}
        >
          <span className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sanad-gold opacity-40" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-sanad-gold" />
            </span>
            {t.ticker1}
          </span>
          <motion.span whileHover={{ color: "#D2B589" }}>{t.ticker2}</motion.span>
          <motion.span whileHover={{ color: "#D2B589" }}>{t.ticker3}</motion.span>
          <motion.span whileHover={{ color: "#D2B589" }}>{t.ticker4}</motion.span>
        </motion.div>
      </div>
    </section>
  );
}
