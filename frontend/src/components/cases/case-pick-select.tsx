"use client";

import { useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { ChevronDown, FolderOpen, Plus } from "lucide-react";
import type { CaseListItem } from "@/lib/api";
import { caseHoverLines, caseSelectLabel } from "@/lib/case-display";
import { cn } from "@/lib/utils";

type Props = {
  cases: CaseListItem[];
  value: string;
  onChange: (caseId: string) => void;
  onCreateNew: () => void;
  uiFr?: boolean;
  className?: string;
};

type MenuBox = { top: number; left: number; width: number; maxHeight: number };

export function CasePickSelect({
  cases,
  value,
  onChange,
  onCreateNew,
  uiFr = true,
  className,
}: Props) {
  const [open, setOpen] = useState(false);
  const [hoverId, setHoverId] = useState<string | null>(null);
  const [box, setBox] = useState<MenuBox | null>(null);
  const [mounted, setMounted] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const btnRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const listId = useId();

  const selected = cases.find((c) => c.id === value) || null;
  const hoverCase = cases.find((c) => c.id === hoverId) || null;
  const hoverInfo = hoverCase
    ? caseHoverLines(hoverCase, uiFr ? "fr" : "ar")
    : null;

  useEffect(() => {
    setMounted(true);
  }, []);

  useLayoutEffect(() => {
    if (!open || !btnRef.current) {
      setBox(null);
      return;
    }
    function place() {
      const r = btnRef.current?.getBoundingClientRect();
      if (!r) return;
      const gap = 6;
      const spaceBelow = window.innerHeight - r.bottom - gap - 12;
      const spaceAbove = r.top - gap - 12;
      const preferBelow = spaceBelow >= 180 || spaceBelow >= spaceAbove;
      const maxHeight = Math.max(160, Math.min(320, preferBelow ? spaceBelow : spaceAbove));
      setBox({
        top: preferBelow ? r.bottom + gap : Math.max(8, r.top - gap - maxHeight),
        left: r.left,
        width: r.width,
        maxHeight,
      });
    }
    place();
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    return () => {
      window.removeEventListener("resize", place);
      window.removeEventListener("scroll", place, true);
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      const t = e.target as Node;
      if (rootRef.current?.contains(t)) return;
      if (menuRef.current?.contains(t)) return;
      setOpen(false);
      setHoverId(null);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setOpen(false);
        setHoverId(null);
      }
    }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const menu =
    open && mounted && box
      ? createPortal(
          <div
            ref={menuRef}
            id={listId}
            role="listbox"
            className="fixed z-[9999] overflow-hidden rounded-xl border border-[var(--line)] bg-white shadow-2xl"
            style={{
              top: box.top,
              left: box.left,
              width: box.width,
              maxHeight: box.maxHeight,
              direction: uiFr ? "ltr" : "rtl",
            }}
          >
            <div className="overflow-y-auto" style={{ maxHeight: hoverInfo ? box.maxHeight - 96 : box.maxHeight - 40 }}>
              <button
                type="button"
                role="option"
                className="flex w-full items-center gap-2 border-b border-slate-100 px-3 py-2.5 text-left text-sm font-semibold text-[#0B1A4D] hover:bg-amber-50"
                onClick={() => {
                  setOpen(false);
                  setHoverId(null);
                  onCreateNew();
                }}
              >
                <Plus className="h-4 w-4" />
                {uiFr ? "Créer un nouveau dossier…" : "إنشاء ملف جديد…"}
              </button>

              {cases.map((c) => {
                const active = c.id === value;
                return (
                  <button
                    key={c.id}
                    type="button"
                    role="option"
                    aria-selected={active}
                    className={cn(
                      "relative w-full border-b border-slate-50 px-3 py-2.5 text-left text-sm text-[#0B1A4D] last:border-0 hover:bg-sky-50",
                      active && "bg-sky-50/80 font-semibold",
                      hoverId === c.id && "bg-sky-50",
                    )}
                    onMouseEnter={() => setHoverId(c.id)}
                    onMouseLeave={() => setHoverId((id) => (id === c.id ? null : id))}
                    onFocus={() => setHoverId(c.id)}
                    onClick={() => {
                      onChange(c.id);
                      setOpen(false);
                      setHoverId(null);
                    }}
                  >
                    <div className="truncate font-medium">{caseSelectLabel(c)}</div>
                    {(c.title || "").trim() &&
                    (c.client_name || "").trim() &&
                    c.title !== c.client_name ? (
                      <div className="mt-0.5 truncate text-xs text-slate-500">{c.client_name}</div>
                    ) : null}
                  </button>
                );
              })}

              {cases.length === 0 ? (
                <p className="px-3 py-3 text-xs text-slate-500">
                  {uiFr ? "Aucun dossier pour l’instant." : "لا ملفات حالياً."}
                </p>
              ) : null}
            </div>

            {hoverInfo ? (
              <div
                className="border-t border-amber-200/80 bg-gradient-to-br from-amber-50 to-sky-50 px-3 py-2.5 text-sm"
                role="tooltip"
              >
                <p className="mb-1 text-xs font-bold uppercase tracking-wide text-slate-500">
                  {uiFr ? "Aperçu du dossier" : "معاينة الملف"}
                </p>
                <p className="font-semibold text-[#0B1A4D]">{hoverInfo.heading}</p>
                <ul className="mt-1 space-y-0.5 text-xs leading-relaxed text-slate-600">
                  {hoverInfo.lines.map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="border-t border-slate-100 px-3 py-2 text-[11px] text-slate-400">
                {uiFr
                  ? "Survolez un dossier pour voir ses infos."
                  : "مرّروا على ملف لرؤية معلوماته."}
              </p>
            )}
          </div>,
          document.body,
        )
      : null;

  return (
    <div ref={rootRef} className={cn("relative mb-2", className)}>
      <button
        ref={btnRef}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-2 rounded-xl border border-[var(--line)] bg-[var(--parchment)] px-3 py-[11px] text-left text-sm text-[var(--ink)]"
        style={{ direction: uiFr ? "ltr" : "rtl" }}
      >
        <span className="flex min-w-0 items-center gap-2">
          <FolderOpen className="h-4 w-4 shrink-0 opacity-70" />
          <span className="truncate font-medium">
            {selected
              ? caseSelectLabel(selected)
              : uiFr
                ? "— Choisissez un dossier (obligatoire) —"
                : "— اختاروا ملفاً (إلزامي) —"}
          </span>
        </span>
        <ChevronDown className={cn("h-4 w-4 shrink-0 opacity-60 transition", open && "rotate-180")} />
      </button>
      {menu}
    </div>
  );
}
