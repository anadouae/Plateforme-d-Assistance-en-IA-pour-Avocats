"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Magnetic } from "@/components/motion/magnetic";
import { NoiseBackground } from "@/components/ui/noise-background";

type Props = {
  href: string;
  children: ReactNode;
  variant?: "gold" | "outline" | "ghost";
  className?: string;
  size?: "default" | "lg";
};

export function AnimatedButton({
  href,
  children,
  variant = "gold",
  className,
  size = "lg",
}: Props) {
  const base =
    "relative inline-flex items-center justify-center gap-2 overflow-hidden rounded-full font-serif font-semibold transition-colors";
  const sizes = size === "lg" ? "px-8 py-3.5 text-base" : "px-5 py-2.5 text-sm";
  const variants = {
    gold: "bg-gradient-to-r from-[#4C7CFF] via-[#1B3F9C] to-[#0B1A4D] text-white shadow-[0_0_28px_rgba(76,124,255,0.4)]",
    outline:
      "border border-[rgba(140,170,255,0.4)] bg-white/5 text-[#F4F6FC] backdrop-blur-md hover:bg-[rgba(76,124,255,0.15)]",
    ghost: "text-[#A8C0FF] hover:bg-[rgba(76,124,255,0.12)]",
  };

  const button = (
    <motion.span
      className={cn(base, sizes, variants[variant], className)}
      whileHover={{ scale: 1.04, y: -2 }}
      whileTap={{ scale: 0.97 }}
      transition={{ type: "spring", stiffness: 420, damping: 22 }}
    >
      {variant === "gold" && (
        <motion.span
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-gradient-to-r from-transparent via-white/35 to-transparent"
          initial={{ x: "-120%" }}
          whileHover={{ x: "120%" }}
          transition={{ duration: 0.7, ease: "easeInOut" }}
        />
      )}
      <span className="relative z-10">{children}</span>
    </motion.span>
  );

  return (
    <Magnetic strength={variant === "gold" ? 40 : 28}>
      <Link href={href} className="inline-block">
        {variant === "gold" ? (
          <NoiseBackground containerClassName="rounded-full p-[2px]">
            {button}
          </NoiseBackground>
        ) : (
          button
        )}
      </Link>
    </Magnetic>
  );
}
