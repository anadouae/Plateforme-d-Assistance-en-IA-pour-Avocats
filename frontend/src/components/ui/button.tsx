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
          "bg-sanad-navy text-sanad-ivory shadow-luxe hover:bg-sanad-navy/90 hover:shadow-gold hover:-translate-y-0.5",
        secondary: "bg-sanad-stone text-sanad-navy hover:bg-sanad-cream shadow-md",
        outline:
          "border border-sanad-gold/50 bg-sanad-ivory/80 text-sanad-navy backdrop-blur hover:bg-sanad-cream hover:shadow-md",
        ghost: "text-sanad-navy hover:bg-sanad-cream/80",
        gold:
          "bg-gradient-to-r from-sanad-gold to-[#c4a574] text-sanad-navy shadow-gold hover:shadow-lg hover:-translate-y-0.5",
        destructive: "bg-red-600 text-white hover:bg-red-700",
        ivory: "bg-sanad-ivory text-sanad-navy border border-sanad-stone hover:shadow-luxe",
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
