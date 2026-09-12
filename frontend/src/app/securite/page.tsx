"use client";

import Link from "next/link";
import { useState } from "react";
import {
  EyeOff,
  FileCheck,
  Lock,
  Minus,
  Plus,
  Server,
  Shield,
  UserCheck,
} from "lucide-react";
import { PublicNavbar } from "@/components/layout/public-navbar";
import { PublicFooter } from "@/components/layout/public-footer";
import { Button } from "@/components/ui/button";
import { FadeIn } from "@/components/motion/fade-in";
import { useClientLocale, useTranslations } from "@/store/locale";
import { VisitorConvertNudge } from "@/components/billing/visitor-convert-nudge";
import { cn } from "@/lib/utils";

const ICONS = [Lock, Shield, Server, UserCheck, EyeOff, FileCheck];

const COMPLIANCE = [
  {
    titleFr: "Secret professionnel",
    titleAr: "سرّ المهنة",
    statusFr: "Conçu pour",
    statusAr: "مصمَّم لـ",
    tone: "ok" as const,
    descFr:
      "Isolation multi-cabinets, rôles avocat / assistant / admin, journal d’actions sensibles.",
    descAr: "عزل المكاتب، أدوار محامٍ / مساعد / مدير، سجل الإجراءات الحساسة.",
  },
  {
    titleFr: "Masquage PII",
    titleAr: "إخفاء البيانات الشخصية",
    statusFr: "Actif",
    statusAr: "مفعّل",
    tone: "ok" as const,
    descFr:
      "Noms des parties masqués avant envoi à l’IA. Vos pièces n’entraînent pas de modèles tiers.",
    descAr: "إخفاء أسماء الأطراف قبل الذكاء الاصطناعي. القطع لا تُدرّب نماذج خارجية.",
  },
  {
    titleFr: "Protection des données (Maroc)",
    titleAr: "حماية البيانات (المغرب)",
    statusFr: "En place",
    statusAr: "مفعّل",
    tone: "ok" as const,
    descFr:
      "Loi 09-08 : vos dossiers ne servent qu’à votre cabinet. Pas de revente. Contact : contact@lexhub.space.",
    descAr: "قانون 09-08: ملفاتكم لخدمة مكتبكم فقط. بلا بيع. تواصل: contact@lexhub.space.",
  },
  {
    titleFr: "Serveurs & journal",
    titleAr: "الخوادم والسجل",
    statusFr: "Actif",
    statusAr: "مفعّل",
    tone: "ok" as const,
    descFr:
      "Connexion HTTPS, fichiers chiffrés, historique « qui a fait quoi ». Certificat ISO formalisé : plus tard — on ne ment pas.",
    descAr: "HTTPS وتشفير وسجل من فعل ماذا. شهادة ISO رسمية لاحقاً — بلا ادعاء كاذب.",
  },
];

const SEC_FAQ_FR = [
  {
    q: "Où sont stockées mes données ?",
    a: "Sur l’infrastructure LexHub (serveurs applicatifs + base isolée par cabinet). Accès réservé à votre équipe via comptes nominatifs et rôles.",
  },
  {
    q: "Mes données entraînent-elles l’IA ?",
    a: "Non. Les documents servent uniquement à produire le résultat pour votre cabinet. Pas d’entraînement de modèles publics sur vos dossiers.",
  },
  {
    q: "Que se passe-t-il si je résilie ?",
    a: "Vous conservez l’accès jusqu’à la fin de la période payée / d’essai selon le plan. Export des actes Word/PDF possible. Contactez contact@lexhub.space pour une demande de suppression.",
  },
  {
    q: "Comment parler sécurité à mon barreau / mon client ?",
    a: "LexHub : outil de rédaction et de dossier, pas un avis juridique automatisé. Badge « à relire » sur l’IA, masquage des noms, acte exporté au nom du cabinet — pas de logo LexHub sur la pièce d’audience.",
  },
];

const SEC_FAQ_AR = [
  {
    q: "أين تُخزَّن بياناتي؟",
    a: "على بنية LexHub (خوادم وتطبيق وقاعدة معزولة لكل مكتب). الوصول لفريقكم فقط عبر حسابات وأدوار.",
  },
  {
    q: "هل تُدرَّب الذكاء الاصطناعي على بياناتي؟",
    a: "لا. الوثائق تخدم نتيجتكم فقط. بلا تدريب نماذج عامة على ملفاتكم.",
  },
  {
    q: "ماذا إن ألغيت الاشتراك؟",
    a: "تبقون حتى نهاية الفترة المدفوعة / التجربة حسب الخطة. تصدير Word/PDF ممكن. راسلوا contact@lexhub.space لطلب الحذف.",
  },
  {
    q: "كيف أشرح الأمان لهيئة المحامين / للموكل؟",
    a: "LexHub أداة صياغة وملف، ليس رأياً قانونياً آلياً. شارة «للمراجعة»، إخفاء الأسماء، وثيقة باسم المكتب — بلا شعار LexHub على وثيقة الجلسة.",
  },
];

