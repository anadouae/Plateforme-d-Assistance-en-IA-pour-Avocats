"use client";

import { useEffect, useState } from "react";
import { locales, type Locale } from "@/lib/i18n/translations";
import { useClientLocale, useLocaleStore } from "@/store/locale";

/**
 * Client-only après mount : évite hydratation cassée par
 * locale persistée ou extensions (ex. MetaMask) qui injectent des nœuds.
 */
export function LanguageSwitch({ variant = "light" }: { variant?: "light" | "dark" }) {
  const locale = useClientLocale();
  const setLocale = useLocaleStore((s) => s.setLocale);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setReady(true);
  }, []);

  const shellStyle =
    variant === "dark"
      ? ({ background: "rgba(255,255,255,0.12)", minHeight: 36, minWidth: 96 } as const)
      : ({ minHeight: 36, minWidth: 96 } as const);

  if (!ready) {
    return (
      <div
        className="switch"
        role="presentation"
        aria-hidden
        style={shellStyle}
        suppressHydrationWarning
      />
    );
  }

  return (
    <div
      className="switch"
      role="group"
      aria-label="Language"
      style={variant === "dark" ? { background: "rgba(255,255,255,0.12)" } : undefined}
    >
      {locales.map((l) => (
        <button
          key={l.code}
          type="button"
          className={locale === l.code ? "on" : undefined}
          aria-pressed={locale === l.code}
          onClick={() => setLocale(l.code)}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}
