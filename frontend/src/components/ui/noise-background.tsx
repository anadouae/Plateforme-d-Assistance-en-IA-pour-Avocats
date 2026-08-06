"use client";

import { cn } from "@/lib/utils";

interface NoiseBackgroundProps {
  children: React.ReactNode;
  containerClassName?: string;
  className?: string;
  gradientColors?: string[];
}

export function NoiseBackground({
  children,
  containerClassName,
  className,
  gradientColors = [
    "rgb(210, 181, 137)",
    "rgb(11, 31, 74)",
    "rgb(232, 212, 176)",
  ],
}: NoiseBackgroundProps) {
  const gradient = `linear-gradient(120deg, ${gradientColors.join(", ")})`;

  return (
    <div className={cn("relative inline-flex", containerClassName)}>
      <div
        aria-hidden
        className={cn(
          "pointer-events-none absolute -inset-[2px] rounded-[inherit] opacity-80 blur-[6px]",
          className,
        )}
        style={{ backgroundImage: gradient }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 rounded-[inherit] opacity-[0.18] mix-blend-overlay"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")",
        }}
      />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
