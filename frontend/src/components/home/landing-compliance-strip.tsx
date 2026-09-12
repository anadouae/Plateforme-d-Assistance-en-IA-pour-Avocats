"use client";

import { EyeOff, FileText, Languages, Shield } from "lucide-react";

const ITEMS = [
  {
    icon: Shield,
    fr: "Secret professionnel",
    ar: "سرّ المهنة",
    hintFr: "Isolation cabinet · rôles",
    hintAr: "عزل المكتب · أدوار",
  },
  {
    icon: EyeOff,
    fr: "Noms masqués avant l’IA",
    ar: "إخفاء الأسماء قبل الذكاء",
    hintFr: "Avant envoi au cloud",
    hintAr: "قبل الإرسال للسحابة",
  },
  {
    icon: FileText,
    fr: "Acte au nom du cabinet",
    ar: "الوثيقة باسم المكتب",
    hintFr: "Pas de logo LexHub",
    hintAr: "بدون شعار LexHub",
  },
  {
    icon: Languages,
    fr: "Arabe juridique (fusḥā)",
    ar: "عربية قانونية فصحى",
    hintFr: "Droit marocain · CPC & DOC",
    hintAr: "قانون مغربي · المسطرة و ظهير الالتزامات",
  },
] as const;

/** Barre de confiance type LegalTech — messages barreau marocain (pas GDPR-EU cloné). */
export function LandingComplianceStrip({ ar }: { ar: boolean }) {
  return (
    <section
      className="relative z-20 border-y border-[rgba(11,26,77,0.08)] bg-[#F7F8FC] px-4 py-5 sm:px-8"
      aria-label={ar ? "ضمانات الثقة" : "Signaux de confiance"}
    >
      <div className="mx-auto grid max-w-[1080px] gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.fr}
              className="flex items-center gap-3 rounded-xl border border-[rgba(11,26,77,0.08)] bg-white px-3.5 py-3"
            >
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#1B3F9C]/10 text-[#1B3F9C]">
                <Icon className="h-4 w-4" strokeWidth={1.75} />
              </span>
              <div className="min-w-0">
                <p className="truncate text-[13px] font-semibold text-[#0B1A4D]">
                  {ar ? item.ar : item.fr}
                </p>
                <p className="truncate text-[11px] text-[#5A6A85]">
                  {ar ? item.hintAr : item.hintFr}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
