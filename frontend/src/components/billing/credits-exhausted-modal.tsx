"use client";

import Link from "next/link";
import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";

/** Écran dédié quand forfait essai / mois est épuisé — guide vers les bons choix. */
export function CreditsExhaustedModal({
  open,
  onClose,
  ar,
  message,
  actions,
  trial,
  trialEndsLabel,
  isAdmin = true,
  onEnableOnDemand,
  onBuyPack,
  onUpgrade,
}: {
  open: boolean;
  onClose: () => void;
  ar: boolean;
  message: string;
  actions: string[];
  trial?: boolean;
  trialEndsLabel?: string;
  isAdmin?: boolean;
  onEnableOnDemand?: () => void;
  onBuyPack?: () => void;
  onUpgrade?: () => void;
}) {
  if (trial) {
    return (
      <Modal
        open={open}
        onClose={onClose}
        title={ar ? "حصة التجربة منتهية" : "Forfait d’essai épuisé"}
      >
        <p className="text-sm leading-relaxed text-slate-600">
          {message ||
            (ar
              ? `انتهت حصة التجربة. يمكنكم العودة في ${trialEndsLabel || "—"} أو الاشتراك في خطة.`
              : `Votre forfait d’essai est terminé (crédits / quotas). Vous pouvez attendre la fin d’essai (${trialEndsLabel || "—"}) — sans achat de packs pendant l’essai — ou souscrire à un plan pour continuer tout de suite.`)}
        </p>
        <div className="mt-4 flex flex-col gap-2">
          {isAdmin ? (
            <Button type="button" onClick={() => onUpgrade?.()}>
              {ar ? "الاشتراك / رؤية التعريفات" : "Voir les tarifs / s’abonner"}
            </Button>
          ) : (
            <Link href="/settings#abonnement" className="block" onClick={onClose}>
              <Button type="button" className="w-full" variant="outline">
                {ar ? "طلب من مسؤول المكتب" : "Demander à l’admin cabinet"}
              </Button>
            </Link>
          )}
          <Button type="button" className="w-full" variant="outline" onClick={onClose}>
            {ar ? "حسناً" : "Compris"}
          </Button>
        </div>
      </Modal>
    );
  }

  const order = ["enable_on_demand", "buy_pack", "upgrade"].filter((a) => actions.includes(a));

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={ar ? "لا أرصدة متبقية هذا الشهر" : "Forfait du mois épuisé"}
    >
      <p className="text-sm leading-relaxed text-slate-600">
        {message ||
          (ar
            ? "انتهت أرصدة هذا الشهر. إليكم ما يمكنكم فعله."
            : "Vos crédits / quotas du mois sont terminés. Voici ce que vous pouvez faire :")}
      </p>
      <div className="mt-4 flex flex-col gap-2">
        {order.length === 0 ? (
          <Link href="/tarifs" className="block" onClick={onClose}>
            <Button type="button" className="w-full">
              {ar ? "الترقية إلى خطة أعلى" : "Passer à un plan supérieur"}
            </Button>
          </Link>
        ) : null}
        {order.map((a) => {
          if (a === "enable_on_demand") {
            return (
              <Button
                key={a}
                type="button"
                onClick={() => {
                  onEnableOnDemand?.();
                  onClose();
                }}
              >
                {ar
                  ? isAdmin
                    ? "1. تفعيل الاستخدام عند الطلب"
                    : "1. طلب تفعيل الاستخدام عند الطلب"
                  : isAdmin
                    ? "1. Activer l’usage à la demande"
                    : "1. Demander l’activation à l’admin"}
              </Button>
            );
          }
          if (a === "buy_pack") {
            return (
              <Button
                key={a}
                type="button"
                variant="outline"
                onClick={() => {
                  onBuyPack?.();
                  onClose();
                }}
              >
                {ar
                  ? isAdmin
                    ? "2. شراء حزمة أرصدة"
                    : "2. طلب شراء حزمة"
                  : isAdmin
                    ? "2. Acheter un pack de crédits"
                    : "2. Demander un pack à l’admin"}
              </Button>
            );
          }
          return (
            <Button
              key={a}
              type="button"
              variant="outline"
              onClick={() => {
                onUpgrade?.();
                onClose();
              }}
            >
              {ar ? "3. الترقية إلى خطة أعلى" : "3. Passer au plan supérieur"}
            </Button>
          );
        })}
        <Button type="button" className="w-full" variant="ghost" onClick={onClose}>
          {ar ? "إغلاق" : "Fermer"}
        </Button>
      </div>
    </Modal>
  );
}
