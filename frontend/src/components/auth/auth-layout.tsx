"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Scale } from "lucide-react";
import { LexHubLogo } from "@/components/brand/sanad-logo";
import { LanguageSwitch } from "@/components/layout/language-switch";
import { AuthParticles } from "@/components/auth/auth-particles";
import { useTranslations } from "@/store/locale";
import { cn } from "@/lib/utils";

interface AuthLayoutProps {
  children: React.ReactNode;
  wide?: boolean;
  /** Masque l’icône balance sur le panneau gauche (écrans confirmation, etc.) */
  hideSideBadge?: boolean;
}

export function AuthLayout({ children, wide = false, hideSideBadge = false }: AuthLayoutProps) {
  const auth = useTranslations().auth;

  return (
    <div className="relative flex min-h-screen overflow-hidden">
      <div className="absolute inset-0 z-0">
        <AuthParticles />
      </div>
      <div
        className="absolute inset-0 z-[1] pointer-events-none"
        style={{
          background: `
            linear-gradient(120deg, rgba(7,16,51,0.55) 0%, rgba(11,26,77,0.28) 48%, rgba(7,16,51,0.45) 100%),
            radial-gradient(ellipse at 72% 28%, rgba(76,124,255,0.18), transparent 52%)
          `,
        }}
      />

      <motion.div
        className="pointer-events-none absolute left-[8%] top-[18%] z-[2] h-40 w-40 rounded-full bg-[rgba(76,124,255,0.22)] blur-3xl"
        animate={{ y: [0, -18, 0], opacity: [0.35, 0.6, 0.35] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="pointer-events-none absolute bottom-[12%] right-[10%] z-[2] h-56 w-56 rounded-full bg-[rgba(27,63,156,0.35)] blur-3xl"
        animate={{ y: [0, 16, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
      />

      <div className="relative z-10 flex min-h-screen w-full flex-col lg:flex-row">
        <div className="flex flex-1 flex-col justify-between p-6 sm:p-10 lg:max-w-[46%] lg:p-14">
          <div className="flex items-center justify-between gap-4">
            <Link href="/" className="inline-block">
              <LexHubLogo size="lg" dark withWordmark className="drop-shadow-lg" />
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
            {!hideSideBadge && (
              <motion.div
                className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl border border-[rgba(140,170,255,0.35)] bg-white/10 shadow-[0_0_40px_rgba(76,124,255,0.35)] backdrop-blur-md"
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              >
                <Scale className="h-7 w-7 text-[#A8C0FF]" />
              </motion.div>
            )}
            <h1 className="font-serif text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl">
              {auth.sideTitle}
            </h1>
            <p className="mt-4 font-serif text-xl leading-relaxed text-[#FF6A00] sm:text-2xl">
              {auth.sideDesc}
            </p>
            <p className="mt-6 font-serif text-sm text-white/60">{auth.sideSecure}</p>
          </motion.div>

          <p className="hidden text-xs text-white/35 lg:block">LexHub · lexhub.space</p>
        </div>

        <div className="relative flex flex-1 items-center justify-center p-4 pb-10 sm:p-8">
          <div className="absolute right-6 top-6 hidden lg:block">
            <LanguageSwitch variant="dark" />
          </div>

          <motion.div
            className={cn("relative z-10 w-full", wide ? "max-w-2xl" : "max-w-md")}
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
