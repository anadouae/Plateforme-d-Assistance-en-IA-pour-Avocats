"use client";

import Image from "next/image";
import { cn } from "@/lib/utils";
import { useClientLocale } from "@/store/locale";

interface SanadLogoProps {
  size?: "sm" | "md" | "lg" | "xl" | "hero" | "dock";
  className?: string;
  /** Soft gold aura around the logo. */
  glow?: boolean;
  /** Affiche le nom LexHub à côté du monogramme (identique en FR/AR). */
  withWordmark?: boolean;
  dark?: boolean;
}

const sizeClasses = {
  dock: "h-[52px] w-[52px]",
  sm: "h-8 w-8",
  md: "h-10 w-10",
  lg: "h-14 w-14",
  xl: "h-20 w-20",
  hero: "h-24 w-24 sm:h-28 sm:w-28",
};

const sizeDims = {
  dock: { w: 104, h: 104 },
  sm: { w: 64, h: 64 },
  md: { w: 80, h: 80 },
  lg: { w: 112, h: 112 },
  xl: { w: 160, h: 160 },
  hero: { w: 224, h: 224 },
};

const wordmarkSize = {
  dock: "text-lg",
  sm: "text-lg",
  md: "text-xl",
  lg: "text-2xl",
  xl: "text-3xl",
  hero: "text-4xl",
};

/** Cube or transparent — asset unique partout. */
const LOGO_SRC = "/logo-lexhub-cube.png?v=cube-2";

export function SanadLogo({
  size = "md",
  className,
  glow = false,
  withWordmark = true,
  dark = false,
}: SanadLogoProps) {
  const locale = useClientLocale();
  const dim = sizeDims[size];
  const label = "LexHub";

  return (
    <span
      className={cn(
        "relative inline-flex items-center gap-2.5 bg-transparent",
        glow && "sanad-logo-glow",
        className,
      )}
    >
      <Image
        src={LOGO_SRC}
        alt={label}
        width={dim.w}
        height={dim.h}
        className={cn(
          "relative z-[1] bg-transparent object-contain mix-blend-normal",
          sizeClasses[size],
        )}
        style={{ backgroundColor: "transparent" }}
        priority={size === "hero" || size === "lg" || size === "md" || size === "dock"}
        unoptimized
      />
      {withWordmark && (
        <span
          className={cn(
            "font-display font-semibold tracking-tight drop-shadow-sm",
            wordmarkSize[size],
            dark
              ? "text-[#FFE6C2] [text-shadow:0_1px_12px_rgba(0,0,0,0.65)]"
              : "text-[#0A1228]",
            locale === "ar" && "font-arabic",
          )}
        >
          {label}
        </span>
      )}
    </span>
  );
}

/** Alias LexHub — même composant (logo cube). */
export const LexHubLogo = SanadLogo;

/** @deprecated Use <LexHubLogo /> / <SanadLogo /> */
export function SanadLogoWithText({
  size = "md",
  className,
  dark,
}: {
  size?: "sm" | "md" | "lg" | "hero";
  subtitle?: string;
  dark?: boolean;
  className?: string;
}) {
  return <SanadLogo size={size} className={className} dark={dark} withWordmark />;
}
