"use client";

import Link from "next/link";
import { PublicNavbar } from "@/components/layout/public-navbar";
import { PublicFooter } from "@/components/layout/public-footer";
import { FadeIn } from "@/components/motion/fade-in";
import { SanadLogo } from "@/components/brand/sanad-logo";

interface LegalPageLayoutProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}

export function LegalPageLayout({ title, subtitle, children }: LegalPageLayoutProps) {
  return (
    <div className="min-h-screen bg-sanad-cream">
      <PublicNavbar variant="light" />
      <main className="relative overflow-hidden pb-16 pt-24">
        <div className="sanad-orb sanad-orb-1 opacity-20" />
        <div className="sanad-orb sanad-orb-2 opacity-15" />

        <div className="relative mx-auto max-w-3xl px-4 sm:px-6">
          <FadeIn>
            <div className="mb-10 flex items-center gap-4">
              <SanadLogo size="lg" />
              <div>
                <h1 className="text-3xl font-bold text-sanad-navy">{title}</h1>
                {subtitle && <p className="mt-1 text-sanad-muted">{subtitle}</p>}
              </div>
            </div>
          </FadeIn>

          <FadeIn delay={0.1}>
            <article className="glass-card-light space-y-6 p-8 text-sanad-navy leading-relaxed">
              {children}
            </article>
          </FadeIn>

          <FadeIn delay={0.2} className="mt-8 text-center">
            <Link href="/" className="text-sm text-sanad-gold hover:text-sanad-gold hover:underline">
              ← Retour à l&apos;accueil
            </Link>
          </FadeIn>
        </div>
      </main>
      <PublicFooter />
    </div>
  );
}
