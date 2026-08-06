"use client";

import { useId, useState } from "react";
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";

interface GooeyInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange"> {
  value?: string;
  onValueChange?: (value: string) => void;
  containerClassName?: string;
}

export function GooeyInput({
  className,
  containerClassName,
  placeholder = "بحث…",
  value,
  onValueChange,
  ...props
}: GooeyInputProps) {
  const id = useId();
  const [focused, setFocused] = useState(false);

  return (
    <div className={cn("relative w-full", containerClassName)}>
      <svg className="absolute h-0 w-0" aria-hidden>
        <defs>
          <filter id={`gooey-${id}`}>
            <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur" />
            <feColorMatrix
              in="blur"
              mode="matrix"
              values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -8"
              result="gooey"
            />
            <feBlend in="SourceGraphic" in2="gooey" />
          </filter>
        </defs>
      </svg>

      <div
        className={cn(
          "relative flex items-center rounded-2xl border bg-white/90 shadow-sm transition-all duration-300",
          focused
            ? "border-sanad-gold shadow-gold ring-2 ring-sanad-gold/25"
            : "border-sanad-border",
        )}
        style={{ filter: focused ? `url(#gooey-${id})` : undefined }}
      >
        <Search className="pointer-events-none absolute start-3 h-4 w-4 text-sanad-muted" />
        <input
          value={value}
          onChange={(e) => onValueChange?.(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={placeholder}
          className={cn(
            "h-11 w-full rounded-2xl bg-transparent pe-4 ps-10 text-sm text-sanad-navy outline-none placeholder:text-sanad-muted",
            className,
          )}
          {...props}
        />
      </div>
    </div>
  );
}
