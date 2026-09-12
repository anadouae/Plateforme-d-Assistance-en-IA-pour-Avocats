"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Check, Sparkles } from "lucide-react";
import { api, type BillingPlan } from "@/lib/api";
import { FALLBACK_BILLING_PLANS } from "@/lib/billing-plans-fallback";
import { useAuthStore } from "@/store/auth";
import { useClientLocale, useTranslations } from "@/store/locale";
import { canManageTeam } from "@/lib/roles";
import { TrialPitchModal } from "@/components/billing/trial-pitch-modal";
import { AuthGateModal } from "@/components/billing/auth-gate-modal";
import { AskAdminBillingModal } from "@/components/billing/ask-admin-billing";
import { saveBillingIntent, checkoutHref, commercialHref, needsCommercialQualification } from "@/lib/billing-intent";
import { planCtaLabel, planCtaSub, planTrialBadge } from "@/lib/plan-cta";

function planHighlights(plan: BillingPlan, ar: boolean): string[] {
  if (ar && plan.highlights_ar?.length) return plan.highlights_ar.slice(0, 5);
  if (plan.highlights?.length) return plan.highlights.slice(0, 5);
  const seats = [
    plan.max_avocats > 0
      ? ar
        ? `${plan.max_avocats} محامٍ`
        : `${plan.max_avocats} avocat(s)`
      : null,
    plan.max_assistants > 0
      ? ar
        ? `${plan.max_assistants} مساعد`
        : `${plan.max_assistants} assistant(s)`
      : ar
        ? "بدون مساعد"
        : "0 assistant",
  ].filter(Boolean) as string[];
  const pleas =
    plan.max_plaidoiries_month < 0
      ? ar
        ? "مرافعات غير محدودة"
        : "Plaidoiries illimitées"
      : ar
        ? `${plan.max_plaidoiries_month} مرافعة / شهر`
        : `${plan.max_plaidoiries_month} plaidoiries / mois`;
  return [...seats, pleas].slice(0, 5);
}