export default function SecuritePage() {
  const tr = useTranslations();
  const ar = useClientLocale() === "ar";
  const [openFaq, setOpenFaq] = useState<number | null>(0);
  const faqs = ar ? SEC_FAQ_AR : SEC_FAQ_FR;

  return (
    <div className="min-h-screen bg-sanad-cream" dir={ar ? "rtl" : "ltr"}>
      <PublicNavbar variant="light" />
      <VisitorConvertNudge />

      <section className="relative overflow-hidden border-b border-sanad-navy/10 bg-[#0B1A4D] py-20 text-white sm:py-24">
        <div
          className="pointer-events-none absolute inset-0 opacity-40"
          style={{
            background:
              "radial-gradient(ellipse 70% 60% at 50% -10%, rgba(59,92,222,0.45), transparent 55%), radial-gradient(ellipse 50% 40% at 90% 80%, rgba(255,138,45,0.18), transparent 50%)",
          }}
        />
        <div className="relative mx-auto max-w-3xl px-4 text-center sm:px-6">
          <FadeIn>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#FF8A2D]">
              LexHub · {ar ? "الثقة" : "Confiance"}
            </p>
            <div className="mx-auto mt-6 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/15 bg-white/10 backdrop-blur-sm">
              <Shield className="h-7 w-7 text-[#FF8A2D]" strokeWidth={1.75} />
            </div>
            <h1 className="mt-6 font-display text-4xl font-semibold tracking-tight text-white sm:text-5xl">
              {ar
                ? "ذكاء قانوني مغربي مبني على الثقة"
                : "LegalTech marocaine, construite pour la confiance"}
            </h1>
            <p className="mx-auto mt-5 max-w-2xl text-base leading-relaxed text-white/90 sm:text-lg">
              {tr.security.subtitle}
            </p>
          </FadeIn>
        </div>
      </section>

      <section className="border-b border-sanad-navy/10 bg-white py-14 sm:py-16">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          <FadeIn>
            <h2 className="text-center font-display text-2xl font-semibold text-sanad-navy sm:text-3xl">
              {ar ? "الامتثال والمعايير" : "Conformité & standards"}
            </h2>
            <p className="mx-auto mt-3 max-w-xl text-center text-sm text-sanad-navy/70">
              {ar
                ? "شفافية صريحة: ما هو مفعّل، ما هو قيد المواءمة، وما هو في خارطة الطريق."
                : "Transparence assumée : ce qui est actif, en alignement, ou sur la feuille de route."}
            </p>
            <div className="mt-10 grid gap-4 sm:grid-cols-2">
              {COMPLIANCE.map((c) => (
                <div
                  key={c.titleFr}
                  className="rounded-2xl border border-sanad-navy/10 bg-[#F7F8FC] p-5"
                >
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="font-display text-base font-semibold text-sanad-navy">
                      {ar ? c.titleAr : c.titleFr}
                    </h3>
                    <span
                      className={cn(
                        "rounded-full px-2.5 py-0.5 text-[11px] font-semibold",
                        c.tone === "ok" && "bg-emerald-100 text-emerald-800",
                        c.tone === "progress" && "bg-amber-100 text-amber-900",
                        c.tone === "planned" && "bg-slate-200 text-slate-700",
                      )}
                    >
                      {ar ? c.statusAr : c.statusFr}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-relaxed text-sanad-navy/75">
                    {ar ? c.descAr : c.descFr}
                  </p>
                </div>
              ))}
            </div>
          </FadeIn>
        </div>
      </section>

      <section className="py-16 sm:py-20">
        <div className="mx-auto max-w-4xl space-y-10 px-4 sm:px-6">
          <FadeIn>
            <h2 className="mb-6 font-display text-xl font-semibold text-sanad-navy sm:text-2xl">
              {ar ? "أمن حسب التصميم" : "Sécurité by design"}
            </h2>
            <div className="grid gap-4 sm:grid-cols-2">
              {tr.security.items.map((item, i) => {
                const Icon = ICONS[i % ICONS.length];
                return (
                  <div
                    key={item}
                    className="flex items-start gap-4 rounded-2xl border border-sanad-navy/10 bg-white p-5 shadow-sm"
                  >
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#1B3F9C]/10">
                      <Icon className="h-5 w-5 text-[#1B3F9C]" />
                    </div>
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-[#FF6A00]">
                        {String(i + 1).padStart(2, "0")}
                      </p>
                      <p className="mt-1 text-sm font-medium leading-relaxed text-sanad-navy">
                        {item}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </FadeIn>

          <FadeIn>
            <h2 className="mb-5 text-center font-display text-xl font-semibold text-sanad-navy sm:text-2xl">
              {ar ? "أسئلة الأمان" : "FAQ sécurité"}
            </h2>
            <div className="space-y-3">
              {faqs.map((f, i) => {
                const open = openFaq === i;
                return (
                  <button
                    key={f.q}
                    type="button"
                    onClick={() => setOpenFaq(open ? null : i)}
                    className={cn(
                      "w-full rounded-2xl border bg-white px-5 py-4 text-start shadow-sm transition",
                      open ? "border-[#1B3F9C]/35" : "border-sanad-navy/10",
                    )}
                    aria-expanded={open}
                  >
                    <span className="flex items-start justify-between gap-3">
                      <span
                        className={cn(
                          "font-display text-[15px] font-semibold",
                          open ? "text-[#1B3F9C]" : "text-sanad-navy",
                        )}
                      >
                        {f.q}
                      </span>
                      <span className="mt-0.5 text-[#1B3F9C]">
                        {open ? <Minus className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
                      </span>
                    </span>
                    {open ? (
                      <p className="mt-3 border-t border-sanad-navy/10 pt-3 text-sm leading-relaxed text-sanad-navy/80">
                        {f.a}
                      </p>
                    ) : null}
                  </button>
                );
              })}
            </div>
          </FadeIn>

          <FadeIn className="text-center">
            <Link href="/login?tab=register">
              <Button size="lg" variant="gold" className="btn-3d">
                {tr.cta.button}
              </Button>
            </Link>
            <p className="mt-4 text-sm text-sanad-navy/70">
              <Link href="/#faq" className="font-semibold text-[#1B3F9C] hover:underline">
                {ar ? "كل الأسئلة الشائعة ←" : "Toutes les FAQ landing ←"}
              </Link>
            </p>
          </FadeIn>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
