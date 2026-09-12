"use client";

import { useEffect } from "react";
import { useLocaleStore } from "@/store/locale";
import { ConfirmProvider } from "@/components/ui/confirm-dialog";

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const locale = useLocaleStore((s) => s.locale);
  const hydrated = useLocaleStore((s) => s._hasHydrated);

  useEffect(() => {
    void useLocaleStore.persist.rehydrate();
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    document.documentElement.lang = locale;
    document.documentElement.dir = locale === "ar" ? "rtl" : "ltr";
  }, [locale, hydrated]);

  return <ConfirmProvider>{children}</ConfirmProvider>;
}