export function LandingPricingCarousel() {
  const ar = useClientLocale() === "ar";
  const p = useTranslations().pricing;
  const user = useAuthStore((s) => s.user);
  const [plans, setPlans] = useState<BillingPlan[]>(FALLBACK_BILLING_PLANS);
  const [cycle, setCycle] = useState<"monthly" | "yearly">("monthly");
  const [active, setActive] = useState(2);
  const [pitchPlan, setPitchPlan] = useState<BillingPlan | null>(null);
  const [authPlan, setAuthPlan] = useState<BillingPlan | null>(null);
  const [askAdmin, setAskAdmin] = useState(false);

  useEffect(() => {
    api
      .getBillingPlans()
      .then((list) => setPlans(list.length ? list : FALLBACK_BILLING_PLANS))
      .catch(() => setPlans(FALLBACK_BILLING_PLANS));
  }, []);

  const ordered = [...plans].sort((a, b) => a.sort_order - b.sort_order);

  const price = (plan: BillingPlan) =>
    cycle === "yearly" ? plan.price_mad_yearly : plan.price_mad_monthly;

  function choosePlan(plan: BillingPlan) {
    if (needsCommercialQualification(plan.slug)) {
      window.location.assign(commercialHref("enterprise"));
      return;
    }
    saveBillingIntent({ plan: plan.slug, cycle, intent: plan.slug === "free" ? "free" : "trial" });
    if (plan.slug === "free" && user) {
      window.location.assign("/dashboard");
      return;
    }
    setPitchPlan(plan);
  }

  function afterPitch() {
    const plan = pitchPlan;
    setPitchPlan(null);
    if (!plan) return;
    if (plan.slug === "free") {
      if (!user) setAuthPlan(plan);
      else window.location.assign("/dashboard");
      return;
    }
    if (!user) {
      setAuthPlan(plan);
      return;
    }
    if (canManageTeam(user.role)) {
      window.location.assign(checkoutHref(plan.slug, cycle));
    } else {
      setAskAdmin(true);
    }
  }

  return (
    <section id="tarifs" className="overflow-hidden bg-[var(--lr-paper)] px-6 py-[100px] sm:px-8">
      <div className="mx-auto max-w-[1100px] text-center">
        <p className="font-mono text-[11.5px] uppercase tracking-[0.14em] text-[#FF6A00]">
          LexHub · {ar ? "الأسعار" : "Tarifs"}
        </p>
        <h2 className="font-display mt-3 text-[clamp(28px,4vw,40px)] font-semibold text-[var(--lr-ink)]">
          {ar ? "الباقة المناسبة لمكتبكم" : "La bonne formule pour votre cabinet"}
        </h2>
        <p className="mx-auto mt-3 max-w-lg text-sm text-[var(--lr-ink-soft)]">{p.trialNote}</p>

        <div className="mt-8 inline-flex rounded-full border border-[var(--lr-line-light)] bg-white p-1">
          {(["monthly", "yearly"] as const).map((c) => (
            <button
              key={c}
              type="button"
              className={`rounded-full px-5 py-2 text-sm font-medium transition ${
                cycle === c ? "bg-[var(--lr-royal-900)] text-white" : "text-slate-600"
              }`}
              onClick={() => setCycle(c)}
            >
              {c === "monthly" ? p.monthly : p.yearly}
            </button>
          ))}
        </div>

        <div className="lr-pricing-stage relative mx-auto mt-14 h-[560px] max-w-[980px] perspective-[1200px] sm:h-[580px]">
          {ordered.map((plan, i) => {
            const offset = i - active;
            const isCenter = offset === 0;
            const amt = price(plan);
            const name = ar && plan.name_ar ? plan.name_ar : plan.name;
            const trialDays = plan.trial_days > 0 ? plan.trial_days : 0;
            const highlights = planHighlights(plan, ar);
            return (
              <motion.div
                key={plan.id}
                layout
                role="button"
                tabIndex={0}
                onClick={() => setActive(i)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    setActive(i);
                  }
                }}
                className={`lr-pricing-card absolute left-1/2 top-0 flex w-[min(300px,82vw)] -translate-x-1/2 cursor-pointer flex-col rounded-2xl border bg-white p-5 text-start shadow-xl transition-colors sm:p-6 ${
                  plan.is_recommended
                    ? "border-[#FF6A00] ring-2 ring-[#FF6A00]/25"
                    : "border-slate-200"
                } ${isCenter ? "z-20" : "z-10"}`}
                animate={{
                  rotateY: offset * -22,
                  x: offset * 210,
                  scale: isCenter ? 1.06 : 0.86,
                  opacity: Math.abs(offset) > 2 ? 0 : Math.abs(offset) === 0 ? 1 : 0.7,
                  zIndex: isCenter ? 20 : 10 - Math.abs(offset),
                }}
                transition={{ type: "spring", stiffness: 260, damping: 26 }}
                style={{ transformStyle: "preserve-3d" }}
              >
                {plan.is_recommended ? (
                  <span className="mb-2 inline-flex w-fit items-center gap-1 rounded-full bg-[#FF6A00] px-2 py-0.5 text-[10px] font-bold uppercase text-white">
                    <Sparkles className="h-3 w-3" />
                    {ar ? "الأكثر شعبية" : "Populaire"}
                  </span>
                ) : null}
                <p className="text-lg font-semibold uppercase tracking-wide text-[var(--lr-ink)]">{name}</p>
                <p className="mt-2 font-display text-3xl font-semibold text-[var(--lr-royal-900)] sm:text-4xl">
                  {amt === 0 ? "0" : amt.toLocaleString(ar ? "ar-MA" : "fr-FR")}
                  <span className="text-sm font-normal text-slate-500">
                    {" "}
                    {amt === 0 ? p.madFree : `MAD/${cycle === "yearly" ? p.year : p.month}`}
                  </span>
                </p>
                <p className="mt-2 line-clamp-2 text-xs text-slate-600">{plan.description}</p>
                {trialDays > 0 ? (
                  <span className="mt-2 inline-flex w-fit rounded-full bg-emerald-50 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-800">
                    {planTrialBadge(plan, ar)}
                  </span>
                ) : null}

                <ul className="mt-4 flex-1 space-y-2 border-t border-slate-100 pt-3">
                  {highlights.map((h) => (
                    <li key={h} className="flex gap-2 text-[11px] leading-snug text-slate-700 sm:text-xs">
                      <Check
                        className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--lr-royal-900)]"
                        strokeWidth={2.5}
                      />
                      <span>{h}</span>
                    </li>
                  ))}
                </ul>

                {isCenter ? (
                  <div className="mt-5">
                    <button
                      type="button"
                      className="block w-full rounded-xl bg-[var(--lr-royal-900)] py-2.5 text-center text-sm font-semibold text-white hover:bg-[var(--lr-royal-800)]"
                      onClick={(e) => {
                        e.stopPropagation();
                        choosePlan(plan);
                      }}
                    >
                      {planCtaLabel(plan, ar, { loggedIn: !!user })}
                    </button>
                    {planCtaSub(plan, ar) ? (
                      <p className="mt-1.5 text-center text-[10px] text-slate-500">
                        {planCtaSub(plan, ar)}
                      </p>
                    ) : null}
                  </div>
                ) : (
                  <p className="mt-4 text-center text-[11px] font-medium text-slate-400">
                    {ar ? "اضغطوا للعرض" : "Cliquez pour voir"}
                  </p>
                )}
              </motion.div>
            );
          })}
        </div>

        <div className="mt-6 flex justify-center gap-2">
          {ordered.map((_, i) => (
            <button
              key={i}
              type="button"
              aria-label={`Plan ${i + 1}`}
              className={`h-2 w-2 rounded-full transition ${i === active ? "w-6 bg-[#FF6A00]" : "bg-slate-300"}`}
              onClick={() => setActive(i)}
            />
          ))}
        </div>

        <Link
          href="/tarifs"
          className="mt-8 inline-block text-sm font-semibold text-[var(--lr-royal-900)] underline"
        >
          {ar ? "كل التفاصيل →" : "Voir tous les détails →"}
        </Link>
        <p className="mt-3 text-xs text-slate-500">
          {ar ? (
            <>
              مكاتب كبيرة جداً؟{" "}
              <Link href="/commercial?intent=custom" className="font-semibold underline">
                عرض حسب الطلب
              </Link>
            </>
          ) : (
            <>
              Très gros cabinet ?{" "}
              <Link href="/commercial?intent=custom" className="font-semibold underline">
                Sur mesure — appelez-nous
              </Link>
            </>
          )}
        </p>
      </div>

      <TrialPitchModal
        open={!!pitchPlan}
        onClose={() => setPitchPlan(null)}
        onContinue={afterPitch}
        plan={pitchPlan}
        cycle={cycle}
        ar={ar}
      />
      <AuthGateModal
        open={!!authPlan}
        onClose={() => setAuthPlan(null)}
        planSlug={authPlan?.slug || "pro"}
        cycle={cycle}
        ar={ar}
      />
      <AskAdminBillingModal open={askAdmin} onClose={() => setAskAdmin(false)} ar={ar} />
    </section>
  );
}
