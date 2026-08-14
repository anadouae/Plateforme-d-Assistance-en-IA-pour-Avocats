"use client";

import { useEffect } from "react";
import { cn } from "@/lib/utils";

export function Toast({
  open,
  message,
  onClose,
  durationMs = 2800,
}: {
  open: boolean;
  message: string;
  onClose: () => void;
  durationMs?: number;
}) {
  useEffect(() => {
    if (!open) return;
    const t = window.setTimeout(onClose, durationMs);
    return () => window.clearTimeout(t);
  }, [open, durationMs, onClose]);

  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "pointer-events-none fixed bottom-7 left-1/2 z-[60] flex -translate-x-1/2 items-center gap-2.5 rounded-[14px] bg-sanad-ink px-[22px] py-3.5 text-[13.5px] font-semibold text-white shadow-luxe transition-all duration-[400ms] ease-[cubic-bezier(0.2,0.9,0.25,1)]",
        open
          ? "translate-y-0 opacity-100"
          : "pointer-events-none translate-y-5 opacity-0",
      )}
    >
      <span className="h-2 w-2 shrink-0 rounded-full bg-sanad-goldSoft" aria-hidden />
      {message}
    </div>
  );
}
