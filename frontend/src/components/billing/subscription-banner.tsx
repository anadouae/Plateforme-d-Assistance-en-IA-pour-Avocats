"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type BillingEntitlements } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useClientLocale } from "@/store/locale";
import { canManageTeam, isAssistant } from "@/lib/roles";

export function SubscriptionBanner() {
  const ar = useClientLocale() === "ar";
  const user = useAuthStore((s) => s.user);
  const isAdmin = canManageTeam(user?.role);
  const [ent, setEnt] = useState<BillingEntitlements | null>(null);

  useEffect(() => {
    if (!user || user.role === "admin_webvoice") return;
    let cancelled = false;
    api
      .getBillingEntitlements()
      .then((e) => {
        if (!cancelled) setEnt(e);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [user?.id, user?.role]);

  if (!user || user.role === "admin_webvoice") return null;
  // Assistants : pas de bannière tarifs / abonnement
  if (isAssistant(user.role)) return null;

  if (!ent || !ent.plan) return null;

  const trialLeft = ent.trial_days_left;
  const used = ent.usage?.plaidoiries_used ?? 0;
  const limit = ent.usage?.plaidoiries_limit ?? -1;
  const nearQuota = limit >= 0 && used / Math.max(limit, 1) >= 0.8;
  const showTrial = ent.status === "trial" && trialLeft != null;
  const onFreeAfterTrial =
    ent.status === "active" &&
    (ent.plan as { slug?: string }).slug === "free" &&
    !showTrial;
  const urgentTrial = showTrial && trialLeft != null && trialLeft <= 3;
  const pastDue = ent.status === "past_due";
  const periodEnd = ent.current_period_end ? new Date(ent.current_period_end) : null;
  const daysToRenew =
    periodEnd && !Number.isNaN(periodEnd.getTime())
      ? Math.max(0, Math.ceil((periodEnd.getTime() - Date.now()) / 86400000))
      : null;
  const renewalSoon =
    ent.status === "active" &&
    (ent.plan as { slug?: string }).slug !== "free" &&
    !ent.cancel_at_period_end &&
    daysToRenew != null &&
    daysToRenew <= 7;

  if (!showTrial && !nearQuota && !onFreeAfterTrial && !pastDue && !renewalSoon) return null;

  const planName =
    ar && (ent.plan as { name_ar?: string }).name_ar
      ? (ent.plan as { name_ar?: string }).name_ar!
      : ent.plan.name;

  const ctaHref = "/settings#abonnement";
  let ctaLabel = isAdmin
    ? ar
      ? "إدارة الاشتراك"
      : "Gérer l'abonnement"
    : ar
      ? "عرض الاشتراك"
      : "Voir l'abonnement";
  let message: JSX.Element | null = null;
  let tone =
    "lex-app-banner border-[color:var(--gold-soft)] bg-gradient-to-r from-orange-50 to-sanad-cream";

  if (pastDue) {
    tone = "lex-app-banner lex-app-banner--danger border-red-300 bg-gradient-to-r from-red-50 to-orange-50";
    ctaLabel = isAdmin
      ? ar
        ? "تسوية الدفع"
        : "Régulariser le paiement"
      : ar
        ? "أخبر مدير المكتب"
        : "Prévenir l'admin cabinet";
    message = (
      <p>
        <strong>{ar ? "فشل الدفع" : "Paiement en échec"}</strong>
        {ent.access_restricted
          ? ar
            ? " — الوصول مقيّد (مرافعات IA متوقفة). سوّوا الدفع فوراً."
            : " — accès restreint (plaidoiries IA bloquées). Régularisez immédiatement."
          : isAdmin
            ? ar
              ? ` — سوّوا الدفع خلال ${7 - (ent.past_due_days || 0)} يوماً لتجنب التقييد.`
              : ` — régularisez sous ${Math.max(0, 7 - (ent.past_due_days || 0))} j pour éviter la restriction.`
            : ar
              ? " — اطلبوا من مدير المكتب تسوية الاشتراك."
              : " — demandez à l'admin du cabinet de régulariser l'abonnement."}
      </p>
    );
  } else if (showTrial) {
    tone = urgentTrial
      ? "lex-app-banner lex-app-banner--urgent border-orange-300/90 bg-gradient-to-r from-orange-50 to-amber-50"
      : "lex-app-banner border-[color:var(--gold-soft)] bg-gradient-to-r from-orange-50 to-sanad-cream";
    ctaLabel = isAdmin
      ? urgentTrial
        ? ar
          ? "اختيار خطتي"
          : "Choisir mon plan"
        : ar
          ? "عرض الخطط"
          : "Voir les plans"
      : ar
        ? "عرض الأسعار"
        : "Voir les tarifs";
    message = (
      <p>
        {ar ? "تجربة" : "Essai"} <strong>{planName}</strong> —{" "}
        <strong>{trialLeft}</strong>{" "}
        {ar
          ? trialLeft === 1
            ? "يوم متبقٍ"
            : "أيام متبقية"
          : `jour${trialLeft === 1 ? "" : "s"} restant${trialLeft === 1 ? "" : "s"}`}
        {urgentTrial ? (
          <span className="lex-app-banner__muted text-orange-800">
            {" "}
            ·{" "}
            {ar
              ? "الانتقال إلى الاكتشاف قريبًا"
              : "bascule Découverte bientôt"}
            {!isAdmin
              ? ar
                ? " — أخبروا مدير المكتب"
                : " — signalez-le à votre admin"
              : ""}
          </span>
        ) : null}
        {limit >= 0 ? (
          <span className="lex-app-banner__muted text-slate-600">
            {" "}
            · {used}/{limit} {ar ? "مرافعة هذا الشهر" : "plaidoiries ce mois"}
          </span>
        ) : null}
      </p>
    );
  } else if (onFreeAfterTrial) {
    tone =
      "lex-app-banner border-[color:var(--gold)]/40 bg-gradient-to-r from-sanad-cream to-orange-50";
    ctaLabel = isAdmin
      ? ar
        ? "الترقية إلى Solo أو Cabinet"
        : "Passer à Solo ou Cabinet"
      : ar
        ? "عرض الأسعار"
        : "Voir les tarifs";
    message = (
      <p>
        {ar ? (
          <>
            خطة <strong>الاكتشاف</strong> — حصص محدودة.
            {isAdmin
              ? " انتقلوا إلى Solo (299 درهم) أو Cabinet (699 درهم)."
              : " فقط مسؤول المكتب يمكنه الترقية."}
          </>
        ) : (
          <>
            Plan <strong>Découverte</strong> — quotas limités.
            {isAdmin
              ? " Passez à Solo (299 MAD) ou Cabinet (699 MAD)."
              : " Seul le responsable du cabinet peut upgrader."}
          </>
        )}
      </p>
    );
  } else if (renewalSoon) {
    tone = "lex-app-banner lex-app-banner--info border-sky-200 bg-gradient-to-r from-sky-50 to-white";
    ctaLabel = isAdmin
      ? ar
        ? "عرض التجديد"
        : "Voir le renouvellement"
      : ar
        ? "عرض الاشتراك"
        : "Voir l'abonnement";
    message = (
      <p>
        {ar ? (
          <>
            تجديد <strong>{planName}</strong> خلال <strong>{daysToRenew}</strong> يومًا.
          </>
        ) : (
          <>
            Renouvellement <strong>{planName}</strong> dans <strong>{daysToRenew}</strong> j.
          </>
        )}
      </p>
    );
  } else {
    ctaLabel = isAdmin
      ? ar
        ? "زيادة الخطة"
        : "Augmenter mon plan"
      : ar
        ? "عرض الأسعار"
        : "Voir les tarifs";
    message = (
      <p>
        {ar ? (
          <>
            حصة المرافعات : <strong>{used}/{limit}</strong>
            {isAdmin
              ? " — تجنبوا الانقطاع قبل الجلسة."
              : " — يمكن لمسؤول المكتب زيادة الخطة."}
          </>
        ) : (
          <>
            Quota plaidoiries : <strong>{used}/{limit}</strong>
            {isAdmin
              ? " — évitez une coupure en audience."
              : " — le responsable du cabinet peut augmenter le plan."}
          </>
        )}
      </p>
    );
  }

  return (
    <div className={`mx-4 mt-3 rounded-xl border px-4 py-2.5 text-sm shadow-sm sm:mx-6 ${tone}`} dir={ar ? "rtl" : "ltr"}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">{message}</div>
        <Link
          href={isAdmin ? ctaHref : "/tarifs"}
          className="lex-app-banner__cta shrink-0 rounded-lg bg-sanad-navy px-3 py-1.5 text-xs font-semibold text-white hover:bg-sanad-navy/90"
        >
          {ctaLabel}
        </Link>
      </div>
      {limit > 0 && (showTrial || nearQuota) ? (
        <div className="lex-app-banner__meter mt-2 h-1.5 overflow-hidden rounded-full bg-black/10">
          <div
            className="h-full rounded-full bg-sanad-gold transition-all"
            style={{ width: `${Math.min(100, (used / limit) * 100)}%` }}
          />
        </div>
      ) : null}
    </div>
  );
}
