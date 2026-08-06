"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

const N = 42;

/** Forme d’onde dorée (signature v3) — respire puis se pose en lignes. */
export function LandingWaveform({ className }: { className?: string }) {
  const [heights, setHeights] = useState<number[]>(() =>
    Array.from({ length: N }, () => 24),
  );
  const [asText, setAsText] = useState(false);

  useEffect(() => {
    const wave = () => {
      setAsText(false);
      setHeights(
        Array.from({ length: N }, (_, i) => {
          const center = N / 2;
          const dist = Math.abs(i - center) / center;
          const base = 1 - dist * 0.7;
          return (18 + Math.random() * 64) * base + 8;
        }),
      );
    };
    wave();
    let phase = 0;
    const id = window.setInterval(() => {
      phase = (phase + 1) % 4;
      if (phase === 2) setAsText(true);
      else wave();
    }, 1400);
    return () => window.clearInterval(id);
  }, []);

  return (
    <div
      className={cn(
        "mx-auto mt-12 flex h-[120px] max-w-[640px] items-center justify-center gap-1",
        className,
      )}
      aria-hidden
    >
      {heights.map((h, i) => (
        <div
          key={i}
          className="w-[5px] rounded-[3px] bg-gradient-to-b from-[#D9BA6A] to-[#B8912F] transition-all duration-[1400ms] ease-[cubic-bezier(0.65,0,0.35,1)]"
          style={{
            height: asText ? 2.5 : h,
            opacity: asText ? 0.85 : 1,
            borderRadius: asText ? 1 : 3,
          }}
        />
      ))}
    </div>
  );
}
