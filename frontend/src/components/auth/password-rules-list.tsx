"use client";

import { Check } from "lucide-react";
import { passwordRules } from "@/lib/password";
import { cn } from "@/lib/utils";

type Props = {
  password: string;
  labels: {
    length: string;
    upperLower: string;
    digit: string;
    symbol: string;
  };
  className?: string;
};

export function PasswordRulesList({ password, labels, className }: Props) {
  const rules = passwordRules(password);
  const items = [
    ["length", labels.length, rules.length],
    ["upperLower", labels.upperLower, rules.upperLower],
    ["digit", labels.digit, rules.digit],
    ["symbol", labels.symbol, rules.symbol],
  ] as const;

  return (
    <ul className={cn("grid gap-1 text-[11px] text-[#2C3B5C]", className)}>
      {items.map(([key, label, ok]) => (
        <li key={key} className="flex items-center gap-1.5">
          <Check className={cn("h-3.5 w-3.5 shrink-0", ok ? "text-emerald-600" : "text-slate-300")} />
          <span className={ok ? "text-emerald-800" : undefined}>{label}</span>
        </li>
      ))}
    </ul>
  );
}
