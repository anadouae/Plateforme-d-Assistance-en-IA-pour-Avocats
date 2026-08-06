"use client";

import { locales, type Locale } from "@/lib/i18n/translations";
import { useLocaleStore } from "@/store/locale";
import { cn } from "@/lib/utils";

export function LanguageSwitch({ variant = "light" }: { variant?: "light" | "dark" }) {
  const locale = useLocaleStore((s) => s.locale);
  const setLocale = useLocaleStore((s) => s.setLocale);
  const isDark = variant === "dark";

  return (
    <div
      className={cn(
        "flex items-center rounded-lg border p-0.5 text-xs font-semibold",
        isDark
          ? "border-sanad-gold/30 bg-white/5 backdrop-blur"
          : "border-sanad-gold/20 bg-sanad-cream",
      )}
    >
      {locales.map((l) => (
        <button
          key={l.code}
          type="button"
          onClick={() => setLocale(l.code as Locale)}
          className={cn(
            "rounded-md px-2.5 py-1 transition-all duration-200",
            locale === l.code
              ? isDark
                ? "bg-sanad-gold text-sanad-navy shadow-sm"
                : "bg-sanad-navy text-sanad-ivory shadow-sm"
              : isDark
                ? "text-sanad-cream/70 hover:text-white"
                : "text-sanad-muted hover:text-sanad-navy",
          )}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}
