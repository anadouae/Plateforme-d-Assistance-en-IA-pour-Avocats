"use client";

import { useCallback, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { ArrowLeft, X } from "lucide-react";
import { getLegalDoc, type LegalDocId } from "@/lib/legal-content";
import { cn } from "@/lib/utils";

type Props = {
  doc: LegalDocId;
  label: string;
  locale: "fr" | "ar";
  previewHint: string;
  backLabel: string;
  onOpenChange?: (open: boolean) => void;
};

function LegalDocPanel({
  content,
  locale,
  backLabel,
  onClose,
}: {
  content: ReturnType<typeof getLegalDoc>;
  locale: "fr" | "ar";
  backLabel: string;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-[#0B1A4D]/55 p-4 backdrop-blur-[2px]"
      role="dialog"
      aria-modal="true"
      aria-label={content.title}
      onClick={onClose}
    >
      <div
        className="flex max-h-[min(88vh,720px)] w-full max-w-lg flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex shrink-0 items-center justify-between gap-3 border-b border-slate-100 bg-white px-4 py-3">
          <button
            type="button"
            className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-[#0B1A4D] hover:bg-slate-100"
            onClick={onClose}
          >
            <ArrowLeft className="h-4 w-4" />
            {backLabel}
          </button>
          <button
            type="button"
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-800"
            aria-label="Fermer"
            onClick={onClose}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div
          className="min-h-0 flex-1 overflow-y-auto px-5 py-4"
          dir={locale === "ar" ? "rtl" : "ltr"}
        >
          <h3 className="font-serif text-xl text-[#0B1A4D]">{content.title}</h3>
          <div className="mt-4 space-y-5 text-sm leading-relaxed text-slate-600">
            {content.sections.map((section) => (
              <section key={section.title}>
                <h4 className="font-semibold text-slate-800">{section.title}</h4>
                {section.paragraphs.map((p) => (
                  <p key={p.slice(0, 40)} className="mt-2">
                    {p}
                  </p>
                ))}
              </section>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function LegalDocLink({
  doc,
  label,
  locale,
  previewHint,
  backLabel,
  onOpenChange,
}: Props) {
  const content = getLegalDoc(doc, locale);
  const [hover, setHover] = useState(false);
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const close = useCallback(() => {
    setOpen(false);
    onOpenChange?.(false);
  }, [onOpenChange]);

  const show = useCallback(() => {
    setOpen(true);
    setHover(false);
    onOpenChange?.(true);
  }, [onOpenChange]);

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [open, close]);

  return (
    <>
      <span
        className="relative inline"
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
      >
        <button
          type="button"
          className="font-medium text-[#0B1A4D] underline-offset-2 hover:underline"
          onClick={show}
        >
          {label}
        </button>
        {hover && !open && (
          <span
            role="tooltip"
            className={cn(
              "absolute bottom-full z-30 mb-2 w-64 rounded-xl border border-slate-200 bg-white p-3 text-left text-xs leading-relaxed text-slate-600 shadow-lg",
              locale === "ar" ? "right-0" : "left-0",
            )}
          >
            {content.preview}
            <span className="mt-2 block font-medium text-[#0B1A4D]">{previewHint}</span>
          </span>
        )}
      </span>

      {open && mounted
        ? createPortal(
            <LegalDocPanel
              content={content}
              locale={locale}
              backLabel={backLabel}
              onClose={close}
            />,
            document.body,
          )
        : null}
    </>
  );
}
