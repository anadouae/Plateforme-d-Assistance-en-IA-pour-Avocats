"use client";

import Image from "next/image";
import { cn } from "@/lib/utils";

type Variant = "hero" | "dock" | "voice";

const SIZES: Record<Variant, number> = {
  hero: 148,
  voice: 132,
  dock: 40,
};

/** Logo LexHub animé — rotation 3D + halo doré (sidebar, accueil, dictée). */
export function SanadLogoAnimated({
  variant = "hero",
  listening = false,
  className,
}: {
  variant?: Variant;
  listening?: boolean;
  className?: string;
}) {
  const size = SIZES[variant];

  return (
    <div
      className={cn(
        "sanad-logo-animated",
        `sanad-logo-animated--${variant}`,
        listening && "sanad-logo-animated--listening",
        className,
      )}
      aria-hidden={variant !== "dock"}
    >
      <span className="sanad-logo-animated__orbit" />
      <span className="sanad-logo-animated__glow" />
      <div className="sanad-logo-animated__cube">
        <Image
          src="/logo-lexhub-cube.png?v=cube-2"
          alt=""
          width={size}
          height={size}
          className="sanad-logo-animated__img"
          unoptimized
          priority={variant === "dock"}
        />
      </div>
    </div>
  );
}
