"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Briefcase,
  CalendarDays,
  FileText,
  LayoutDashboard,
  Mic,
  Settings,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { ProfilePortraits } from "@/components/ui/profile-portraits";
import { useAuthStore } from "@/store/auth";
import { useLocaleStore, useTranslations } from "@/store/locale";
import { cn } from "@/lib/utils";

export default function HomePage() {
  const user = useAuthStore((s) => s.user);
  const locale = useLocaleStore((s) => s.locale);
  const ar = locale === "ar";
  const home = useTranslations().app.home;
  const today = new Date().toLocaleDateString(ar ? "ar-MA" : "fr-FR", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  const tiles = [
    {
      href: "/dashboard",
      icon: LayoutDashboard,
      label: home.tileDashboard,
      sub: home.tileDashboardSub,
    },
    {
      href: "/agenda",
      icon: CalendarDays,
      label: home.tileAgenda,
      sub: home.tileAgendaSub,
    },
    {
      href: "/redaction",
      icon: Mic,
      label: home.tileRedaction,
      sub: home.tileRedactionSub,
    },
    {
      href: "/cases",
      icon: Briefcase,
      label: home.tileCases,
      sub: home.tileCasesSub,
    },
    {
      href: "/documents",
      icon: FileText,
      label: home.tileDocuments,
      sub: home.tileDocumentsSub,
    },
    {
      href: "/settings",
      icon: Settings,
      label: home.tileSettings,
      sub: home.tileSettingsSub,
    },
  ] as const;

  return (
    <AppShell>
      <div dir={ar ? "rtl" : "ltr"} className="mx-auto max-w-4xl space-y-8">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-3xl border border-[#B08D3F]/30 bg-white/80 px-6 py-7 shadow-[0_20px_50px_-24px_rgba(22,35,63,0.25)] backdrop-blur-md"
        >
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-[#B08D3F]">
            {home.title}
          </p>
          <h1 className="mt-2 font-serif text-3xl font-semibold text-[#16233F]">
            {home.greeting}, {user?.full_name || ""}
          </h1>
          <p className="mt-2 text-sm text-[#2C3B5C]/80">{today}</p>
          <div className="mt-5">
            <ProfilePortraits />
          </div>
        </motion.div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {tiles.map((tile, i) => {
            const Icon = tile.icon;
            return (
              <motion.div
                key={tile.href}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.04 * i }}
              >
                <Link
                  href={tile.href}
                  className={cn(
                    "group flex h-full flex-col gap-3 rounded-2xl border border-white/70 bg-white/75 p-5",
                    "shadow-[0_16px_40px_-20px_rgba(22,35,63,0.2)] backdrop-blur-md transition",
                    "hover:-translate-y-1 hover:border-[#B08D3F]/45 hover:bg-white/95",
                  )}
                >
                  <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#16233F]/90 text-[#E8C577] transition group-hover:scale-105">
                    <Icon className="h-5 w-5" />
                  </span>
                  <span className="font-serif text-lg font-semibold text-[#16233F]">
                    {tile.label}
                  </span>
                  <span className="text-xs leading-relaxed text-[#2C3B5C]/75">{tile.sub}</span>
                </Link>
              </motion.div>
            );
          })}
        </div>
      </div>
    </AppShell>
  );
}
