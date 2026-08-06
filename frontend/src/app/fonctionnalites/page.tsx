"use client";

import Link from "next/link";
import { BookOpen, FileSearch, Scale, Shield, Sparkles } from "lucide-react";
import { PublicNavbar } from "@/components/layout/public-navbar";
import { PublicFooter } from "@/components/layout/public-footer";
import { SanadLogo } from "@/components/brand/sanad-logo";
import { Button } from "@/components/ui/button";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/motion/fade-in";
import { TiltCard } from "@/components/motion/tilt-card";
import { useTranslations } from "@/store/locale";

export default function FonctionnalitesPage() {
  const tr = useTranslations();

  const features = [
    { icon: Scale, title: tr.features.f1Title, description: tr.features.f1Desc, accent: "from-sanad-gold/20 to-sanad-gold/5" },
    { icon: FileSearch, title: tr.features.f2Title, description: tr.features.f2Desc, accent: "from-sanad-gold/20 to-sanad-gold/5" },
    { icon: Sparkles, title: tr.features.f3Title, description: tr.features.f3Desc, accent: "from-sanad-gold/15 to-sanad-gold/5" },
    { icon: Shield, title: tr.features.f4Title, description: tr.features.f4Desc, accent: "from-amber-500/15 to-sanad-gold/5" },
  ];

  const aiPoints = [tr.ai.point1, tr.ai.point2, tr.ai.point3];

  return (
    <div className="min-h-screen bg-sanad-cream">
      <PublicNavbar variant="light" />
      <main className="relative overflow-hidden pb-16 pt-24">
        <div className="sanad-orb sanad-orb-1 opacity-20" />
        <div className="sanad-orb sanad-orb-2 opacity-15" />

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeIn className="mb-14 flex flex-col items-center text-center sm:flex-row sm:items-center sm:text-left">
            <SanadLogo size="xl" className="mb-4 sm:mb-0 sm:mr-6" />
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sanad-gold">LegalTech Maroc</p>
              <h1 className="mt-2 text-3xl font-bold text-sanad-navy sm:text-4xl">{tr.features.title}</h1>
              <p className="mt-3 max-w-2xl text-sanad-muted">{tr.features.subtitle}</p>
            </div>
          </FadeIn>

          <StaggerContainer className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4" stagger={0.12}>
            {features.map((f) => (
              <StaggerItem key={f.title}>
                <TiltCard intensity={8}>
                  <div className={`glass-card-light group h-full bg-gradient-to-br ${f.accent} p-6`}>
                    <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-white/80 text-sanad-gold shadow-sm transition-all duration-300 group-hover:bg-sanad-gold/15 group-hover:text-sanad-gold">
                      <f.icon className="h-5 w-5" />
                    </div>
                    <h2 className="font-semibold text-sanad-navy">{f.title}</h2>
                    <p className="mt-2 text-sm leading-relaxed text-sanad-muted">{f.description}</p>
                  </div>
                </TiltCard>
              </StaggerItem>
            ))}
          </StaggerContainer>

          <FadeIn className="mt-20 grid items-center gap-12 lg:grid-cols-2" delay={0.1}>
            <div>
              <div className="mb-3 flex items-center gap-2 text-sanad-gold">
                <BookOpen className="h-5 w-5" />
                <span className="text-sm font-semibold uppercase tracking-wide">{tr.ai.label}</span>
              </div>
              <h2 className="text-2xl font-bold text-sanad-navy sm:text-3xl">{tr.ai.title}</h2>
              <p className="mt-4 text-sanad-muted">{tr.ai.description}</p>
              <ul className="mt-6 space-y-3">
                {aiPoints.map((item, i) => (
                  <li key={item} className="flex items-start gap-3 text-sm text-sanad-muted">
                    <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-sanad-gold/15 text-xs font-bold text-sanad-gold">
                      {i + 1}
                    </span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <TiltCard intensity={6}>
              <div className="glass-card-dark p-8">
                <p className="text-xs font-medium uppercase tracking-wider text-sanad-gold/80">{tr.ai.example}</p>
                <p className="mt-5 text-sm text-sanad-cream/80">
                  <span className="font-semibold text-sanad-gold">{tr.ai.you}</span> {tr.ai.question}
                </p>
                <p className="mt-5 text-sm leading-relaxed text-sanad-cream/90">
                  <span className="font-semibold text-sanad-gold">{tr.ai.sanad}</span> {tr.ai.answer}
                </p>
              </div>
            </TiltCard>
          </FadeIn>

          <FadeIn className="mt-16 text-center" delay={0.2}>
            <Link href="/register">
              <Button size="lg" variant="gold" className="btn-3d px-10">
                {tr.cta.button}
              </Button>
            </Link>
          </FadeIn>
        </div>
      </main>
      <PublicFooter />
    </div>
  );
}
