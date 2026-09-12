import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, label, hint, error, id, ...props }, ref) => {
    const inputId = id || props.name;
    return (
      <div className="space-y-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium text-[#0B1A4D]"
          >
            {label}
          </label>
        )}
        <input
          type={type}
          id={inputId}
          className={cn(
            "flex h-10 w-full rounded-lg border border-sanad-border bg-white px-3 py-2 text-sm text-[#0B1A4D] caret-[#0B1A4D] placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sanad-blue focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50",
            error && "border-red-500 focus-visible:ring-red-500",
            className,
          )}
          ref={ref}
          {...props}
        />
        {hint && !error ? (
          <p className="text-[11px] leading-relaxed text-slate-500">{hint}</p>
        ) : null}
        {error && <p className="text-xs text-red-600">{error}</p>}
      </div>
    );
  },
);
Input.displayName = "Input";

export { Input };
