"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Coins, Minus, AlertTriangle } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { useBillingCredits } from "@/store/billing-credits";
import { setDailyOverageHandler } from "@/lib/api";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { cn } from "@/lib/utils";

export function CreditSpendHost() {
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const refresh = useBillingCredits((s) => s.refresh);
  const toasts = useBillingCredits((s) => s.toasts);
  const dismiss = useBillingCredits((s) => s.dismiss);
  const ent = useBillingCredits((s) => s.entitlements);
  const confirm = useConfirm();
  const router = useRouter();
  const [shake, setShake] = useState(false);

  useEffect(() => {
    if (!token || !user || user.role === "admin_webvoice") return;
    void refresh();
  }, [token, user, refresh]);

  useEffect(() => {
    if (!user || user.role === "admin_webvoice") {
      setDailyOverageHandler(null);
      return;
    }
    setDailyOverageHandler(async (info) => {
      const lim = info.dailyLimit;
      const used = info.dailyUsed;
      const plan = (info.planName || "").trim() || "votre plan";
      const phase = info.isTrial
        ? `Vous êtes en essai « ${plan} »`
        : `Vous êtes sur l’abonnement « ${plan} »`;
      const usageLine =
        lim != null && used != null
          ? `Aujourd’hui : ${used} / ${lim} crédits IA (repère du jour).`
          : "Repère IA du jour atteint.";
      return confirm({
        title: "Beaucoup d’IA aujourd’hui",
        description:
          `${phase}.\n` +
          `${usageLine}\n\n` +
          "Même règle pour tous les plans (Découverte, Solo, Cabinet, Entreprise — essai ou payant) : " +
          "ce n’est pas un problème de paiement.\n\n" +
          "• Continuer maintenant → l’IA part ; on débite vos crédits (mois ou essai).\n" +
          "• Attendre demain → le compteur du jour repart à zéro demain.",
        confirmLabel: "Continuer maintenant",
        cancelLabel: "Attendre demain",
      });
    });
    return () => setDailyOverageHandler(null);
  }, [user, confirm]);

  if (!user || user.role === "admin_webvoice") return null;

  const used = ent?.usage?.ai_credits_used ?? 0;
  const lim = ent?.usage?.ai_credits_limit ?? -1;
  const rem = lim < 0 ? null : Math.max(0, lim - used);
  const dailyLim = ent?.ai_daily_limit ?? 0;
  const dailyUsed = ent?.ai_daily_used ?? 0;
  const dailyRem = dailyLim > 0 ? Math.max(0, dailyLim - dailyUsed) : null;
  const low = rem != null && lim > 0 && (rem <= 15 || rem / lim <= 0.15);
  const dailyLow =
    dailyRem != null && dailyLim > 0 && (dailyRem === 0 || dailyRem / dailyLim <= 0.2);

  function openCredits(e: React.MouseEvent) {
    e.preventDefault();
    setShake(true);
    window.setTimeout(() => {
      setShake(false);
      router.push("/settings#plan");
    }, 320);
  }

  const title =
    rem != null && dailyRem != null
      ? `${rem} crédits ce mois · ${dailyRem} aujourd’hui — ouvrir Plan & usage`
      : rem != null
        ? `${rem} crédits IA restants — ouvrir Plan & usage`
        : dailyRem != null
          ? `${dailyRem} crédits aujourd’hui — ouvrir Plan & usage`
          : "Crédits IA";

  return (
    <>
      {rem != null || dailyRem != null ? (
        <Link
          href="/settings#plan"
          onClick={openCredits}
          className={cn(
            "credit-pill",
            (low || dailyLow) && "credit-pill--low",
            rem === 0 && "credit-pill--empty",
            shake && "credit-pill--shake",
          )}
          title={title}
          aria-label={title}
        >
          <Coins className="h-3.5 w-3.5" aria-hidden />
          {rem != null ? (
            <>
              <span className="credit-pill__n">{rem}</span>
              <span className="credit-pill__lbl">crédits</span>
            </>
          ) : null}
          {dailyRem != null ? (
            <>
              {rem != null ? <span className="credit-pill__sep">·</span> : null}
              <span className="credit-pill__n">{dailyRem}</span>
              <span className="credit-pill__lbl">auj.</span>
            </>
          ) : null}
        </Link>
      ) : null}

      <div className="credit-toast-stack" aria-live="polite">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "credit-toast",
              t.kind === "spend" && "credit-toast--spend",
              t.kind === "low" && "credit-toast--low",
              t.kind === "empty" && "credit-toast--empty",
              t.kind === "daily" && "credit-toast--daily",
              t.kind === "daily-empty" && "credit-toast--daily-empty",
            )}
            role="status"
          >
            <div className="credit-toast__icon">
              {t.kind === "spend" ? (
                <Minus className="h-4 w-4" strokeWidth={2.5} />
              ) : (
                <AlertTriangle className="h-4 w-4" />
              )}
            </div>
            <div className="credit-toast__body">
              {t.kind === "spend" ? (
                <>
                  <p className="credit-toast__title">
                    −{t.delta} crédit{t.delta > 1 ? "s" : ""}
                  </p>
                  <p className="credit-toast__sub">{t.label}</p>
                  {t.remaining != null ? (
                    <p className="credit-toast__rem">
                      Il vous reste {t.remaining} ce mois
                      {t.dailyRemaining != null ? ` · ${t.dailyRemaining} aujourd’hui` : ""}.
                    </p>
                  ) : t.dailyRemaining != null ? (
                    <p className="credit-toast__rem">Il vous reste {t.dailyRemaining} aujourd’hui.</p>
                  ) : null}
                </>
              ) : t.kind === "low" ? (
                <>
                  <p className="credit-toast__title">Solde bientôt épuisé</p>
                  <p className="credit-toast__sub">
                    Il vous reste {t.remaining} crédit{(t.remaining || 0) > 1 ? "s" : ""} ce mois.
                    Pensez à activer l’usage à la demande ou à changer de plan.
                  </p>
                  <Link href="/settings#plan" className="credit-toast__link" onClick={() => dismiss(t.id)}>
                    Voir Plan & usage
                  </Link>
                </>
              ) : t.kind === "empty" ? (
                <>
                  <p className="credit-toast__title">Crédits épuisés</p>
                  <p className="credit-toast__sub">
                    Les actions IA sont en pause jusqu’au prochain mois, sauf usage à la demande
                    (admin cabinet).
                  </p>
                  <Link href="/settings" className="credit-toast__link" onClick={() => dismiss(t.id)}>
                    Ouvrir les paramètres
                  </Link>
                </>
              ) : t.kind === "daily" ? (
                <>
                  <p className="credit-toast__title">Il vous reste {t.dailyRemaining} crédits aujourd’hui</p>
                  <p className="credit-toast__sub">
                    Indicateur du jour (information). Au plafond, vous pourrez choisir de continuer
                    ou d’attendre demain.
                    {t.remaining != null ? ` Mois : ${t.remaining} restants.` : ""}
                  </p>
                  <Link href="/settings#plan" className="credit-toast__link" onClick={() => dismiss(t.id)}>
                    Voir Plan & usage
                  </Link>
                </>
              ) : (
                <>
                  <p className="credit-toast__title">Plafond du jour atteint</p>
                  <p className="credit-toast__sub">
                    Vous êtes informé. À la prochaine action IA, choisissez : attendre demain, ou
                    continuer (crédits du mois débités). Ce n’est pas un impayé.
                    {t.remaining != null ? ` Solde du mois : ${t.remaining}.` : ""}
                  </p>
                  <Link href="/settings#plan" className="credit-toast__link" onClick={() => dismiss(t.id)}>
                    Voir Plan & usage
                  </Link>
                </>
              )}
            </div>
            <button type="button" className="credit-toast__x" onClick={() => dismiss(t.id)} aria-label="Fermer">
              ×
            </button>
          </div>
        ))}
      </div>
    </>
  );
}
