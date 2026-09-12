"use client";

import type { BillingPlan } from "@/lib/api";
import { LexProductModal } from "@/components/billing/lex-product-modal";

type Props = {
  open: boolean;
  onClose: () => void;
  onContinue: () => void;
  plan: BillingPlan | null;
  cycle: "monthly" | "yearly";
  ar: boolean;
};

export function TrialPitchModal({ open, onClose, onContinue, plan, cycle, ar }: Props) {
  if (!open || !plan) return null;

  const trialDays = plan.trial_days > 0 ? plan.trial_days : 30;
  const price = cycle === "yearly" ? plan.price_mad_yearly : plan.price_mad_monthly;
  const name = ar && plan.name_ar ? plan.name_ar : plan.name;
  const isFree = price <= 0;

  const points = isFree
    ? [
        ar ? "ابدأ مجانًا بدون بطاقة" : "Commencez gratuitement, sans carte",
        ar ? "حصص محدودة لاكتشاف LexHub" : "Quotas limités pour découvrir LexHub",
        ar ? "ترقية في أي وقت إلى Solo أو Cabinet" : "Passez à Solo / Cabinet quand vous voulez",
      ]
    : [
        ar
          ? `وصول كامل إلى خطة ${name} خلال ${trialDays} يومًا`
          : `Accès complet au plan ${name} pendant ${trialDays} jours`,
        ar ? "ألغِ في أي وقت قبل نهاية التجربة — بدون خصم" : "Annulez avant la fin de l’essai — aucun débit",
        ar
          ? `ثم ${price.toLocaleString("fr-FR")} درهم / ${cycle === "yearly" ? "سنة" : "شهر"}`
          : `Puis ${price.toLocaleString("fr-FR")} MAD / ${cycle === "yearly" ? "an" : "mois"}`,
      ];

  return (
    <LexProductModal
      open={open}
      onClose={onClose}
      zIndexClass="z-[80]"
      tag={isFree ? (ar ? "اكتشاف" : "Découverte") : ar ? "تجربة مجانية" : "Essai gratuit"}
      title={
        isFree
          ? ar
            ? "ابدأ بخطة الاكتشاف"
            : "Commencer avec Découverte"
          : ar
            ? `ابدأ تجربتك المجانية ${trialDays} يومًا`
            : `Démarrez votre essai ${trialDays} jours`
      }
      points={points}
      primaryLabel={
        isFree
          ? ar
            ? "متابعة"
            : "Continuer"
          : ar
            ? "بدء التجربة المجانية"
            : "Démarrer l’essai gratuit"
      }
      onPrimary={onContinue}
      secondaryLabel={ar ? "رجوع" : "Retour"}
      closeLabel={ar ? "إغلاق" : "Fermer"}
    />
  );
}
