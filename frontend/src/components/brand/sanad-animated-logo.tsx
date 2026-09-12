"use client";

import Image from "next/image";
import { cn } from "@/lib/utils";

/** Logo LexHub animé — rotation 3D + halo doré (plaidoirie / accueil). */
export function SanadAnimatedLogo({
  active = false,
  className,
  size = 132,
}: {
  active?: boolean;
  className?: string;
  size?: number;
}) {
  return (
    <div
      className={cn("sanad-logo-hero", active && "sanad-logo-hero--active", className)}
      style={{ width: size, height: size }}
      aria-hidden
    >
      <div className="sanad-logo-hero__glow" />
      <div className="sanad-logo-hero__ring" />
      <div className="sanad-logo-hero__cube">
        <Image
          src="/logo-lexhub-cube.png?v=cube-2"
          alt=""
          width={size * 0.72}
          height={size * 0.72}
          className="sanad-logo-hero__img"
          unoptimized
          priority
        />
      </div>
    </div>
  );
}
