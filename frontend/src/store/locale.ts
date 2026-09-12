import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Locale } from "@/lib/i18n/translations";
import { getTranslations, normalizeAppLocale } from "@/lib/i18n/translations";

interface LocaleState {
  locale: Locale;
  _hasHydrated: boolean;
  setHasHydrated: (v: boolean) => void;
  setLocale: (locale: Locale) => void;
}

export function useTranslations() {
  // Même locale que le SSR tant que le persist n’a pas fini (évite mismatch).
  const locale = useClientLocale();
  return getTranslations(locale);
}

/** Locale stable au SSR + 1er paint (évite mismatch hydratation). */
export function useClientLocale(): Locale {
  const locale = useLocaleStore((s) => s.locale);
  const ready = useLocaleStore((s) => s._hasHydrated);
  return ready ? locale : "fr";
}

export const useLocaleStore = create<LocaleState>()(
  persist(
    (set) => ({
      // Français par défaut — arabe via le switch
      locale: "fr",
      _hasHydrated: false,
      setHasHydrated: (v) => set({ _hasHydrated: v }),
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
      name: "lexhub-locale-v1",
      // Empêche localStorage de changer la locale avant la fin de l’hydratation React
      skipHydration: true,
      partialize: (s) => ({ locale: s.locale }),
      merge: (persisted, current) => {
        const p = persisted as Partial<LocaleState> | undefined;
        const locale = normalizeAppLocale(p?.locale ?? current.locale);
        return { ...current, ...p, locale };
      },
      onRehydrateStorage: () => (state) => {
        if (!state) return;
        state.locale = normalizeAppLocale(state.locale);
        state.setHasHydrated(true);
        if (typeof document !== "undefined") {
          document.documentElement.lang = state.locale;
          document.documentElement.dir = state.locale === "ar" ? "rtl" : "ltr";
        }
      },
    },
  ),
);
