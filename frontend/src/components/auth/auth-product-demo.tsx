"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { FileText, FolderOpen, Mic, Sparkles, Users } from "lucide-react";
import { useClientLocale } from "@/store/locale";

const STEPS = [
  {
    id: "voice",
    Icon: Mic,
    accent: "#4C7CFF",
    glow: "rgba(76,124,255,0.55)",
    labelFr: "Dictée",
    labelAr: "إملاء",
    hintFr: "La voix devient plaidoirie",
    hintAr: "الصوت يصبح مرافعة",
  },
  {
    id: "synth",
    Icon: Sparkles,
    accent: "#FF6A00",
    glow: "rgba(255,106,0,0.5)",
    labelFr: "Synthèse",
    labelAr: "تلخيص",
    hintFr: "Pièces lues et résumées",
    hintAr: "الوثائق تُقرأ وتُلخّص",
  },
  {
    id: "cases",
    Icon: FolderOpen,
    accent: "#C9A84A",
    glow: "rgba(201,168,74,0.5)",
    labelFr: "Dossiers",
    labelAr: "الملفات",
    hintFr: "Organisation par affaire",
    hintAr: "تنظيم حسب الملف",
  },
  {
    id: "team",
    Icon: Users,
    accent: "#57A88C",
    glow: "rgba(87,168,140,0.45)",
    labelFr: "Équipe",
    labelAr: "الفريق",
    hintFr: "Cabinet synchronisé",
    hintAr: "المكتب متزامن",
  },
  {
    id: "doc",
    Icon: FileText,
    accent: "#A8C0FF",
    glow: "rgba(168,192,255,0.5)",
    labelFr: "Document",
    labelAr: "وثيقة",
    hintFr: "Officiel, prêt à signer",
    hintAr: "رسمي وجاهز للتوقيع",
  },
] as const;

