"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useClientLocale } from "@/store/locale";
import { LexProductModal } from "@/components/billing/lex-product-modal";

const SEEN_KEY = "lexhub_referral_nudge_at";
/** Réafficher au plus toutes les ~7 jours. */
const COOLDOWN_MS = 7 * 24 * 60 * 60 * 1000;

/** Popup périodique parrainage — soft, non bloquant au 1er écran. */
export function ReferralNudgeModal() {
  const ar = useClientLocale() === "ar";
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const [open, setOpen] = useState(false);
  const [code, setCode] = useState<string | null>(null);

  useEffect(() => {
    if (!user?.cabinet_id) return;
    if (user.role === "admin_webvoice" || user.role === "assistant_juridique") return;
    try {
      const raw = localStorage.getItem(SEEN_KEY);
      if (raw && Date.now() - Number(raw) < COOLDOWN_MS) return;
    } catch {
      /* ignore */
    }
    let cancelled = false;
    const delay = window.matchMedia("(max-width: 768px)").matches ? 90_000 : 60_000;
    const timer = window.setTimeout(() => {
      api
        .getReferral()
        .then((r) => {
          if (cancelled || !r.available || !r.code) return;
          setCode(r.code);
          setOpen(true);
        })
        .catch(() => undefined);
    }, delay);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [user]);

  function dismiss() {
    try {
      localStorage.setItem(SEEN_KEY, String(Date.now()));
    } catch {
      /* ignore */
    }
    setOpen(false);
  }

  return (
    <LexProductModal
      open={open && !!code}
      onClose={dismiss}
      tag={ar ? "إحالة" : "Parrainage"}
      title={
        ar
          ? "ادعوا مكتباً زميلاً — شهر إضافي لكم"
          : "Invitez un cabinet confrère — un mois offert"
      }
      points={
        ar
          ? [
              `رمزكم: ${code}`,
              "المدعو: +14 يوماً عند بدء Solo/Cabinet",
              "أنتم: +1 شهر عند بدء اشتراكه المدفوع",
            ]
          : [
              `Votre code : ${code}`,
              "Filleul : +14 jours d’essai Solo/Cabinet",
              "Vous : +1 mois à son abonnement payant",
            ]
      }
      primaryLabel={ar ? "رؤية رمزي" : "Voir mon code"}
      onPrimary={() => {
        try {
          if (code) void navigator.clipboard.writeText(code);
        } catch {
          /* ignore */
        }
        dismiss();
        router.push("/settings#parrainage");
        window.setTimeout(() => {
          document.getElementById("parrainage")?.scrollIntoView({
            behavior: "smooth",
            block: "center",
          });
        }, 700);
      }}
      secondaryLabel={ar ? "لاحقاً" : "Plus tard"}
      closeLabel={ar ? "إغلاق" : "Fermer"}
    />
  );
}
