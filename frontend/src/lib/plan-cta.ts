import type { BillingPlan } from "@/lib/api";

/** Badge essai affiché sur les cartes plan. */
export function planTrialBadge(plan: BillingPlan, ar: boolean): string | null {
  if (plan.slug === "free" || plan.trial_days <= 0) return null;
  return ar ? `${plan.trial_days} يومًا مجانًا` : `${plan.trial_days} j d'essai`;
}

/** Libellé bouton tarifs / landing — pro, avec durée d'essai explicite. */
export function planCtaLabel(
  plan: BillingPlan,
  ar: boolean,
  opts?: { loggedIn?: boolean },
): string {
  if (plan.slug === "free") {
    return ar ? "ابدأ مجانًا" : "Commencer gratuitement";
  }
  const days = plan.trial_days > 0 ? plan.trial_days : 30;

  if (opts?.loggedIn) {
    return ar
      ? `ترقية · ${days} يومًا مجانًا`
      : `Upgrader — ${days} j offerts`;
  }

  return ar
    ? `ابدأ التجربة · ${days} يومًا`
    : `Essai gratuit · ${days} jours`;
}

/** Sous-titre optionnel sous le bouton (cartes larges). */
export function planCtaSub(plan: BillingPlan, ar: boolean): string | null {
  if (plan.slug === "free") return ar ? "بدون بطاقة" : "Sans carte";
  return ar ? `0 درهم اليوم · إلغاء في أي وقت` : `0 MAD aujourd'hui · annulable`;
}
