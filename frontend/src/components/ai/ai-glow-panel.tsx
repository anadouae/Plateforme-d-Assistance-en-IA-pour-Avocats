"use client";

import type { ReactNode } from "react";
import { MarkdownAnswer } from "@/components/ai/markdown-answer";
import type { Citation } from "@/lib/api";
import { cn } from "@/lib/utils";

/** Cadre sobre pour réponses IA (sans halo animé). */
export function AiGlowPanel({
  children,
  className,
  dir,
}: {
  children: ReactNode;
  className?: string;
  dir?: "ltr" | "rtl";
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-slate-200/90 bg-gradient-to-br from-white to-slate-50/90 p-4 shadow-sm",
        className,
      )}
      dir={dir}
    >
      {children}
    </div>
  );
}

export function AiLangSwitch({
  value,
  onChange,
  disabled,
}: {
  value: "fr" | "ar";
  onChange: (v: "fr" | "ar") => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex items-center rounded-lg border border-sanad-gold/25 bg-sanad-cream/80 p-0.5 text-xs font-semibold">
      {(
        [
          { code: "fr" as const, label: "FR" },
          { code: "ar" as const, label: "عربي" },
        ] as const
      ).map((l) => (
        <button
          key={l.code}
          type="button"
          disabled={disabled}
          onClick={() => onChange(l.code)}
          className={cn(
            "rounded-md px-2.5 py-1 transition-all disabled:opacity-50",
            value === l.code
              ? "bg-sanad-navy text-sanad-ivory shadow-sm"
              : "text-sanad-muted hover:text-sanad-navy",
          )}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}

export function AiMarkdownResult({
  text,
  sources,
  dir,
  className,
}: {
  text: string;
  sources?: Citation[];
  dir?: "ltr" | "rtl";
  className?: string;
}) {
  return (
    <AiGlowPanel dir={dir} className={className}>
      <MarkdownAnswer text={text} sources={sources || []} />
    </AiGlowPanel>
  );
}
