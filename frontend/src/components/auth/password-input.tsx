"use client";

import * as React from "react";
import { Eye, EyeOff } from "lucide-react";
import { cn } from "@/lib/utils";

export interface PasswordInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
  error?: string;
}

export const PasswordInput = React.forwardRef<HTMLInputElement, PasswordInputProps>(
  ({ className, label, error, id, name, ...props }, ref) => {
    const [visible, setVisible] = React.useState(false);
    const inputId = id || name;

    return (
      <div className="space-y-1.5">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-[#0B1A4D]">
            {label}
          </label>
        )}
        <div className="relative">
          <input
            ref={ref}
            id={inputId}
            name={name}
            type={visible ? "text" : "password"}
            className={cn(
              "flex h-11 w-full rounded-xl border border-sanad-border bg-white px-3 py-2 pe-11 text-sm text-[#0B1A4D] caret-[#0B1A4D] placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sanad-navy/30 focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50",
              error && "border-red-500 focus-visible:ring-red-500",
              className,
            )}
            {...props}
          />
          <button
            type="button"
            tabIndex={-1}
            onClick={() => setVisible((v) => !v)}
            className="absolute end-2 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-[#0B1A4D]/70 transition hover:bg-sanad-navy/5 hover:text-sanad-navy"
            aria-label={visible ? "Masquer le mot de passe" : "Afficher le mot de passe"}
          >
            {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        {error && <p className="text-xs text-red-600">{error}</p>}
      </div>
    );
  },
);
PasswordInput.displayName = "PasswordInput";
