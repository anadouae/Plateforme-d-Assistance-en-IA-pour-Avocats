"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import {
  Download,
  Eye,
  FileText,
  FolderOpen,
  Loader2,
  Pin,
  Save,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { arabicFieldProps } from "@/lib/arabic-bidi";
import type { CaseListItem } from "@/lib/api";
import { useLocaleStore } from "@/store/locale";

type Props = {
  title: string;
  body: string;
  onTitleChange: (v: string) => void;
  onBodyChange: (v: string) => void;
  cases: CaseListItem[];
  caseId: string;
  onCaseIdChange: (v: string) => void;
  onExportPdf?: () => void;
  onExportWord: () => void | Promise<void>;
  onPreviewWord?: () => void | Promise<void>;
  onPreviewPdf?: () => void | Promise<void>;
  onSaveTemplate?: () => void | Promise<void>;
  onSaveToCase: () => void | Promise<void>;
  savingCase?: boolean;
  exportingWord?: boolean;
  exportingPdf?: boolean;
  previewingWord?: boolean;
  previewingPdf?: boolean;
  savingTemplate?: boolean;
  /** Langue du document (dictée) — indépendante de l’UI */
  docLang?: "ar" | "fr";
  /** full = tout · edit = texte · export = téléchargements */
  mode?: "full" | "edit" | "export";
  /** Masquer « Classer dans un dossier » (déjà dans un dossier lié). */
  hideClassify?: boolean;
};

