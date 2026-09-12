"use client";

import { motion } from "framer-motion";
import { CheckCircle2, Clock3, KeyRound, Sparkles } from "lucide-react";
import { useClientLocale } from "@/store/locale";

const STEPS_FR = [
  {
    title: "Invitation par email",
    body: "L’administrateur du cabinet vous envoie un lien personnel.",
    icon: KeyRound,
  },
  {
    title: "Activer votre compte",
    body: "Ouvrez le lien, choisissez votre mot de passe — c’est tout.",
    icon: Sparkles,
  },
  {
    title: "Accéder à LexHub",
    body: "Connectez-vous immédiatement selon le rôle attribué (avocat, assistant, admin).",
    icon: CheckCircle2,
  },
];

const STEPS_AR = [
  {
    title: "دعوة بالبريد",
    body: "يرسل مسؤول المكتب رابطاً شخصياً.",
    icon: KeyRound,
  },
  {
    title: "تفعيل الحساب",
    body: "افتحوا الرابط واختاروا كلمة المرور.",
    icon: Sparkles,
  },
  {
    title: "الدخول إلى LexHub",
    body: "اتصال فوري حسب الدور المحدد.",
    icon: CheckCircle2,
  },
];

/** Pipeline vertical animé — à côté du formulaire rejoindre. */
export function JoinPipeline() {
  const ar = useClientLocale() === "ar";
  const steps = ar ? STEPS_AR : STEPS_FR;

  return (
    <div
      className="join-pipeline rounded-3xl border border-white/15 bg-white/10 p-5 text-white backdrop-blur-md sm:p-6"
      dir={ar ? "rtl" : "ltr"}
    >
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#FFB07A]">
        {ar ? "كيف يعمل الانضمام" : "Comment ça marche"}
      </p>
      <h3 className="mt-2 font-serif text-2xl text-white">
        {ar ? "٣ خطوات" : "3 étapes"}
      </h3>
      <ol className="mt-6 space-y-0">
        {steps.map((s, i) => {
          const Icon = s.icon;
          return (
            <li key={s.title} className="relative flex gap-4 pb-7 last:pb-0">
              {i < steps.length - 1 ? (
                <span
                  className="join-pipeline__line absolute top-10 bottom-0 w-px bg-gradient-to-b from-[#FFB07A]/80 to-white/10"
                  style={{ insetInlineStart: "1.15rem" }}
                  aria-hidden
                />
              ) : null}
              <motion.span
                className="relative z-[1] flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#0B1A4D] text-[#FFB07A] ring-2 ring-[#FFB07A]/50"
                initial={{ scale: 0.7, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.12 * i, type: "spring", stiffness: 260, damping: 18 }}
              >
                <Icon className="h-4 w-4" />
              </motion.span>
              <motion.div
                initial={{ opacity: 0, x: ar ? 12 : -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.12 * i + 0.05, duration: 0.35 }}
              >
                <p className="text-sm font-semibold text-white">
                  <span className="me-2 text-[#FFB07A]">{i + 1}.</span>
                  {s.title}
                </p>
                <p className="mt-1 text-xs leading-relaxed text-white/70">{s.body}</p>
              </motion.div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
