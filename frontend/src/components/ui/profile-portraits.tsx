"use client";

import { useId } from "react";
import { cn } from "@/lib/utils";
import { useTranslations } from "@/store/locale";

/** Portraits SVG stylisés (cabinet) — pas d’assets externes. */
const PORTRAITS = [
  { id: "p1", bg: "#16233F", accent: "#E8C577", label: "A" },
  { id: "p2", bg: "#1E3A5F", accent: "#D4A84B", label: "M" },
  { id: "p3", bg: "#0F2744", accent: "#F0D78C", label: "S" },
  { id: "p4", bg: "#243B55", accent: "#C9A227", label: "Y" },
] as const;

function PortraitSvg({
  bg,
  accent,
  label,
  size,
  gradId,
}: {
  bg: string;
  accent: string;
  label: string;
  size: number;
  gradId: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={bg} />
          <stop offset="100%" stopColor="#0B1F4A" />
        </linearGradient>
      </defs>
      <circle cx="32" cy="32" r="32" fill={`url(#${gradId})`} />
      <circle cx="32" cy="24" r="10" fill={accent} opacity="0.92" />
      <path
        d="M12 58c4-14 14-20 20-20s16 6 20 20"
        fill={accent}
        opacity="0.85"
      />
      <text
        x="32"
        y="28"
        textAnchor="middle"
        fontSize="11"
        fontFamily="Georgia, serif"
        fontWeight="600"
        fill="#16233F"
      >
        {label}
      </text>
    </svg>
  );
}

interface ProfilePortraitsProps {
  className?: string;
  size?: number;
  /** Variante claire (fond blanc) ou sur fond sombre */
  variant?: "light" | "dark";
  showLabels?: boolean;
}

export function ProfilePortraits({
  className,
  size = 44,
  variant = "light",
  showLabels = true,
}: ProfilePortraitsProps) {
  const t = useTranslations().app.home;
  const uid = useId().replace(/:/g, "");
  const dark = variant === "dark";

  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-3 rounded-2xl border px-4 py-3",
        dark
          ? "border-white/15 bg-white/5 text-white"
          : "border-[#B08D3F]/25 bg-white/80 text-[#16233F] shadow-[0_12px_32px_-18px_rgba(22,35,63,0.25)] backdrop-blur-md",
        className,
      )}
    >
      <div className="flex items-center">
        {PORTRAITS.map((p, i) => (
          <div
            key={p.id}
            className="relative rounded-full ring-2 ring-white shadow-md"
            style={{ marginInlineStart: i === 0 ? 0 : -10, zIndex: PORTRAITS.length - i }}
            title={p.label}
          >
            <PortraitSvg
              bg={p.bg}
              accent={p.accent}
              label={p.label}
              size={size}
              gradId={`${uid}-${p.id}`}
            />
          </div>
        ))}
      </div>
      {showLabels && (
        <div className="min-w-0">
          <p className={cn("text-sm font-semibold", dark ? "text-white" : "text-[#16233F]")}>
            {t.teamStrip}
          </p>
          <p className={cn("text-xs", dark ? "text-white/60" : "text-[#2C3B5C]/70")}>
            {t.teamStripHint}
          </p>
        </div>
      )}
    </div>
  );
}
