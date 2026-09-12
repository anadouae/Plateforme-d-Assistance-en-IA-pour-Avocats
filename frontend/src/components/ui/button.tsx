"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { NoiseBackground } from "@/components/ui/noise-background";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sanad-gold focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.97]",
  {
    variants: {
      variant: {
        default:
          "bg-gradient-to-br from-[var(--royal-700)] to-[var(--royal-900)] text-white shadow-[0_10px_28px_rgba(11,26,77,0.28),0_0_22px_rgba(76,124,255,0.28)] hover:-translate-y-0.5 hover:shadow-[0_14px_34px_rgba(11,26,77,0.35),0_0_32px_rgba(76,124,255,0.4)]",
        secondary: "bg-white text-sanad-ink border border-[var(--line)] hover:border-[var(--royal-glow)] shadow-sm",
        outline:
          "border border-[rgba(76,124,255,0.28)] bg-white/80 text-[var(--royal-800)] backdrop-blur hover:border-[var(--royal-glow)] hover:bg-[rgba(76,124,255,0.06)] hover:shadow-sanad-sm",
        ghost: "text-sanad-inkSoft hover:bg-[rgba(76,124,255,0.08)] hover:text-sanad-ink",
        gold:
          "bg-gradient-to-br from-[var(--royal-glow)] via-[var(--royal-700)] to-[var(--royal-900)] text-white shadow-[0_0_28px_rgba(76,124,255,0.35)] hover:shadow-[0_0_40px_rgba(76,124,255,0.5)] hover:-translate-y-0.5",
        destructive: "bg-red-600 text-white hover:bg-red-700",
        ivory: "bg-white text-sanad-ink border border-[var(--line)] hover:shadow-sanad-sm",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-lg px-3",
        lg: "h-12 rounded-xl px-8 text-base",
        icon: "h-10 w-10",
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
