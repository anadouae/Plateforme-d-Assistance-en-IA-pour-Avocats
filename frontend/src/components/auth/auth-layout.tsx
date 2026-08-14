"use client";

import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { Scale } from "lucide-react";
import { SanadLogo } from "@/components/brand/sanad-logo";
import { LanguageSwitch } from "@/components/layout/language-switch";
import { useTranslations } from "@/store/locale";
import { cn } from "@/lib/utils";

interface AuthLayoutProps {
  children: React.ReactNode;
  wide?: boolean;
}

export function AuthLayout({ children, wide = false }: AuthLayoutProps) {
  const auth = useTranslations().auth;

  return (
    <div className="relative flex min-h-screen overflow-hidden">
      {/* Full-bleed cabinet / library background */}
      <Image
        src="/hero-cabinet.png"
        alt=""
        fill
        priority
        className="object-cover object-center"
        sizes="100vw"
      />
      <div
        className="absolute inset-0 z-[1]"
        style={{
          background: `
            linear-gradient(120deg, rgba(11,31,74,0.94) 0%, rgba(11,31,74,0.72) 42%, rgba(6,18,46,0.55) 100%),
            radial-gradient(ellipse at 70% 30%, rgba(210,181,137,0.22), transparent 50%)
          `,
        }}
      />

      {/* Floating gold orbs */}
      <motion.div
        className="pointer-events-none absolute left-[8%] top-[18%] z-[2] h-40 w-40 rounded-full bg-sanad-gold/20 blur-3xl"
        animate={{ y: [0, -18, 0], opacity: [0.35, 0.6, 0.35] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="pointer-events-none absolute bottom-[12%] right-[10%] z-[2] h-56 w-56 rounded-full bg-[#14306B]/50 blur-3xl"
        animate={{ y: [0, 16, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
      />

      <div className="relative z-10 flex min-h-screen w-full flex-col lg:flex-row">
        {/* Left copy panel */}
        <div className="flex flex-1 flex-col justify-between p-6 sm:p-10 lg:max-w-[46%] lg:p-14">
          <div className="flex items-center justify-between gap-4">
            <Link href="/" className="inline-block">
              <SanadLogo size="lg" dark withWordmark className="drop-shadow-lg" />
            </Link>
            <div className="lg:hidden">
              <LanguageSwitch variant="dark" />
            </div>
          </div>

          <motion.div
            className="my-10 max-w-md lg:my-0"
            initial={{ opacity: 0, y: 28 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
          >
            <motion.div
              className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl border border-sanad-gold/40 bg-white/10 shadow-[0_0_40px_rgba(210,181,137,0.35)] backdrop-blur-md"
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            >
              <Scale className="h-7 w-7 text-sanad-gold" />
            </motion.div>
            <h1 className="font-serif text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl">
              {auth.sideTitle}
            </h1>
            <p className="mt-4 font-serif text-xl leading-relaxed text-sanad-gold sm:text-2xl">
              {auth.sideDesc}
            </p>
            <p className="mt-6 font-serif text-sm text-white/60">{auth.sideSecure}</p>
          </motion.div>

          <p className="hidden text-xs text-white/35 lg:block">WebVoice · Sanad</p>
        </div>

        {/* Right glass form */}
        <div className="relative flex flex-1 items-center justify-center p-4 pb-10 sm:p-8">
          <div className="absolute right-6 top-6 hidden lg:block">
            <LanguageSwitch variant="dark" />
          </div>

          <motion.div
            className={cn("w-full", wide ? "max-w-2xl" : "max-w-md")}
            initial={{ opacity: 0, y: 24, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
          >
            {children}
          </motion.div>
        </div>
      </div>
    </div>
  );
}
