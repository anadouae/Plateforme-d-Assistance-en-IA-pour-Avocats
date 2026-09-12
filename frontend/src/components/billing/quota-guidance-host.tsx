"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { useClientLocale } from "@/store/locale";
import { canManageTeam } from "@/lib/roles";
import { api, setQuotaExhaustedHandler } from "@/lib/api";
import { CreditsExhaustedModal } from "@/components/billing/credits-exhausted-modal";
import { useBillingCredits } from "@/store/billing-credits";

type QuotaState = {
  open: boolean;
  message: string;
  actions: string[];
  trial: boolean;
  trialEndsLabel?: string;
};

const EMPTY: QuotaState = {
  open: false,
  message: "",
  actions: [],
  trial: false,
};

/** Écoute les 402 quota / crédits et ouvre le modal de guidance. */
export function QuotaGuidanceHost() {
  const user = useAuthStore((s) => s.user);
  const ar = useClientLocale() === "ar";
  const isAdmin = canManageTeam(user?.role);
  const router = useRouter();
  const refresh = useBillingCredits((s) => s.refresh);
  const [state, setState] = useState<QuotaState>(EMPTY);

  useEffect(() => {
    if (!user || user.role === "admin_webvoice") {
      setQuotaExhaustedHandler(null);
      return;
    }
    setQuotaExhaustedHandler(async (info) => {
      setState({
        open: true,
        message: info.message,
        actions: info.actions,
        trial: Boolean(info.trial),
        trialEndsLabel: info.trialEndsLabel || undefined,
      });
      void refresh();
    });
    return () => setQuotaExhaustedHandler(null);
  }, [user, refresh]);

  if (!user || user.role === "admin_webvoice") return null;

  return (
    <CreditsExhaustedModal
      open={state.open}
      onClose={() => setState(EMPTY)}
      ar={ar}
      message={state.message}
      actions={state.actions}
      trial={state.trial}
      trialEndsLabel={state.trialEndsLabel}
      isAdmin={isAdmin}
      onEnableOnDemand={() => {
        if (!isAdmin) {
          router.push("/settings#abonnement");
          return;
        }
        void api
          .updateOnDemandSettings(true, null)
          .then(() => refresh())
          .catch(() => router.push("/settings#abonnement"));
      }}
      onBuyPack={() => router.push("/settings#abonnement")}
      onUpgrade={() => router.push(isAdmin ? "/tarifs" : "/settings#abonnement")}
    />
  );
}
