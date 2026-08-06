import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Locale } from "@/lib/i18n/translations";
import { getTranslations, normalizeAppLocale } from "@/lib/i18n/translations";

interface LocaleState {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}

export function useTranslations() {
  const locale = useLocaleStore((s) => s.locale);
  return getTranslations(locale);
}

export const useLocaleStore = create<LocaleState>()(
  persist(
    (set) => ({
      // Arabe par défaut — français via le switch (optionnel)
      locale: "ar",
      setLocale: (locale) => {
        const next = normalizeAppLocale(locale);
        set({ locale: next });
        if (typeof document !== "undefined") {
          document.documentElement.lang = next;
          document.documentElement.dir = next === "ar" ? "rtl" : "ltr";
        }
      },
    }),
    {
      name: "sanad-locale-v3",
      merge: (persisted, current) => {
        const p = persisted as Partial<LocaleState> | undefined;
        const locale = normalizeAppLocale(p?.locale ?? current.locale);
        return { ...current, ...p, locale };
      },
      onRehydrateStorage: () => (state) => {
        if (!state) return;
        state.locale = normalizeAppLocale(state.locale);
        if (typeof document !== "undefined") {
          document.documentElement.lang = state.locale;
          document.documentElement.dir = state.locale === "ar" ? "rtl" : "ltr";
        }
      },
    },
  ),
);
