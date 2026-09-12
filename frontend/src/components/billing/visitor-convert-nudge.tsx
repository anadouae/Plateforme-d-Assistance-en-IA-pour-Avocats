"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { useClientLocale } from "@/store/locale";
import { LexProductModal } from "@/components/billing/lex-product-modal";

const SEEN_KEY = "lexhub_visitor_nudge_seen";

/** Popup conversion visiteur — design LexHub produit. */
export function VisitorConvertNudge() {
  const ar = useClientLocale() === "ar";
  const user = useAuthStore((s) => s.user);
  const hydrated = useAuthStore((s) => s._hasHydrated);
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!hydrated || user) return;
    const publicPaths = ["/", "/home", "/tarifs", "/about", "/securite", "/fonctionnalites", "/aide"];
    const onPublic =
      publicPaths.includes(pathname || "") || (pathname || "").startsWith("/tarifs");
    if (!onPublic) return;
    try {
      if (sessionStorage.getItem(SEEN_KEY) === "1") return;
    } catch {
      /* ignore */
    }
    const t = window.setTimeout(() => setOpen(true), 18000);
    return () => window.clearTimeout(t);
  }, [hydrated, user, pathname]);

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
      open={open && !user}
      onClose={dismiss}
      tag={ar ? "للمكاتب" : "Pour votre cabinet"}
      title={
        ar
          ? "جرّبوا المرافعة من الملف — بدون بطاقة اليوم"
          : "Testez la plaidoirie depuis le dossier — 0 MAD aujourd’hui"
      }
      points={
        ar
          ? [
              "إملاء عربي من الملف، مع قطع اختيارية",
              "إخفاء أسماء الأطراف قبل الذكاء الاصطناعي",
              "تصدير Word وPDF بترويسة مكتبكم",
            ]
          : [
              "Dictée arabe depuis le dossier, pièces facultatives",
              "Noms des parties masqués avant l’IA",
              "Export Word et PDF à l’en-tête du cabinet",
            ]
      }
      primaryLabel={ar ? "إنشاء مكتبي" : "Créer mon cabinet"}
      primaryHref="/login?tab=register"
      secondaryLabel={ar ? "رؤية الأسعار" : "Voir les tarifs"}
      onSecondary={() => {
        dismiss();
        window.location.assign("/tarifs");
      }}
      closeLabel={ar ? "إغلاق" : "Fermer"}
    />
  );
}
