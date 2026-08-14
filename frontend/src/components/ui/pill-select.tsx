"use client";

import { cn } from "@/lib/utils";

export type PillOption = { value: string; label: string };

export function PillSelect({
  options,
  value,
  onChange,
  error,
  ariaLabel,
}: {
  options: PillOption[];
  value: string;
  onChange: (value: string) => void;
  error?: string;
  ariaLabel?: string;
}) {
  return (
    <div className="space-y-1.5">
      <div
        role="radiogroup"
        aria-label={ariaLabel}
        className="flex flex-wrap gap-2"
      >
        {options.map((opt) => {
          const selected = value === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => onChange(opt.value)}
              className={cn(
                "rounded-full border px-3.5 py-2 text-[12.5px] font-semibold transition-all duration-250",
                selected
                  ? "border-sanad-ink bg-sanad-ink text-white"
                  : "border-[var(--line)] bg-white text-sanad-inkSoft hover:border-sanad-goldSoft hover:text-sanad-ink",
              )}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
