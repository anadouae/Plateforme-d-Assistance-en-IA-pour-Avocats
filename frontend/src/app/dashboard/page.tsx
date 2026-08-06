"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Briefcase,
  FileText,
  FolderOpen,
  Mic,
  Plus,
  Sparkles,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { api, type CaseListItem } from "@/lib/api";
import { isAssistant, roleLabel } from "@/lib/roles";
import { useAuthStore } from "@/store/auth";
import { useTranslations } from "@/store/locale";
import { cn } from "@/lib/utils";
import { TiltCard } from "@/components/motion/tilt-card";
import { Magnetic } from "@/components/motion/magnetic";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/motion/fade-in";
import { CometCard } from "@/components/ui/comet-card";
import { NoiseBackground } from "@/components/ui/noise-background";

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const t = useTranslations().app.dashboard;
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const assistantMode = isAssistant(user?.role);

  useEffect(() => {
    api.getCases().then(setCases).catch(() => setCases([]));
  }, []);

  const activeCount = cases.filter((c) => c.status !== "Clôturé").length;
  const recentCases = cases.slice(0, 6);

  const actions = assistantMode
    ? [
        {
          href: "/cases",
          title: "Dossiers",
          desc: "Consultez les affaires et organisez les pièces",
          icon: FolderOpen,
          primary: true,
        },
        {
          href: "/documents",
          title: "Documents",
          desc: "Uploadez et classez les pièces pour l’avocat",
          icon: FileText,
          primary: false,
        },
        {
          href: "/agenda",
          title: "Planning",
          desc: "Échéances et audiences liées aux dossiers",
          icon: Briefcase,
          primary: false,
        },
      ]
    : [
        {
          href: "/redaction",
          title: "Plaidoirie",
          desc: "Dictez → corrigez → document officiel",
          icon: Mic,
          primary: true,
        },
        {
          href: "/cases",
          title: "Dossiers",
          desc: "Affaires, pièces et historique du cabinet",
          icon: FolderOpen,
          primary: false,
        },
        {
          href: "/documents",
          title: "Documents",
          desc: "Upload, OCR et synthèse des pièces",
          icon: FileText,
          primary: false,
        },
      ];

  return (
    <AppShell>
      <div className="space-y-8">
        <FadeIn>
          <div className="relative overflow-hidden rounded-3xl bg-sanad-navy px-6 py-8 text-white shadow-luxe sm:px-10">
            <div className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full bg-sanad-gold/15 blur-3xl" />
            <div className="pointer-events-none absolute -bottom-20 left-10 h-48 w-48 rounded-full bg-sanad-gold/10 blur-3xl" />

            <div className="relative flex flex-wrap items-center justify-between gap-6">
              <div className="max-w-xl">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sanad-gold">
                  Sanad · {roleLabel(user?.role || "avocat")}
                </p>
                <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight sm:text-4xl">
                  {t.welcome}, {user?.full_name?.split(" ")[0]}
                </h1>
                <p className="mt-2 text-sm text-sanad-cream/70">
                  {user?.cabinet_name} —{" "}
                  {assistantMode
                    ? "espace assistant : dossiers, pièces et préparation"
                    : "espace avocat : plaidoirie, dossiers et documents"}
                </p>
                <div className="mt-6 flex flex-wrap gap-3">
                  {assistantMode ? (
                    <Magnetic strength={30}>
                      <Link href="/documents">
                        <Button variant="gold" className="btn-3d gap-2 shadow-gold">
                          <FileText className="h-4 w-4" />
                          Gérer les pièces
                        </Button>
                      </Link>
                    </Magnetic>
                  ) : (
                    <Magnetic strength={30}>
                      <Link href="/redaction">
                        <Button variant="gold" className="btn-3d gap-2 shadow-gold">
                          <Mic className="h-4 w-4" />
                          Nouvelle plaidoirie
                        </Button>
                      </Link>
                    </Magnetic>
                  )}
                  {!assistantMode && (
                    <Magnetic strength={22}>
                      <Link href="/cases/new">
                        <Button
                          variant="outline"
                          className="gap-2 border-sanad-gold/40 bg-transparent text-sanad-ivory hover:bg-sanad-gold/10"
                        >
                          <Plus className="h-4 w-4" />
                          {t.newCase}
                        </Button>
                      </Link>
                    </Magnetic>
                  )}
                </div>
              </div>

              <motion.div
                className="flex flex-col items-center"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.15, type: "spring", stiffness: 200, damping: 18 }}
                whileHover={{ scale: 1.04, rotateY: 8 }}
              >
                <div className="rounded-2xl bg-white/95 p-3 shadow-gold">
                  <Image
                    src="/armoiries-maroc.png"
                    alt="Armoiries du Royaume du Maroc"
                    width={96}
                    height={120}
                    className="h-28 w-auto object-contain"
                    priority
                  />
                </div>
                <p className="mt-2 text-center text-[10px] text-sanad-cream/50">
                  Modèle officiel · Plaidoirie
                </p>
              </motion.div>
            </div>
          </div>
        </FadeIn>

        <StaggerContainer className="grid gap-4 sm:grid-cols-3" stagger={0.08}>
          <StaggerItem>
            <TiltCard intensity={12}>
              <div className="glass-card-light flex items-center gap-4 p-5">
                <div className="rounded-xl bg-sanad-navy/10 p-3 text-sanad-navy">
                  <Briefcase className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-sanad-navy">
                    {activeCount || cases.length || "0"}
                  </p>
                  <p className="text-sm text-slate-500">{t.activeCases}</p>
                </div>
              </div>
            </TiltCard>
          </StaggerItem>
          <StaggerItem>
            <TiltCard intensity={12}>
              <div className="glass-card-light flex items-center gap-4 p-5">
                <div className="rounded-xl bg-sanad-gold/20 p-3 text-sanad-gold">
                  <Mic className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-sanad-navy">Cœur produit</p>
                  <p className="text-sm text-slate-500">Dictée → plaidoirie</p>
                </div>
              </div>
            </TiltCard>
          </StaggerItem>
          <StaggerItem>
            <TiltCard intensity={12}>
              <div className="glass-card-light flex items-center gap-4 p-5">
                <div className="rounded-xl bg-sanad-gold/15 p-3 text-sanad-navy">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-sanad-navy">
                    {assistantMode ? "Votre rôle" : "IA métier"}
                  </p>
                  <p className="text-sm text-slate-500">
                    {assistantMode
                      ? "Préparer le dossier pour l’avocat"
                      : "Correction sans inventer"}
                  </p>
                </div>
              </div>
            </TiltCard>
          </StaggerItem>
        </StaggerContainer>

        <div>
          <FadeIn>
            <h2 className="mb-4 font-display text-lg font-semibold text-sanad-navy">
              Accès rapide
            </h2>
          </FadeIn>
          <StaggerContainer className="grid gap-4 md:grid-cols-3" stagger={0.1}>
            {actions.map((a) => (
              <StaggerItem key={a.href}>
                <CometCard className="h-full">
                  <Link href={a.href} className="block h-full">
                    <div
                      className={cn(
                        "h-full rounded-2xl border p-6 transition",
                        a.primary
                          ? "border-sanad-gold/40 bg-gradient-to-br from-sanad-navy to-sanad-dark text-white shadow-luxe"
                          : "border-sanad-border bg-white hover:border-sanad-gold/40",
                      )}
                    >
                      <motion.div
                        className={cn(
                          "mb-4 flex h-11 w-11 items-center justify-center rounded-xl",
                          a.primary ? "bg-sanad-gold/20 text-sanad-gold" : "bg-sanad-cream text-sanad-navy",
                        )}
                        whileHover={{ scale: 1.1, rotate: -4 }}
                      >
                        <a.icon className="h-5 w-5" />
                      </motion.div>
                      <h3
                        className={cn(
                          "font-semibold",
                          a.primary ? "text-sanad-ivory" : "text-sanad-navy",
                        )}
                      >
                        {a.title}
                      </h3>
                      <p
                        className={cn(
                          "mt-1 text-sm",
                          a.primary ? "text-sanad-cream/70" : "text-slate-500",
                        )}
                      >
                        {a.desc}
                      </p>
                    </div>
                  </Link>
                </CometCard>
              </StaggerItem>
            ))}
          </StaggerContainer>
        </div>

        <FadeIn delay={0.1}>
          <div className="rounded-2xl border border-sanad-border bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-display text-lg font-semibold text-sanad-navy">
                {t.recentCases}
              </h2>
              <Link href="/cases">
                <Button variant="ghost" size="sm">
                  {t.seeAll}
                </Button>
              </Link>
            </div>
            <div className="divide-y divide-sanad-border">
              {recentCases.length === 0 && (
                <p className="py-6 text-center text-sm text-slate-400">
                  Aucun dossier — créez-en un, puis rattachez votre plaidoirie.
                </p>
              )}
              {recentCases.map((c, i) => (
                <motion.div
                  key={c.id}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Link
                    href={`/cases/${c.id}`}
                    className="flex items-center justify-between py-3.5 transition hover:bg-sanad-cream/50"
                  >
                    <div>
                      <p className="font-medium text-sanad-navy">{c.reference}</p>
                      <p className="text-sm text-slate-500">{c.client_name}</p>
                    </div>
                    <span
                      className={cn(
                        "rounded-full px-2.5 py-0.5 text-xs font-medium",
                        c.status === "Urgent"
                          ? "bg-red-100 text-red-700"
                          : c.status === "Clôturé"
                            ? "bg-slate-100 text-slate-600"
                            : "bg-sanad-gold/20 text-sanad-navy",
                      )}
                    >
                      {c.status}
                    </span>
                  </Link>
                </motion.div>
              ))}
            </div>
          </div>
        </FadeIn>
      </div>
    </AppShell>
  );
}
