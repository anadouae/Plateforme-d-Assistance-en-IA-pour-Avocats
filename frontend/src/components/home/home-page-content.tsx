"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { motion, useMotionValue, useSpring } from "framer-motion";
import { FolderClock, Lock, ShieldCheck } from "lucide-react";
import { PublicNavbar } from "@/components/layout/public-navbar";
import { PublicFooter } from "@/components/layout/public-footer";
import { LandingParticles } from "@/components/home/landing-particles";
import { HeroSerpentBackdrop, useHeroRevealDelay } from "@/components/home/hero-serpent-b";
import { LandingTrustBand } from "@/components/home/landing-trust-band";
import { LandingComplianceStrip } from "@/components/home/landing-compliance-strip";
import { LandingPainSection } from "@/components/home/landing-pain-section";
import { LandingFaqAccordion } from "@/components/home/landing-faq";
import { LandingFeatureIcon } from "@/components/home/landing-feature-icon";
import { LandingPricingCarousel } from "@/components/home/landing-pricing-carousel";
import { LandingReferralSection } from "@/components/home/landing-referral-section";
import { HERO_VIDEOS, VideoCarousel } from "@/components/home/video-carousel";
import { VisitorConvertNudge } from "@/components/billing/visitor-convert-nudge";
import { LANDING_FAQ_AR, LANDING_FAQ_FR } from "@/lib/landing-faq";
import { useClientLocale, useTranslations } from "@/store/locale";
import { cn } from "@/lib/utils";
import "./landing-royal-test.css";

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
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  const { ref, visible } = useReveal<HTMLDivElement>();
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 28 }}
      animate={visible ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.65, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
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
  const ar = useClientLocale() === "ar";
  const hero = t.hero;
  const features = t.features;
  const heroDelay = useHeroRevealDelay();

  const featureCards = [
    {
      n: "01 — Plaidoirie",
      title: features.f1Title,
      desc: features.f1Desc,
      dark: true,
      iconKind: "mic" as const,
    },
    {
      n: "02 — Dossiers",
      title: features.f2Title,
      desc: features.f2Desc,
      dark: false,
      iconKind: "file" as const,
    },
    {
      n: "03 — Synthèse",
      title: features.f3Title,
      desc: features.f3Desc,
      dark: false,
      iconKind: "synth" as const,
    },
    {
      n: "04 — Équipe",
      title: features.f4Title,
      desc: features.f4Desc,
      dark: true,
      iconKind: "team" as const,
    },
  ];

  return (
    <div className="landing-royal-test relative min-h-screen bg-[var(--lr-paper)] text-[var(--lr-ink)]">
      <div
        className="pointer-events-none fixed inset-0 z-[60] opacity-[0.03] mix-blend-overlay"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
        }}
        aria-hidden
      />

      <PublicNavbar variant="dark" />
      <VisitorConvertNudge />

      <section
        className="relative overflow-hidden px-6 pb-16 pt-28 sm:px-8 sm:pt-32"
        style={{
          background:
            "radial-gradient(ellipse 1000px 560px at 50% -8%, rgba(76,124,255,0.22), transparent 55%), linear-gradient(165deg, #0B1A4D 0%, #071033 55%, #0A1228 100%)",
        }}
      >
        <div className="lr-aura lr-aura--a opacity-70" aria-hidden />
        <div className="lr-aura lr-aura--b opacity-50" aria-hidden />
        <div className="lr-aura lr-aura--c opacity-40" aria-hidden />
        <div className="lr-hero-shine opacity-60" aria-hidden />
        <HeroSerpentBackdrop />
        <div
          className="pointer-events-none absolute inset-0 opacity-30"
          style={{
            backgroundImage:
              "linear-gradient(rgba(140,170,255,0.16) 1px, transparent 1px)",
            backgroundSize: "100% 96px",
          }}
          aria-hidden
        />
        <LandingParticles />

        <div className="relative z-10 mx-auto grid max-w-[1180px] items-center gap-10 lg:grid-cols-2 lg:gap-12">
          <div className={cn("text-center", ar ? "lg:text-right" : "lg:text-start")}>
            <motion.h1
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: heroDelay, duration: 0.75 }}
              className="lr-title-gold font-display text-[clamp(48px,8vw,92px)] font-semibold leading-[0.95] tracking-tight"
            >
              {hero.title}
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: heroDelay + 0.12, duration: 0.7 }}
              className="font-display mt-2 text-[21px] font-normal italic text-[#FF6A00]"
            >
              {hero.subtitle}
            </motion.p>

            <motion.p
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: heroDelay + 0.22, duration: 0.7 }}
              className={cn(
                "mt-5 max-w-[520px] text-[16.5px] leading-relaxed text-[#A8B6D4]",
                ar ? "mr-0 lg:mr-auto" : "mx-auto lg:mx-0",
              )}
            >
              {hero.description}
            </motion.p>

            <motion.p
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: heroDelay + 0.32, duration: 0.65 }}
              className={cn(
                "mt-8 max-w-[480px] text-[13.5px] leading-relaxed text-[#8FA0C0]",
                ar ? "mr-0 lg:mr-auto text-right" : "mx-auto lg:mx-0 text-left",
              )}
            >
              {ar
                ? "إملاء عربي · ملف · مرافعة — LexHub يصوغ دون اختراع."
                : "Dictée arabe · dossier · plaidoirie — LexHub structure, sans inventer."}
            </motion.p>
          </div>

          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: heroDelay + 0.15, duration: 0.9 }}
            className="relative min-h-[280px] overflow-hidden rounded-[4px] border border-white/10 shadow-[0_40px_80px_rgba(0,0,0,0.35)] sm:min-h-[360px] lg:min-h-[480px]"
          >
            <VideoCarousel sources={HERO_VIDEOS} className="absolute inset-0 h-full w-full" />
            <motion.span
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: heroDelay + 0.4, duration: 0.6 }}
              className="lr-badge-maroc absolute left-4 top-4 z-[2] inline-flex items-center gap-2 rounded-full border border-white/15 bg-black/35 px-3.5 py-1.5 font-mono text-[11px] uppercase tracking-[0.14em] text-white backdrop-blur-sm"
            >
              <span className="lr-badge-maroc__dot h-1.5 w-1.5 rounded-full" />
              {hero.badge}
            </motion.span>
          </motion.div>
        </div>

        {/* Gestes sous le fold — hors premier viewport */}
        <div className="relative z-10 mx-auto mt-24 max-w-[1180px] pt-8 sm:mt-32">
        <motion.div
          initial={{ opacity: 0, y: 32 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.35 }}
          transition={{ duration: 0.75 }}
          className="grid gap-[22px] perspective-[1200px] sm:grid-cols-2"
        >
          <TiltCard className="rounded-[18px] border border-[rgba(140,170,255,0.22)] bg-gradient-to-br from-[#12307A] to-[#0B1A4D] p-8 text-start shadow-none transition hover:border-[rgba(76,124,255,0.45)] hover:shadow-[0_30px_60px_rgba(7,16,51,0.45)]">
            <p className="font-mono text-[11.5px] uppercase tracking-[0.14em] text-[#A8C0FF]">
              {hero.gesture1Label}
            </p>
            <h3 className="font-display mt-3 text-[23px] font-semibold text-[#F4F6FC]">
              {hero.gesture1Title}
            </h3>
            <p className="mt-2.5 text-[14.5px] leading-relaxed text-[#A8B6D4]">
              {hero.gesture1Desc}
            </p>
            <div className="mt-5 flex h-[46px] w-[46px] items-center justify-center rounded-[10px] border border-[rgba(140,170,255,0.28)] bg-[rgba(76,124,255,0.12)]">
              <LandingFeatureIcon kind="mic" dark />
            </div>
          </TiltCard>

          <TiltCard className="rounded-[18px] border border-[rgba(140,170,255,0.22)] bg-gradient-to-br from-[#12307A] to-[#0B1A4D] p-8 text-start transition hover:border-[rgba(76,124,255,0.45)] hover:shadow-[0_30px_60px_rgba(7,16,51,0.45)]">
            <p className="font-mono text-[11.5px] uppercase tracking-[0.14em] text-[#A8C0FF]">
              {hero.gesture2Label}
            </p>
            <h3 className="font-display mt-3 text-[23px] font-semibold text-[#F4F6FC]">
              {hero.gesture2Title}
            </h3>
            <p className="mt-2.5 text-[14.5px] leading-relaxed text-[#A8B6D4]">
              {hero.gesture2Desc}
            </p>
            <div className="mt-5 flex h-[46px] w-[46px] items-center justify-center rounded-[10px] border border-[rgba(140,170,255,0.28)] bg-[rgba(76,124,255,0.12)]">
              <LandingFeatureIcon kind="synth" dark />
            </div>
          </TiltCard>
        </motion.div>
        </div>
      </section>

      <LandingComplianceStrip ar={ar} />
      <LandingTrustBand ar={ar} />

      <LandingPainSection ar={ar} />

      <section id="fonctionnalites" className="bg-[var(--lr-paper)] px-6 py-[108px] sm:px-8">
        <Reveal className="mx-auto mb-14 max-w-[620px] text-center">
          <p className="font-mono text-[11.5px] uppercase tracking-[0.14em] text-[#1B3F9C]">
            {hero.featuresEyebrow}
          </p>
          <h2 className="font-display mt-3.5 text-[clamp(30px,4vw,42px)] font-semibold tracking-tight text-[var(--lr-ink)]">
            {features.title}
          </h2>
        </Reveal>

        <div className="mx-auto grid max-w-[1080px] gap-5 md:grid-cols-2">
          {featureCards.map((f, idx) => (
            <Reveal key={f.n} delay={idx * 0.1}>
              <TiltCard
                strength={4}
                className="lr-feature-card overflow-hidden rounded-2xl border border-[var(--lr-line-light)] bg-[var(--lr-card)] transition hover:border-[rgba(27,63,156,0.35)] hover:shadow-[0_24px_48px_rgba(11,26,77,0.12)]"
              >
                <div
                  className={cn(
                    "flex h-[168px] items-center justify-center",
                    f.dark
                      ? "bg-gradient-to-br from-[#1B3F9C] to-[#0B1A4D]"
                      : "bg-[var(--lr-paper-dim)]",
                  )}
                >
                  <LandingFeatureIcon kind={f.iconKind} dark={f.dark} />
                </div>
                <div className="px-[26px] pb-7 pt-6">
                  <p className="font-mono text-[11.5px] uppercase tracking-[0.14em] text-[var(--lr-ink-soft)]">
                    {f.n}
                  </p>
                  <h3 className="font-display mt-2.5 text-[19px] font-semibold text-[var(--lr-ink)]">
                    {f.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-[var(--lr-ink-soft)]">{f.desc}</p>
                </div>
              </TiltCard>
            </Reveal>
          ))}
        </div>
      </section>

      <LandingPricingCarousel />

      <LandingReferralSection ar={ar} />

      <LandingFaqAccordion
        ar={ar}
        eyebrow={ar ? "أسئلة المحامي" : "Questions d’avocat"}
        title={ar ? "أسئلة شائعة" : "Questions fréquentes"}
        items={[...(ar ? LANDING_FAQ_AR : LANDING_FAQ_FR)]}
      />

      <section
        id="confidentialite"
        className="relative overflow-hidden bg-[var(--lr-royal-950)] px-6 py-[96px] text-center sm:px-8"
      >
        <div className="lr-aura lr-aura--a opacity-60" aria-hidden />
        <Reveal className="relative z-10 mx-auto max-w-[720px]">
          <p className="font-mono text-[11.5px] uppercase tracking-[0.18em] text-[#A8C0FF]">
            {hero.privacyEyebrow}
          </p>
          <h2 className="font-display mt-4 text-[clamp(28px,4vw,40px)] font-semibold tracking-tight text-[var(--lr-ivory)]">
            {hero.privacyTitle}
          </h2>
          <p className="mx-auto mt-4 max-w-[560px] text-[15.5px] leading-relaxed text-[var(--lr-muted-on-dark)]">
            {hero.privacyDesc}
          </p>
        </Reveal>

        <div className="relative z-10 mx-auto mt-14 grid max-w-[1080px] gap-5 text-start md:grid-cols-3">
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
          ].map((card, idx) => {
            const Icon = card.icon;
            return (
              <Reveal key={card.title} delay={idx * 0.12}>
                <motion.article
                  whileHover={{ y: -4 }}
                  className="h-full rounded-2xl border border-[var(--lr-line-dark)] bg-[#0F2258] px-6 py-7 transition hover:border-[rgba(76,124,255,0.4)] hover:shadow-[0_0_40px_rgba(76,124,255,0.12)]"
                >
                  <div className="lr-security-icon flex h-12 w-12 items-center justify-center rounded-full border border-[#4C7CFF]/45 text-[#4C7CFF]">
                    <Icon className="h-5 w-5" strokeWidth={1.6} />
                  </div>
                  <h3 className="mt-5 text-[17px] font-semibold text-white">{card.title}</h3>
                  <p className="mt-2.5 text-sm leading-relaxed text-[var(--lr-muted-on-dark)]">{card.desc}</p>
                </motion.article>
              </Reveal>
            );
          })}
        </div>
      </section>

      <section className="relative bg-[var(--lr-paper)] px-6 py-[100px] text-center sm:px-8">
        <div className="absolute left-1/2 top-0 h-14 w-px -translate-x-1/2 bg-[var(--lr-line-light)]" />
        <Reveal>
          <h2 className="font-display text-[clamp(28px,3.6vw,38px)] font-semibold text-[var(--lr-ink)]">
            {t.cta.title}
          </h2>
          <p className="mx-auto mt-3.5 max-w-[460px] text-[15.5px] text-[var(--lr-ink-soft)]">
            {t.cta.subtitle}
          </p>
          <Link
            href="/login?tab=register"
            className="lr-cta-pulse mt-8 inline-flex items-center gap-2.5 rounded-full border border-[var(--lr-royal-900)] bg-[var(--lr-royal-900)] px-[30px] py-[15px] text-[15px] font-semibold text-[var(--lr-ivory)] shadow-[0_0_28px_rgba(76,124,255,0.25)] transition hover:-translate-y-0.5 hover:bg-[var(--lr-royal-800)] hover:shadow-[0_16px_36px_rgba(11,26,77,0.28)]"
          >
            {hero.ctaRegister}
            <motion.span aria-hidden animate={{ x: [0, 4, 0] }} transition={{ repeat: Infinity, duration: 1.6 }}>
              →
            </motion.span>
          </Link>
        </Reveal>
      </section>

      <PublicFooter />
    </div>
  );
}
