"use client";

import Link from "next/link";
import { Gift, Link2, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

/** Section landing — parrainage cabinet → cabinet. */
export function LandingReferralSection({ ar }: { ar: boolean }) {
  const steps = ar
    ? [
        {
          icon: Link2,
          title: "شاركوا رمزكم",
          desc: "من الإعدادات ← الخطة والاستخدام، انسخوا الرابط أو الرمز.",
        },
        {
          icon: Gift,
          title: "المكتب المدعو يكسب",
          desc: "+14 يوماً من التجربة عند بدء Solo أو Cabinet برمزكم.",
        },
        {
          icon: Sparkles,
          title: "أنتم تكسبون",
          desc: "+1 شهر عند بدء اشتراكه المدفوع بعد التجربة (بدون إلغاء).",
        },
      ]
    : [
        {
          icon: Link2,
          title: "Partagez votre code",
          desc: "Dans Paramètres → Plan & usage, copiez le lien ou le code.",
        },
        {
          icon: Gift,
          title: "Le filleul gagne",
          desc: "+14 jours d’essai quand il démarre Solo ou Cabinet avec votre code.",
        },
        {
          icon: Sparkles,
          title: "Vous gagnez",
          desc: "+1 mois offert quand son abonnement payant commence après l’essai.",
        },
      ];

  return (
    <section
      id="parrainage"
      className="relative overflow-hidden bg-[#0B1A4D] px-6 py-[96px] sm:px-8"
      dir={ar ? "rtl" : "ltr"}
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          background:
            "radial-gradient(ellipse 70% 60% at 20% 20%, rgba(90,139,255,0.35), transparent), radial-gradient(ellipse 50% 40% at 90% 80%, rgba(255,138,45,0.18), transparent)",
        }}
        aria-hidden
      />
      <div className="relative z-10 mx-auto max-w-[1080px]">
        <div className="mx-auto mb-12 max-w-[640px] text-center">
          <p className="font-mono text-[11.5px] uppercase tracking-[0.14em] text-[#A8C0FF]">
            {ar ? "برنامج الإحالة" : "Parrainage cabinets"}
          </p>
          <h2 className="font-display mt-3.5 text-[clamp(28px,4vw,40px)] font-semibold tracking-tight text-white">
            {ar
              ? "ادعوا مكتباً زميلاً — كلاكما يربح"
              : "Invitez un cabinet confrère — vous gagnez tous les deux"}
          </h2>
          <p className="mx-auto mt-4 max-w-[520px] text-[15px] leading-relaxed text-white/75">
            {ar
              ? "إحالة مكتب إلى مكتب فقط. بلا إحالة ذاتية. حد سنوي معقول للحماية من الإساءة."
              : "Uniquement cabinet → cabinet. Pas d’auto-parrainage. Plafond annuel pour limiter les abus."}
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {steps.map((s, i) => (
            <motion.div
              key={s.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.45, delay: i * 0.08 }}
              className="rounded-2xl border border-white/10 bg-white/[0.06] px-5 py-6 backdrop-blur-sm"
            >
              <s.icon className="h-6 w-6 text-[#FF8A2D]" aria-hidden />
              <h3 className="font-display mt-4 text-lg font-semibold text-white">{s.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-white/70">{s.desc}</p>
            </motion.div>
          ))}
        </div>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/login?tab=register"
            className="inline-flex h-11 items-center justify-center rounded-xl bg-[#FF8A2D] px-6 text-sm font-semibold text-white transition hover:bg-[#ff9a4a]"
          >
            {ar ? "إنشاء مكتب" : "Créer mon cabinet"}
          </Link>
          <Link
            href="/login"
            className="inline-flex h-11 items-center justify-center rounded-xl border border-white/25 bg-transparent px-6 text-sm font-semibold text-white transition hover:bg-white/10"
          >
            {ar ? "لدي حساب — رؤية رمزي" : "J’ai un compte — voir mon code"}
          </Link>
        </div>
      </div>
    </section>
  );
}
