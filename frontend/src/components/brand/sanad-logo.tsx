"use client";

import Image from "next/image";
import { cn } from "@/lib/utils";
import { useLocaleStore } from "@/store/locale";

interface SanadLogoProps {
  size?: "sm" | "md" | "lg" | "xl" | "hero";
  className?: string;
  /** Soft gold aura around the logo (palette sanad-gold #D2B589). */
  glow?: boolean;
  /** Affiche le nom سند / Sanad à côté du monogramme. */
  withWordmark?: boolean;
  dark?: boolean;
}

const sizeClasses = {
  sm: "h-8 w-8",
  md: "h-10 w-10",
  lg: "h-14 w-14",
  xl: "h-20 w-20",
  hero: "h-24 w-24 sm:h-28 sm:w-28",
};

const sizeDims = {
  sm: { w: 64, h: 64 },
  md: { w: 80, h: 80 },
  lg: { w: 112, h: 112 },
  xl: { w: 160, h: 160 },
  hero: { w: 224, h: 224 },
};

const wordmarkSize = {
  sm: "text-lg",
  md: "text-xl",
  lg: "text-2xl",
  xl: "text-3xl",
  hero: "text-4xl",
};

/** Garde le logo actuel + wordmark سند (arabe d’abord). */
export function SanadLogo({
  size = "md",
  className,
  glow = true,
  withWordmark = true,
  dark = false,
}: SanadLogoProps) {
  const locale = useLocaleStore((s) => s.locale);
  const dim = sizeDims[size];
  const label = locale === "ar" ? "سند" : "Sanad";

  return (
    <span
      className={cn(
        "relative inline-flex items-center gap-2.5",
        glow && "sanad-logo-glow",
        className,
      )}
    >
      <Image
        src="/logo-sanad.png"
        alt={label}
        width={dim.w}
        height={dim.h}
        className={cn("relative z-[1] object-contain", sizeClasses[size])}
        priority={size === "hero"}
      />
      {withWordmark && (
        <span
          className={cn(
            "font-display font-semibold tracking-tight",
            wordmarkSize[size],
            dark ? "text-white" : "text-sanad-navy",
            locale === "ar" && "font-arabic",
          )}
        >
          {label}
        </span>
      )}
    </span>
  );
}

/** @deprecated Use <SanadLogo /> */
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
