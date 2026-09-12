"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Scale } from "lucide-react";
import { LexHubLogo } from "@/components/brand/sanad-logo";
import { useTranslations } from "@/store/locale";

/** Kept for compatibility — hero is now embedded in AuthLayout. */
export function AuthHeroSide() {
  const auth = useTranslations().auth;

  return (
    <div className="auth-hero-side relative hidden overflow-hidden lg:flex lg:w-[45%] lg:flex-col lg:justify-between">
      <div className="relative z-10 flex h-full flex-col justify-between p-12 text-white">
        <Link href="/" className="inline-block">
          <LexHubLogo size="lg" className="drop-shadow-lg" />
        </Link>
        <div>
          <motion.div
            className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl border border-sanad-gold/35 bg-white/10 backdrop-blur-md"
            animate={{ y: [0, -6, 0] }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          >
            <Scale className="h-7 w-7 text-sanad-gold" />
          </motion.div>
          <h1 className="font-serif text-3xl font-semibold leading-tight lg:text-4xl">
            {auth.sideTitle}
          </h1>
          <p className="mt-5 font-serif text-lg leading-relaxed text-sanad-gold/90">
            {auth.sideDesc}
          </p>
        </div>
        <p className="font-serif text-sm text-white/50">{auth.sideSecure}</p>
      </div>
    </div>
  );
}