/** Carrousel 3D à côté login / register — Expérience LexHub */
export function AuthProductDemo() {
  const locale = useClientLocale();
  const ar = locale === "ar";
  const [ready, setReady] = useState(false);
  const [step, setStep] = useState(0);
  const n = STEPS.length;

  useEffect(() => {
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;
    const t = window.setInterval(() => {
      setStep((s) => (s + 1) % n);
    }, 2800);
    return () => window.clearInterval(t);
  }, [n, ready]);

  const current = STEPS[step];

  return (
    <aside className="auth-demo relative order-1 overflow-hidden rounded-[28px] border border-[rgba(140,170,255,0.28)] bg-[rgba(7,16,51,0.45)] p-5 text-white shadow-[0_0_48px_rgba(76,124,255,0.2),0_0_36px_rgba(255,106,0,0.12)] backdrop-blur-md sm:p-6 lg:order-2 lg:min-h-[460px] lg:p-8">
      <div
        className="pointer-events-none absolute -right-20 -top-24 h-64 w-64 rounded-full bg-[rgba(76,124,255,0.28)] blur-3xl"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -bottom-28 left-0 h-56 w-56 rounded-full bg-[rgba(255,106,0,0.18)] blur-3xl"
        aria-hidden
      />

      <div className="relative z-10 text-center">
        <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-[#FFB07A]">
          {ar ? "تجربة LexHub" : "Expérience LexHub"}
        </p>
        <h2 className="mt-2 font-serif text-2xl font-semibold tracking-tight text-white sm:text-3xl lg:text-[2.15rem] lg:leading-tight">
          {ar ? "من الصوت إلى الملف" : "De la voix au dossier"}
        </h2>
        <p className="mx-auto mt-2 max-w-[320px] text-sm text-white/65">
          {ar
            ? "إملاء، تلخيص، تنظيم الملفات والفريق — في مسار واحد."
            : "Dictée, synthèse, dossiers et équipe — un seul flux."}
        </p>
      </div>

      <div
        className="relative z-10 mx-auto mt-6 flex h-[210px] w-full max-w-[360px] items-center justify-center lg:mt-8 lg:h-[230px]"
        style={{ perspective: "1100px" }}
      >
        <motion.div
          className="pointer-events-none absolute bottom-2 left-1/2 h-8 w-[70%] -translate-x-1/2 rounded-[100%] bg-[rgba(76,124,255,0.25)] blur-2xl"
          initial={false}
          animate={ready ? { opacity: [0.35, 0.7, 0.35], scaleX: [0.9, 1.05, 0.9] } : { opacity: 0.5 }}
          transition={{ duration: 3.2, repeat: Infinity }}
          aria-hidden
        />

        <div className="relative h-full w-full" style={{ transformStyle: "preserve-3d" }}>
          {STEPS.map((s, i) => {
            const Icon = s.Icon;
            let offset = i - step;
            if (offset > Math.floor(n / 2)) offset -= n;
            if (offset < -Math.floor(n / 2)) offset += n;
            const abs = Math.abs(offset);
            const active = offset === 0;
            return (
              <motion.button
                key={s.id}
                type="button"
                onClick={() => setStep(i)}
                className="absolute left-1/2 top-1/2 w-[140px] border-0 bg-transparent p-0 outline-none"
                style={{
                  transformStyle: "preserve-3d",
                  marginLeft: -70,
                  marginTop: -78,
                }}
                initial={false}
                animate={{
                  x: offset * 72,
                  z: active ? 70 : -abs * 85,
                  rotateY: offset * -26,
                  rotateX: active ? 6 : 12,
                  scale: active ? 1.06 : Math.max(0.64, 1 - abs * 0.15),
                  opacity: abs > 2 ? 0 : active ? 1 : 0.42,
                }}
                transition={{ type: "spring", stiffness: 170, damping: 24 }}
                aria-label={ar ? s.labelAr : s.labelFr}
                tabIndex={active ? 0 : -1}
              >
                <div
                  className="relative overflow-hidden rounded-[22px] border px-3 pb-3.5 pt-4 text-center"
                  style={{
                    borderColor: active ? s.accent : "rgba(255,255,255,0.14)",
                    background: active
                      ? "linear-gradient(155deg, rgba(27,63,156,0.95), rgba(7,16,51,0.98))"
                      : "linear-gradient(155deg, rgba(18,48,122,0.75), rgba(7,16,51,0.85))",
                    boxShadow: active
                      ? `0 24px 50px rgba(7,16,51,0.55), 0 0 36px ${s.glow}, inset 0 1px 0 rgba(255,255,255,0.18)`
                      : "0 12px 28px rgba(7,16,51,0.35)",
                  }}
                >
                  {active && ready ? (
                    <motion.span
                      className="pointer-events-none absolute inset-0"
                      style={{
                        background: `radial-gradient(circle at 50% 20%, ${s.glow}, transparent 65%)`,
                      }}
                      animate={{ opacity: [0.45, 0.9, 0.45] }}
                      transition={{ duration: 2.4, repeat: Infinity }}
                      aria-hidden
                    />
                  ) : null}
                  <div
                    className="relative mx-auto mb-2.5 flex h-12 w-12 items-center justify-center rounded-2xl border"
                    style={{
                      borderColor: `${s.accent}88`,
                      background: `linear-gradient(145deg, ${s.accent}33, rgba(7,16,51,0.6))`,
                      boxShadow: active ? `0 0 24px ${s.glow}` : undefined,
                    }}
                  >
                    <Icon
                      className="h-6 w-6"
                      strokeWidth={1.7}
                      style={{ color: active ? "#fff" : s.accent }}
                    />
                  </div>
                  <p className="relative font-serif text-[16px] font-semibold text-white">
                    {ar ? s.labelAr : s.labelFr}
                  </p>
                </div>
              </motion.button>
            );
          })}
        </div>
      </div>

      <div className="relative z-10 mt-1 flex min-h-[40px] items-center justify-center px-2">
        <AnimatePresence mode="wait">
          <motion.p
            key={current.id}
            className="text-center text-sm font-medium"
            style={{ color: current.accent }}
            initial={false}
            animate={{ opacity: 1, y: 0 }}
            exit={ready ? { opacity: 0, y: -4 } : undefined}
            transition={{ duration: 0.25 }}
          >
            {ar ? current.hintAr : current.hintFr}
          </motion.p>
        </AnimatePresence>
      </div>

      <div className="relative z-10 mt-4 flex items-center justify-center gap-2">
        {STEPS.map((s, i) => (
          <button
            key={s.id}
            type="button"
            onClick={() => setStep(i)}
            className="h-2 rounded-full border-0 p-0 transition-all"
            style={{
              width: i === step ? 22 : 8,
              background: i === step ? s.accent : "rgba(255,255,255,0.22)",
              boxShadow: i === step ? `0 0 12px ${s.glow}` : undefined,
            }}
            aria-label={ar ? s.labelAr : s.labelFr}
          />
        ))}
      </div>
    </aside>
  );
}
