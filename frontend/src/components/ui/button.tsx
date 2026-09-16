"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { NoiseBackground } from "@/components/ui/noise-background";

const buttonVariants = cva(
  "inline-flex max-w-full items-center justify-center gap-2 rounded-xl text-sm font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sanad-gold focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98] sm:whitespace-nowrap",
  {
    variants: {
      variant: {
        default:
          "bg-gradient-to-br from-[var(--royal-700)] to-[var(--royal-900)] text-white shadow-[0_8px_20px_rgba(11,26,77,0.22)] hover:opacity-95",
        secondary: "bg-white text-sanad-ink border border-[var(--line)] hover:border-[var(--royal-glow)] shadow-sm",
        outline:
          "border border-[rgba(76,124,255,0.28)] bg-white text-[var(--royal-800)] hover:border-[var(--royal-glow)] hover:bg-[rgba(76,124,255,0.06)]",
        ghost: "text-sanad-inkSoft hover:bg-[rgba(76,124,255,0.08)] hover:text-sanad-ink",
        gold:
          "bg-gradient-to-br from-[var(--royal-glow)] via-[var(--royal-700)] to-[var(--royal-900)] text-white shadow-[0_0_20px_rgba(76,124,255,0.28)]",
        destructive: "bg-red-600 text-white hover:bg-red-700",
        ivory: "bg-white text-sanad-ink border border-[var(--line)]",
      },
      size: {
        default: "min-h-10 h-auto px-4 py-2.5",
        sm: "min-h-9 h-auto rounded-lg px-3 py-2",
        lg: "min-h-12 h-auto rounded-xl px-6 py-3 text-base",
        icon: "h-10 w-10 shrink-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /** Halo noise Aceternity autour du bouton (CTA importants) */
  noise?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, noise = false, ...props }, ref) => {
    const btn = (
      <button
        className={cn(buttonVariants({ variant, size, className }), noise && "rounded-full")}
        ref={ref}
        {...props}
      />
    );
    if (!noise) return btn;
    return (
      <NoiseBackground containerClassName="inline-flex rounded-full p-[2px]">
        {btn}
      </NoiseBackground>
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
