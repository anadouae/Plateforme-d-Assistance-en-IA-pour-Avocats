"use client";

import { useState } from "react";
import { Minus, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

export type LandingFaqItem = {
  q: string;
  a: string;
};

export function LandingFaqAccordion({
  title,
  eyebrow,
  items,
  ar,
}: {
  title: string;
  eyebrow: string;
  items: LandingFaqItem[];
  ar: boolean;
}) {
  const [open, setOpen] = useState<number | null>(0);
  const mid = Math.ceil(items.length / 2);
  const left = items.slice(0, mid);
  const right = items.slice(mid);

  function renderCol(col: LandingFaqItem[], offset: number) {
    return col.map((item, i) => {
      const idx = offset + i;
      const isOpen = open === idx;
      return (
        <button
          key={item.q}
          type="button"
          onClick={() => setOpen(isOpen ? null : idx)}
          className={cn(
            "w-full rounded-2xl border bg-white px-5 py-4 text-start shadow-[0_8px_24px_rgba(11,26,77,0.06)] transition",
            isOpen
              ? "border-[#1B3F9C]/35 ring-1 ring-[#1B3F9C]/15"
              : "border-[rgba(11,26,77,0.08)] hover:border-[rgba(27,63,156,0.25)]",
          )}
          aria-expanded={isOpen}
        >
          <span className="flex items-start justify-between gap-3">
            <span
              className={cn(
                "font-display text-[15px] font-semibold leading-snug sm:text-[16px]",
                isOpen ? "text-[#1B3F9C]" : "text-[#0B1A4D]",
              )}
            >
              {item.q}
            </span>
            <span
              className={cn(
                "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
                isOpen ? "bg-[#1B3F9C]/10 text-[#1B3F9C]" : "bg-[#F3F5FA] text-[#5A6A85]",
              )}
            >
              {isOpen ? <Minus className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
            </span>
          </span>
          {isOpen ? (
            <p className="mt-3 border-t border-[rgba(11,26,77,0.08)] pt-3 text-sm leading-relaxed text-[#3D4A66]">
              {item.a}
            </p>
          ) : null}
        </button>
      );
    });
  }

  return (
    <section id="faq" className="bg-[#F4F6FB] px-6 py-[96px] sm:px-8" dir={ar ? "rtl" : "ltr"}>
      <div className="mx-auto mb-12 max-w-[640px] text-center">
        <p className="font-mono text-[11.5px] uppercase tracking-[0.14em] text-[#1B3F9C]">
          {eyebrow}
        </p>
        <h2 className="font-display mt-3.5 text-[clamp(28px,4vw,40px)] font-semibold tracking-tight text-[#0B1A4D]">
          {title}
        </h2>
      </div>
      <div className="mx-auto grid max-w-[1080px] gap-4 md:grid-cols-2 md:gap-5">
        <div className="flex flex-col gap-4">{renderCol(left, 0)}</div>
        <div className="flex flex-col gap-4">{renderCol(right, mid)}</div>
      </div>
    </section>
  );
}
