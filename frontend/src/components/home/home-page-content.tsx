"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { motion, useMotionValue, useSpring } from "framer-motion";
import {
  Activity,
  FileText,
  FolderClock,
  Lock,
  Mic,
  ShieldCheck,
  Users,
} from "lucide-react";
import { PublicNavbar } from "@/components/layout/public-navbar";
import { PublicFooter } from "@/components/layout/public-footer";
import { LandingWaveform } from "@/components/home/landing-waveform";
import { LandingParticles } from "@/components/home/landing-particles";
import { useTranslations } from "@/store/locale";
import { cn } from "@/lib/utils";

function useReveal<T extends HTMLElement>() {
  const ref = useRef<T | null>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([e]) => {
        if (e?.isIntersecting) setVisible(true);
      },
      { threshold: 0.15 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return { ref, visible };
}

function Reveal({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const { ref, visible } = useReveal<HTMLDivElement>();
  return (
    <div
      ref={ref}
      className={cn(
        "transition-all duration-700 ease-out",
        visible ? "translate-y-0 opacity-100" : "translate-y-7 opacity-0",
        className,
      )}
    >
      {children}
    </div>
  );
}

function TiltCard({
  children,
  className,
  strength = 6,
}: {
  children: React.ReactNode;
  className?: string;
  strength?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const rx = useMotionValue(0);
  const ry = useMotionValue(0);
  const rotateX = useSpring(rx, { stiffness: 260, damping: 22 });
  const rotateY = useSpring(ry, { stiffness: 260, damping: 22 });

  return (
    <motion.div
      ref={ref}
      style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
      onMouseMove={(e) => {
        const el = ref.current;
        if (!el) return;
        const rect = el.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        rx.set(((y - rect.height / 2) / rect.height) * -strength);
        ry.set(((x - rect.width / 2) / rect.width) * strength);
      }}
      onMouseLeave={() => {
        rx.set(0);
        ry.set(0);
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export function HomePageContent() {
  const t = useTranslations();
  const hero = t.hero;
  const features = t.features;
  const heroRef = useRef<HTMLElement>(null);
  const glowX = useMotionValue(0);
  const glowY = useMotionValue(0);
  const [glowOn, setGlowOn] = useState(false);

  const featureCards = [
    {
      n: "01 — Voix",
      title: features.f1Title,
      desc: features.f1Desc,
      dark: true,
      icon: Mic,
    },
    {
      n: "02 — Dossiers",
      title: features.f2Title,
      desc: features.f2Desc,
      dark: false,
      icon: FileText,
    },
    {
      n: "03 — Synthèse",
      title: features.f3Title,
      desc: features.f3Desc,
      dark: false,
      icon: Activity,
    },
    {
      n: "04 — Équipe",
      title: features.f4Title,
      desc: features.f4Desc,
      dark: true,
      icon: Users,
    },
  ];

  return (
    <div className="relative min-h-screen bg-[#F7F2E7] text-[#1A1A17]">
      {/* grain subtil */}
      <div
        className="pointer-events-none fixed inset-0 z-[60] opacity-[0.035] mix-blend-overlay"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
        }}
        aria-hidden
      />

      <PublicNavbar variant="dark" />

      {/* HERO v3 */}
      <section
        ref={heroRef}
        className="relative overflow-hidden px-6 pb-16 pt-28 sm:px-8 sm:pt-32"
        style={{
          background:
            "radial-gradient(ellipse 900px 500px at 50% -10%, rgba(184,145,47,0.10), transparent), #0A1220",
        }}
        onMouseMove={(e) => {
          const el = heroRef.current;
          if (!el) return;
          const rect = el.getBoundingClientRect();
          glowX.set(e.clientX - rect.left);
          glowY.set(e.clientY - rect.top);
          setGlowOn(true);
        }}
        onMouseLeave={() => setGlowOn(false)}
      >
        <div
          className="pointer-events-none absolute inset-0 opacity-35"
          style={{
            backgroundImage:
              "linear-gradient(rgba(217,186,106,0.18) 1px, transparent 1px)",
            backgroundSize: "100% 96px",
          }}
          aria-hidden
        />
        <LandingParticles />
        <motion.div
          className="pointer-events-none absolute z-0 h-[560px] w-[560px] -translate-x-1/2 -translate-y-1/2 rounded-full"
          style={{
            left: glowX,
            top: glowY,
            opacity: glowOn ? 1 : 0,
            background:
              "radial-gradient(circle, rgba(217,186,106,0.10), transparent 70%)",
          }}
        />

        <div className="relative z-10 mx-auto max-w-[860px] text-center">
          <motion.span
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 rounded-full border border-[rgba(217,186,106,0.18)] bg-white/[0.03] px-4 py-2 font-mono text-[11.5px] uppercase tracking-[0.14em] text-[#D9BA6A]"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-[#D9BA6A]" />
            {hero.badge}
          </motion.span>

          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="font-display mt-7 text-[clamp(64px,11vw,128px)] font-semibold leading-[0.95] tracking-tight text-[#F7F2E7]"
          >
            {hero.title}
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="font-display mt-2 text-[21px] font-normal italic text-[#D9BA6A]"
          >
            {hero.subtitle}
          </motion.p>

          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mx-auto mt-5 max-w-[560px] text-[16.5px] leading-relaxed text-[#A7B1C2]"
          >
            {hero.description}
          </motion.p>

          <LandingWaveform />

          <div className="mx-auto mt-14 grid max-w-[980px] gap-[22px] perspective-[1200px] sm:grid-cols-2">
            <TiltCard className="rounded-[18px] border border-[rgba(217,186,106,0.18)] bg-gradient-to-br from-[#142640] to-[#0E1A2E] p-8 text-start shadow-none transition hover:border-[rgba(184,145,47,0.35)] hover:shadow-[0_30px_60px_rgba(0,0,0,0.35)]">
              <p className="font-mono text-[11.5px] uppercase tracking-[0.14em] text-[#D9BA6A]">
                {hero.gesture1Label}
              </p>
              <h3 className="font-display mt-3 text-[23px] font-semibold text-[#F4EEDD]">
                {hero.gesture1Title}
              </h3>
              <p className="mt-2.5 text-[14.5px] leading-relaxed text-[#9AA4B2]">
                {hero.gesture1Desc}
              </p>
              <div className="mt-5 flex h-[46px] w-[46px] items-center justify-center rounded-[10px] border border-[rgba(217,186,106,0.18)] bg-[rgba(217,186,106,0.08)] text-[#D9BA6A]">
                <Mic className="h-5 w-5" />
              </div>
            </TiltCard>

            <TiltCard className="rounded-[18px] border border-[rgba(217,186,106,0.18)] bg-gradient-to-br from-[#142640] to-[#0E1A2E] p-8 text-start transition hover:border-[rgba(184,145,47,0.35)] hover:shadow-[0_30px_60px_rgba(0,0,0,0.35)]">
              <p className="font-mono text-[11.5px] uppercase tracking-[0.14em] text-[#D9BA6A]">
                {hero.gesture2Label}
              </p>
              <h3 className="font-display mt-3 text-[23px] font-semibold text-[#F4EEDD]">
                {hero.gesture2Title}
              </h3>
              <p className="mt-2.5 text-[14.5px] leading-relaxed text-[#9AA4B2]">
                {hero.gesture2Desc}
              </p>
              <div className="mt-5 flex h-[46px] w-[46px] items-center justify-center rounded-[10px] border border-[rgba(217,186,106,0.18)] bg-[rgba(217,186,106,0.08)] text-[#D9BA6A]">
                <FileText className="h-5 w-5" />
              </div>
            </TiltCard>
          </div>
        </div>
      </section>

      {/* FEATURES v3 — 2×2 */}
      <section id="fonctionnalites" className="bg-[#F7F2E7] px-6 py-[108px] sm:px-8">
        <Reveal className="mx-auto mb-14 max-w-[620px] text-center">
          <p className="font-mono text-[11.5px] uppercase tracking-[0.14em] text-[#B8912F]">
            {hero.featuresEyebrow}
          </p>
          <h2 className="font-display mt-3.5 text-[clamp(30px,4vw,42px)] font-semibold tracking-tight text-[#1A1A17]">
            {features.title}
          </h2>
        </Reveal>

        <div className="mx-auto grid max-w-[1080px] gap-5 md:grid-cols-2">
          {featureCards.map((f) => {
            const Icon = f.icon;
            return (
              <TiltCard
                key={f.n}
                strength={4}
                className="overflow-hidden rounded-2xl border border-[rgba(26,26,23,0.10)] bg-[#FFFFFC] transition hover:border-[rgba(184,145,47,0.35)] hover:shadow-[0_24px_48px_rgba(20,30,50,0.09)]"
              >
                <div
                  className={cn(
                    "flex h-[168px] items-center justify-center",
                    f.dark
                      ? "bg-gradient-to-br from-[#1D3357] to-[#0E1A2E]"
                      : "bg-[#EFE7D6]",
                  )}
                >
                  <Icon
                    className={cn(
                      "h-[52px] w-[52px]",
                      f.dark ? "text-[#D9BA6A]" : "text-[#142640] opacity-55",
                    )}
                    strokeWidth={1.4}
                  />
                </div>
                <div className="px-[26px] pb-7 pt-6">
                  <p className="font-mono text-[11.5px] uppercase tracking-[0.14em] text-[#5E6470]">
                    {f.n}
                  </p>
                  <h3 className="font-display mt-2.5 text-[19px] font-semibold text-[#1A1A17]">
                    {f.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-[#5E6470]">{f.desc}</p>
                </div>
              </TiltCard>
            );
          })}
        </div>
      </section>

      {/* Confidentialité — remplace le bandeau citation / stats */}
      <section
        id="confidentialite"
        className="bg-[#0A1220] px-6 py-[96px] text-center sm:px-8"
      >
        <Reveal className="mx-auto max-w-[720px]">
          <p className="font-mono text-[11.5px] uppercase tracking-[0.18em] text-[#D9BA6A]">
            {hero.privacyEyebrow}
          </p>
          <h2 className="font-display mt-4 text-[clamp(28px,4vw,40px)] font-semibold tracking-tight text-[#F7F2E7]">
            {hero.privacyTitle}
          </h2>
          <p className="mx-auto mt-4 max-w-[560px] text-[15.5px] leading-relaxed text-[#94A3B8]">
            {hero.privacyDesc}
          </p>
        </Reveal>

        <div className="mx-auto mt-14 grid max-w-[1080px] gap-5 text-start md:grid-cols-3">
          {[
            {
              icon: ShieldCheck,
              title: hero.privacyCard1Title,
              desc: hero.privacyCard1Desc,
            },
            {
              icon: Lock,
              title: hero.privacyCard2Title,
              desc: hero.privacyCard2Desc,
            },
            {
              icon: FolderClock,
              title: hero.privacyCard3Title,
              desc: hero.privacyCard3Desc,
            },
          ].map((card) => {
            const Icon = card.icon;
            return (
              <Reveal key={card.title}>
                <article className="h-full rounded-2xl border border-[rgba(148,163,184,0.14)] bg-[#111D35] px-6 py-7 transition hover:border-[rgba(217,186,106,0.28)]">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full border border-[#D9BA6A]/50 text-[#D9BA6A]">
                    <Icon className="h-5 w-5" strokeWidth={1.6} />
                  </div>
                  <h3 className="mt-5 text-[17px] font-semibold text-white">{card.title}</h3>
                  <p className="mt-2.5 text-sm leading-relaxed text-[#94A3B8]">{card.desc}</p>
                </article>
              </Reveal>
            );
          })}
        </div>
      </section>

      {/* CTA */}
      <section className="relative bg-[#F7F2E7] px-6 py-[100px] text-center sm:px-8">
        <div className="absolute left-1/2 top-0 h-14 w-px -translate-x-1/2 bg-[rgba(26,26,23,0.10)]" />
        <Reveal>
          <h2 className="font-display text-[clamp(28px,3.6vw,38px)] font-semibold text-[#1A1A17]">
            {t.cta.title}
          </h2>
          <p className="mx-auto mt-3.5 max-w-[460px] text-[15.5px] text-[#5E6470]">
            {t.cta.subtitle}
          </p>
          <Link
            href="/register"
            className="mt-8 inline-flex items-center gap-2.5 rounded-full border border-[#0A1220] bg-[#0A1220] px-[30px] py-[15px] text-[15px] font-semibold text-[#F4EEDD] transition hover:-translate-y-0.5 hover:bg-[#142640] hover:shadow-[0_16px_32px_rgba(20,30,50,0.18)]"
          >
            {hero.ctaRegister}
            <span aria-hidden>→</span>
          </Link>
        </Reveal>
      </section>

      <PublicFooter />
    </div>
  );
}
