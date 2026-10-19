"use client";

import { useEffect, useState } from "react";
import { api, type BillingEntitlements } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useClientLocale } from "@/store/locale";
import { canManageTeam } from "@/lib/roles";
import { LexProductModal } from "@/components/billing/lex-product-modal";

const SEEN_KEY = "lexhub_plans_nudge_seen";

/** Popup connecté (admin) — plan Découverte → Solo / Cabinet. Soft : 1× / session, délai long. */
export function PlansNudgeModal() {
  const ar = useClientLocale() === "ar";
  const user = useAuthStore((s) => s.user);
  const [open, setOpen] = useState(false);
  const [ent, setEnt] = useState<BillingEntitlements | null>(null);

  useEffect(() => {
    if (!user || !canManageTeam(user.role)) return;
    try {
      if (sessionStorage.getItem(SEEN_KEY) === "1") return;
    } catch {
      /* ignore */
    }
    let cancelled = false;
    api
      .getBillingEntitlements()
      .then((e) => {
        if (cancelled) return;
        setEnt(e);
        const free = e.plan?.slug === "free" && e.status !== "trial";
        if (free) {
          // Desktop ~45s, mobile ~70s — après un vrai usage, pas au login
          const delay = window.matchMedia("(max-width: 768px)").matches ? 70_000 : 45_000;
          window.setTimeout(() => {
            if (!cancelled) setOpen(true);
          }, delay);
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [user]);

  function dismiss() {
    try {
      sessionStorage.setItem(SEEN_KEY, "1");
    } catch {
      /* ignore */
    }
    setOpen(false);
  }

  return (
    <LexProductModal
      open={open && !!ent}
      onClose={dismiss}
      tag={ar ? "مساحة المكتب" : "Votre espace"}
      title={ar ? "أنتم على الاكتشاف — حصص محدودة" : "Vous êtes sur Découverte — quotas limités"}
      points={
        ar
          ? [
              "ملف + إملاء + صياغة مع إخفاء الأسماء",
              "تصدير Word/PDF بترويسة المكتب",
              "تجربة Solo أو Cabinet — 0 درهم اليوم",
            ]
          : [
              "Dossier + dictée + rédaction (noms masqués)",
              "Export Word/PDF à l’en-tête du cabinet",
              "Essai Solo ou Cabinet — 0 MAD aujourd’hui",
            ]
      }
      primaryLabel={ar ? "اختيار خطة" : "Choisir un plan"}
      primaryHref="/tarifs"
      secondaryLabel={ar ? "لاحقاً" : "Plus tard"}
      closeLabel={ar ? "إغلاق" : "Fermer"}
    />
  );
}
