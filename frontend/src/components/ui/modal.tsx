"use client";

import { useEffect, useId, useRef } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export function Modal({
  open,
  onClose,
  title,
  subtitle,
  icon,
  children,
  footer,
  className,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}) {
  const titleId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  const previouslyFocused = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) return;
    previouslyFocused.current = document.activeElement as HTMLElement | null;
    const panel = panelRef.current;
    const focusables = () =>
      panel?.querySelectorAll<HTMLElement>(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
      ) || [];

    const firstInput =
      panel?.querySelector<HTMLElement>("input:not([disabled]), textarea:not([disabled])") ||
      focusables()[0];
    firstInput?.focus();

    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
        return;
      }
      if (e.key !== "Tab" || !panel) return;
      const list = Array.from(focusables());
      if (!list.length) return;
      const first = list[0];
      const last = list[list.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
      previouslyFocused.current?.focus?.();
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center bg-[rgba(14,21,38,0.42)] p-5 backdrop-blur-[6px] animate-[fade-in_0.35s_cubic-bezier(0.2,0.9,0.25,1)]"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className={cn(
          "max-h-[88vh] w-full max-w-[560px] overflow-y-auto rounded-sanad-lg border border-[var(--line)] bg-white/92 p-[30px] shadow-luxe backdrop-blur-[20px] animate-[modal-rise_0.45s_cubic-bezier(0.2,0.9,0.25,1)]",
          className,
        )}
      >
        <div className="mb-1.5 flex items-start justify-between gap-3">
          <div>
            {icon && (
              <div className="mb-3.5 flex h-11 w-11 items-center justify-center rounded-[14px] bg-sanad-gold text-white shadow-sanad-sm">
                {icon}
              </div>
            )}
            <h2
              id={titleId}
              className="font-display text-[23px] font-medium text-sanad-ink"
            >
              {title}
            </h2>
            {subtitle && (
              <p className="mt-1 text-[13px] text-sanad-inkSoft">{subtitle}</p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[10px] border border-[var(--line)] bg-white text-sanad-inkSoft transition hover:rotate-90 hover:border-sanad-gold hover:text-sanad-ink"
            aria-label="Fermer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="mt-5">{children}</div>
        {footer && (
          <div className="mt-5 flex justify-end gap-2.5 border-t border-[var(--line)] pt-[18px]">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
