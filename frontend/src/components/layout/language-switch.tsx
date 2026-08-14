"use client";

import { locales, type Locale } from "@/lib/i18n/translations";
import { useLocaleStore } from "@/store/locale";

export function LanguageSwitch({ variant = "light" }: { variant?: "light" | "dark" }) {
  const locale = useLocaleStore((s) => s.locale);
  const setLocale = useLocaleStore((s) => s.setLocale);

  if (variant === "dark") {
    return (
      <div className="switch" role="group" aria-label="Language" style={{ background: "rgba(255,255,255,0.12)" }}>
        {locales.map((l) => (
          <span
            key={l.code}
            role="button"
            tabIndex={0}
            className={locale === l.code ? "on" : undefined}
            onClick={() => setLocale(l.code as Locale)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") setLocale(l.code as Locale);
            }}
          >
            {l.label}
          </span>
        ))}
      </div>
    );
  }

  return (
    <div className="switch" role="group" aria-label="Language">
      {locales.map((l) => (
        <span
          key={l.code}
          role="button"
          tabIndex={0}
          className={locale === l.code ? "on" : undefined}
          onClick={() => setLocale(l.code as Locale)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") setLocale(l.code as Locale);
          }}
        >
          {l.label}
        </span>
      ))}
    </div>
  );
}
