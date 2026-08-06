"use client";

import Link from "next/link";
import { Lock, Server, Shield, UserCheck } from "lucide-react";
import { PublicNavbar } from "@/components/layout/public-navbar";
import { PublicFooter } from "@/components/layout/public-footer";
import { SanadLogo } from "@/components/brand/sanad-logo";
import { Button } from "@/components/ui/button";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/motion/fade-in";
import { useTranslations } from "@/store/locale";

const securityIcons = [Lock, Shield, Server, UserCheck];

export default function SecuritePage() {
  const tr = useTranslations();

  return (
    <div className="min-h-screen bg-sanad-navy text-white">
      <PublicNavbar variant="dark" />
      <main className="relative overflow-hidden pb-16 pt-24">
        <div className="sanad-orb sanad-orb-1 opacity-40" />
        <div className="sanad-orb sanad-orb-2 opacity-30" />
        <div className="hero-grid-overlay absolute inset-0 opacity-10" />

        <div className="relative mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <FadeIn className="flex flex-col items-center text-center">
            <SanadLogo size="xl" className="mb-6" />
            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-sanad-gold/15 backdrop-blur">
              <Shield className="h-8 w-8 text-sanad-gold" />
            </div>
            <h1 className="font-serif text-3xl font-semibold sm:text-4xl">{tr.security.title}</h1>
            <p className="mt-4 max-w-2xl font-serif text-sanad-cream/70">{tr.security.subtitle}</p>
          </FadeIn>

          <StaggerContainer className="mt-14 grid gap-4 sm:grid-cols-2" stagger={0.08}>
            {tr.security.items.map((item, i) => {
              const Icon = securityIcons[i % securityIcons.length];
              return (
                <StaggerItem key={item}>
                  <div className="glass-card-dark flex items-start gap-4 px-6 py-5">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sanad-gold/15">
                      <Icon className="h-5 w-5 text-sanad-gold" />
                    </div>
                    <p className="text-sm font-medium leading-relaxed">{item}</p>
                  </div>
                </StaggerItem>
              );
            })}
          </StaggerContainer>

          <FadeIn className="mt-16" delay={0.15}>
            <div className="glass-card-dark space-y-4 p-8 text-sm leading-relaxed text-sanad-cream/80">
              <h2 className="font-serif text-lg font-semibold text-white">Engagements WebVoice</h2>
              <p className="font-serif">
                Sanad est conçu pour les cabinets d&apos;avocats marocains. Vos dossiers restent
                dans votre espace. Chaque action sensible est tracée — digne de la confiance du
                barreau.
              </p>
              <p>
                Pour toute question relative à la sécurité :{" "}
                <a href="mailto:contact@webvoice.ma" className="text-sanad-gold hover:underline">
                  contact@webvoice.ma
                </a>
              </p>
            </div>
          </FadeIn>

          <FadeIn className="mt-12 text-center" delay={0.2}>
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
