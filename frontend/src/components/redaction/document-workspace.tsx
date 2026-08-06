"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Download,
  ExternalLink,
  FileText,
  FolderOpen,
  Loader2,
  Pin,
  Printer,
  Save,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { CaseListItem } from "@/lib/api";

type Props = {
  title: string;
  body: string;
  onTitleChange: (v: string) => void;
  onBodyChange: (v: string) => void;
  cases: CaseListItem[];
  caseId: string;
  onCaseIdChange: (v: string) => void;
  onExportPdf: () => void;
  onExportDocLegacy: () => void;
  onExportWord: () => void | Promise<void>;
  onOpenGoogleDocs: () => void;
  onSaveTemplate: () => void | Promise<void>;
  onSaveToCase: () => void | Promise<void>;
  savingCase?: boolean;
  exportingWord?: boolean;
  savingTemplate?: boolean;
};

/**
 * Panneau document : survol → agrandissement fluide, épingle pour fixer, X pour réduire.
 * Édition type Word dans l'app (textarea RTL élargi).
 */
export function DocumentWorkspace({
  title,
  body,
  onTitleChange,
  onBodyChange,
  cases,
  caseId,
  onCaseIdChange,
  onExportPdf,
  onExportDocLegacy,
  onExportWord,
  onOpenGoogleDocs,
  onSaveTemplate,
  onSaveToCase,
  savingCase,
  exportingWord,
  savingTemplate,
}: Props) {
  const [hovered, setHovered] = useState(false);
  const [pinned, setPinned] = useState(false);
  const expanded = pinned || hovered;

  useEffect(() => {
    if (!pinned) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setPinned(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [pinned]);

  return (
    <>
      <AnimatePresence>
        {pinned && (
          <motion.div
            key="backdrop"
            className="fixed inset-0 z-40 bg-sanad-navy/25 backdrop-blur-[2px]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setPinned(false)}
          />
        )}
      </AnimatePresence>

      <motion.div
        layout
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => {
          if (!pinned) setHovered(false);
        }}
        className={cn(
          "overflow-hidden rounded-2xl border border-[#1a3a2a]/25 bg-white shadow-luxe",
          pinned && "fixed inset-4 z-50 m-auto flex max-h-[min(920px,92vh)] max-w-5xl flex-col md:inset-8",
          !pinned && expanded && "relative z-30 scale-[1.02] shadow-2xl ring-1 ring-sanad-gold/30",
        )}
        transition={{ type: "spring", stiffness: 280, damping: 28 }}
        style={{ transformOrigin: "top center" }}
      >
        <div className="space-y-3 bg-gradient-to-l from-sanad-cream to-white px-4 py-3 sm:px-5">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-base font-semibold text-sanad-navy">
                4. Document réalisé — modifier · exporter
              </p>
              <p className="text-[11px] text-slate-500">
                Survolez pour agrandir · épinglez pour fixer · ✕ pour réduire
              </p>
            </div>
            <div className="flex shrink-0 items-center gap-1">
              <Button
                type="button"
                size="sm"
                variant={pinned ? "default" : "ghost"}
                className="h-8 w-8 p-0"
                title={pinned ? "Détacher" : "Épingler (agrandi)"}
                onClick={() => setPinned((v) => !v)}
              >
                <Pin className={cn("h-4 w-4", pinned && "fill-current")} />
              </Button>
              {(pinned || hovered) && (
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className="h-8 w-8 p-0"
                  title="Réduire"
                  onClick={() => {
                    setPinned(false);
                    setHovered(false);
                  }}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>

          <input
            className="w-full rounded-lg border border-sanad-border px-3 py-2 text-sm"
            value={title}
            onChange={(e) => onTitleChange(e.target.value)}
            placeholder="Titre de la plaidoirie"
            dir="rtl"
          />

          <div className="flex flex-wrap gap-2">
            <Button size="sm" onClick={onExportPdf}>
              <Printer className="h-4 w-4" />
              PDF
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={exportingWord}
              onClick={() => void onExportWord()}
            >
              {exportingWord ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <FileText className="h-4 w-4" />
              )}
              Word (.docx)
            </Button>
            <Button size="sm" variant="outline" onClick={onExportDocLegacy}>
              <Download className="h-4 w-4" />
              DOC
            </Button>
            <Button size="sm" variant="ghost" onClick={onOpenGoogleDocs}>
              <ExternalLink className="h-4 w-4" />
              Google Docs
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={savingTemplate}
              onClick={() => void onSaveTemplate()}
            >
              {savingTemplate ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Sauver modèle cabinet
            </Button>
          </div>

          <div className="flex flex-wrap items-end gap-2 rounded-xl border border-sanad-border bg-white p-3">
            <div className="min-w-[200px] flex-1">
              <label className="mb-1 flex items-center gap-1 text-xs font-medium text-slate-500">
                <FolderOpen className="h-3.5 w-3.5" />
                Classer dans un dossier
              </label>
              <select
                className="w-full rounded-lg border border-sanad-border px-2 py-2 text-sm"
                value={caseId}
                onChange={(e) => onCaseIdChange(e.target.value)}
              >
                <option value="">— Choisir un dossier —</option>
                {cases.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.reference} — {c.client_name}
                  </option>
                ))}
              </select>
            </div>
            <Button
              size="sm"
              variant="gold"
              disabled={savingCase}
              onClick={() => void onSaveToCase()}
            >
              {savingCase ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Enregistrer
            </Button>
          </div>
        </div>

        <div className={cn("p-4 sm:p-5", pinned && "min-h-0 flex-1 overflow-auto")}>
          <textarea
            dir="rtl"
            lang="ar"
            className={cn(
              "w-full rounded-xl border border-[#1a3a2a]/20 bg-white px-4 py-4 text-right text-sm leading-8 outline-none transition-all focus:ring-2 focus:ring-sanad-gold/40",
              expanded ? "min-h-[420px]" : "min-h-[280px]",
              pinned && "min-h-[min(560px,55vh)]",
            )}
            value={body}
            onChange={(e) => onBodyChange(e.target.value)}
            placeholder="نص المرافعة — عدّل كما في Word…"
          />
        </div>
      </motion.div>
    </>
  );
}
