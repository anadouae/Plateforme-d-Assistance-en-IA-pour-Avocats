"use client";

import Link from "next/link";
import { PublicNavbar } from "@/components/layout/public-navbar";
import { PublicFooter } from "@/components/layout/public-footer";
import { LexHubLogo } from "@/components/brand/lexhub-logo";
import { Button } from "@/components/ui/button";
import { FadeIn } from "@/components/motion/fade-in";
import { useClientLocale, useTranslations } from "@/store/locale";
import { VisitorConvertNudge } from "@/components/billing/visitor-convert-nudge";

export default function AboutPage() {
  const tr = useTranslations();
  const ar = useClientLocale() === "ar";

  return (
    <div className="min-h-screen bg-sanad-cream" dir={ar ? "rtl" : "ltr"}>
      <PublicNavbar variant="light" />
      <VisitorConvertNudge />

      <section className="relative overflow-hidden bg-sanad-navy py-24 text-sanad-ivory">
        <div className="sanad-orb sanad-orb-2 opacity-30" />
        <div className="relative mx-auto max-w-4xl px-4 text-center sm:px-6">
          <FadeIn>
            <div className="mx-auto mb-8 flex justify-center">
              <LexHubLogo size="lg" withWordmark dark />
            </div>
            <h1 className="font-display text-4xl font-semibold text-white sm:text-5xl">{tr.about.title}</h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg text-white/90">{tr.about.subtitle}</p>
          </FadeIn>
        </div>
      </section>

      <section className="py-20">
        <div className="mx-auto max-w-3xl space-y-8 px-4 sm:px-6">
          {tr.about.paragraphs.map((p) => (
            <FadeIn key={p}>
              <p className="text-lg leading-relaxed text-sanad-navy/85">{p}</p>
            </FadeIn>
          ))}
          <FadeIn>
            <div className="grid gap-4 sm:grid-cols-3">
              {tr.about.values.map((v) => (
                <div
                  key={v.title}
                  className="glass-card-light rounded-2xl border border-sanad-gold/20 p-5 text-center"
                >
                  <p className="font-serif font-semibold text-sanad-navy">{v.title}</p>
                  <p className="mt-2 text-sm text-sanad-muted">{v.desc}</p>
                </div>
              ))}
            </div>
          </FadeIn>
          <FadeIn className="pt-8 text-center">
            <Link href="/login?tab=register">
              <Button size="lg" variant="gold" className="btn-3d">
                {tr.cta.button}
              </Button>
            </Link>
          </FadeIn>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
