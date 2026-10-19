"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/** Tooltip natif enrichi (title) — léger, pas de lib. */
export function Hint({
  tip,
  tipAr,
  ar,
  children,
  className,
}: {
  tip: string;
  tipAr?: string;
  ar?: boolean;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn("inline-flex cursor-help", className)}
      title={ar && tipAr ? tipAr : tip}
    >
      {children}
    </span>
  );
}