function SplitExportButton({
  primaryLabel,
  previewLabel,
  onPrimary,
  onPreview,
  busyPrimary,
  busyPreview,
  variant = "default",
  icon,
}: {
  primaryLabel: string;
  previewLabel: string;
  onPrimary: () => void;
  onPreview?: () => void;
  busyPrimary?: boolean;
  busyPreview?: boolean;
  variant?: "default" | "outline";
  icon: React.ReactNode;
}) {
  return (
    <div className="inline-flex overflow-hidden rounded-lg border border-sanad-border shadow-sm">
      <Button
        type="button"
        size="sm"
        variant={variant}
        className="rounded-none border-0"
        disabled={busyPrimary || busyPreview}
        onClick={onPrimary}
      >
        {busyPrimary ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
        {primaryLabel}
      </Button>
      {onPreview ? (
        <Button
          type="button"
          size="sm"
          variant={variant === "default" ? "default" : "outline"}
          className={cn(
            "rounded-none border-0 border-s border-white/25 px-2.5",
            variant === "outline" && "border-s border-sanad-border",
          )}
          disabled={busyPrimary || busyPreview}
          onClick={() => void onPreview()}
          title={previewLabel}
        >
          {busyPreview ? <Loader2 className="h-4 w-4 animate-spin" /> : <Eye className="h-4 w-4" />}
          <span className="ms-1 hidden sm:inline">{previewLabel}</span>
        </Button>
      ) : null}
    </div>
  );
}

/**
 * Panneau document : épingle plein écran, export, classement dossier.
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
  onExportWord,
  onPreviewWord,
  onSaveTemplate,
  onSaveToCase,
  savingCase,
  exportingWord,
  previewingWord,
  savingTemplate,
  docLang = "ar",
  mode = "full",
  hideClassify = false,
}: Props) {
  const [pinned, setPinned] = useState(false);
  const locale = useLocaleStore((s) => s.locale);
  const uiFr = locale === "fr";
  const docFr = docLang === "fr";
  const docField = arabicFieldProps(docFr);

  useEffect(() => {
    if (!pinned) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setPinned(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [pinned]);

  const t = uiFr
    ? {
        heading: "Document — modifier et exporter",
        hint: "Plein écran · Échap pour réduire",
        pin: "Plein écran",
        unpin: "Réduire",
        titlePh: "Titre de la plaidoirie",
        word: "Word",
        pdf: "PDF",
        preview: "Aperçu",
        saveTpl: "Enregistrer comme modèle",
        classify: "Classer dans un dossier",
        chooseCase: "— Choisir un dossier —",
        noCases: "Aucun dossier pour l’instant.",
        createCase: "Créer un dossier",
        save: "Enregistrer",
        bodyPh: "Texte de la plaidoirie — modifiez comme dans Word…",
      }
    : {
        heading: "الوثيقة — تعديل وتصدير",
        hint: "ملء الشاشة · Esc للتصغير",
        pin: "ملء الشاشة",
        unpin: "تصغير",
        titlePh: "عنوان المرافعة",
        word: "Word",
        pdf: "PDF",
        preview: "معاينة",
        saveTpl: "حفظ كنموذج للمكتب",
        classify: "تصنيف في ملف",
        chooseCase: "— اختيار ملف —",
        noCases: "لا يوجد ملف بعد.",
        createCase: "إنشاء ملف",
        save: "حفظ",
        bodyPh: "نص المرافعة — عدّلوا كما في Word…",
      };

  const showChrome = mode !== "export";
  const showExports = mode === "full" || mode === "export";
  // Export : déjà dans un dossier lié → pas de re-choix
  const showClassify =
    !hideClassify && (mode === "full") && !(mode === "export" && !!caseId);
  const showEditor = mode === "full" || mode === "edit";

  const exportButtons = (
    <div className="flex flex-wrap gap-2">
      <SplitExportButton
        primaryLabel={uiFr ? "Télécharger Word (.docx)" : "تحميل Word (.docx)"}
        previewLabel={t.preview}
        onPrimary={() => void onExportWord()}
        onPreview={onPreviewWord}
        busyPrimary={exportingWord}
        busyPreview={previewingWord}
        variant="default"
        icon={<FileText className="h-4 w-4" />}
      />
      {onSaveTemplate ? (
        <Button size="sm" variant="outline" disabled={savingTemplate} onClick={() => void onSaveTemplate()}>
          {savingTemplate ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          {t.saveTpl}
        </Button>
      ) : null}
    </div>
  );

  const classifyBlock = showClassify ? (
    <div className="flex flex-wrap items-end gap-2 rounded-xl border border-sanad-border bg-white p-3">
      <div className="min-w-[200px] flex-1">
        <label className="mb-1 flex items-center gap-1 text-xs font-medium text-slate-500">
          <FolderOpen className="h-3.5 w-3.5" />
          {t.classify}
        </label>
        {cases.length === 0 ? (
          <div className="rounded-lg border border-dashed border-sanad-border px-3 py-2 text-sm text-slate-600">
            <p className="mb-2">{t.noCases}</p>
            <Link href="/cases/new" className="font-semibold text-sanad-navy underline">
              {t.createCase}
            </Link>
          </div>
        ) : (
          <select
            className="w-full rounded-lg border border-sanad-border px-2 py-2 text-sm"
            value={caseId}
            onChange={(e) => onCaseIdChange(e.target.value)}
          >
            <option value="">{t.chooseCase}</option>
            {cases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.reference} — {c.client_name}
              </option>
            ))}
          </select>
        )}
      </div>
      <Button size="sm" variant="gold" disabled={savingCase || cases.length === 0} onClick={() => void onSaveToCase()}>
        {savingCase ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
        {t.save}
      </Button>
    </div>
  ) : null;

  return (
    <>
      <AnimatePresence>
        {pinned && showEditor && (
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
        className={cn(
          "overflow-hidden rounded-2xl border border-[#1a3a2a]/25 bg-white shadow-luxe",
          pinned && showEditor && "fixed inset-4 z-50 m-auto flex max-h-[min(920px,92vh)] max-w-5xl flex-col md:inset-8",
        )}
        transition={{ type: "spring", stiffness: 280, damping: 28 }}
        style={{ transformOrigin: "top center" }}
      >
        {showChrome ? (
          <div className="space-y-3 bg-gradient-to-l from-sanad-cream to-white px-4 py-3 sm:px-5">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-base font-semibold text-sanad-navy">{t.heading}</p>
                <p className="text-[11px] text-slate-500">{t.hint}</p>
              </div>
              {showEditor ? (
                <div className="flex shrink-0 items-center gap-1">
                  <Button
                    type="button"
                    size="sm"
                    variant={pinned ? "default" : "ghost"}
                    className="h-8 w-8 p-0"
                    title={pinned ? t.unpin : t.pin}
                    onClick={() => setPinned((v) => !v)}
                  >
                    <Pin className={cn("h-4 w-4", pinned && "fill-current")} />
                  </Button>
                  {pinned && (
                    <Button type="button" size="sm" variant="ghost" className="h-8 w-8 p-0" title={t.unpin} onClick={() => setPinned(false)}>
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ) : null}
            </div>

            {showEditor ? (
              <input
                className="w-full rounded-lg border border-sanad-border px-3 py-2 text-sm"
                value={title}
                onChange={(e) => onTitleChange(e.target.value)}
                placeholder={t.titlePh}
                dir={docFr ? "ltr" : "rtl"}
              />
            ) : null}

            {showExports ? exportButtons : null}
            {classifyBlock}
          </div>
        ) : (
          <div className="space-y-3 bg-gradient-to-l from-sanad-cream to-white px-4 py-3 sm:px-5">
            <p className="text-base font-semibold text-sanad-navy">{uiFr ? "Exporter" : "تصدير"}</p>
            <p className="text-[11px] text-slate-500">
              {uiFr
                ? "Télécharger = fichier final · Aperçu = ouvrir sans enregistrer."
                : "تحميل = الملف النهائي · معاينة = فتح دون حفظ."}
            </p>
            {exportButtons}
            {caseId ? (
              <p className="text-[11px] text-slate-500">
                {uiFr
                  ? `Dossier lié : ${cases.find((c) => c.id === caseId)?.reference || "—"} — pas besoin de reclasse.`
                  : `الملف المرتبط: ${cases.find((c) => c.id === caseId)?.reference || "—"}`}
              </p>
            ) : null}
          </div>
        )}

        {showEditor ? (
          <div className={cn("p-4 sm:p-5", pinned && "min-h-0 flex-1 overflow-auto")}>
            <textarea
              dir={docField.dir}
              lang={docField.lang}
              className={cn(
                docField.className,
                "w-full rounded-xl border border-[#1a3a2a]/20 bg-white px-4 py-4 text-sm leading-8 outline-none transition-all focus:ring-2 focus:ring-sanad-gold/40 whitespace-pre-wrap",
                docFr ? "text-left" : "text-right",
                pinned ? "min-h-[min(560px,55vh)]" : "min-h-[280px]",
              )}
              value={body}
              onChange={(e) => onBodyChange(e.target.value)}
              placeholder={docFr ? t.bodyPh : "نص المرافعة — عدّلوا كما في Word…"}
            />
          </div>
        ) : null}
      </motion.div>
    </>
  );
}
