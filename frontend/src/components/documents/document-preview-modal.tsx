"use client";

import { useCallback, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { Download, FileText, Loader2, X } from "lucide-react";
import { ApiError, api } from "@/lib/api";
import { Button } from "@/components/ui/button";

export type DocumentPreviewTarget = {
  id: string;
  name: string;
  mimeType?: string | null;
  /** Texte extrait pour DOCX / fallback */
  textPreview?: string | null;
};

function isPdf(name: string, mime?: string | null) {
  const m = (mime || "").toLowerCase();
  const n = name.toLowerCase();
  return m.includes("pdf") || n.endsWith(".pdf");
}

function isImage(name: string, mime?: string | null) {
  const m = (mime || "").toLowerCase();
  const n = name.toLowerCase();
  return m.startsWith("image/") || /\.(png|jpe?g|webp|gif)$/i.test(n);
}

function isDocx(name: string, mime?: string | null) {
  const m = (mime || "").toLowerCase();
  const n = name.toLowerCase();
  return m.includes("wordprocessingml") || m.includes("msword") || n.endsWith(".docx") || n.endsWith(".doc");
}

function isPlainText(name: string, mime?: string | null) {
  const m = (mime || "").toLowerCase();
  const n = name.toLowerCase();
  return (
    m.startsWith("text/") ||
    m.includes("json") ||
    m.includes("xml") ||
    /\.(md|markdown|txt|rtf|csv|json|xml|html?|log)$/i.test(n)
  );
}

export function DocumentPreviewModal({
  doc,
  open,
  onClose,
  ar,
}: {
  doc: DocumentPreviewTarget | null;
  open: boolean;
  onClose: () => void;
  ar?: boolean;
}) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [textPreview, setTextPreview] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  const cleanup = useCallback(() => {
    setBlobUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    setError("");
    setTextPreview(null);
  }, []);

  async function handleDownload() {
    if (!doc) return;
    setDownloading(true);
    setError("");
    try {
      await api.downloadDocument(doc.id, doc.name);
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.message
          : ar
            ? "تعذر تحميل الملف."
            : "Téléchargement impossible.",
      );
    } finally {
      setDownloading(false);
    }
  }

  useEffect(() => {
    if (!open || !doc) {
      cleanup();
      return;
    }

    const pdfOrImg = isPdf(doc.name, doc.mimeType) || isImage(doc.name, doc.mimeType);
    const wantsText =
      isDocx(doc.name, doc.mimeType) ||
      isPlainText(doc.name, doc.mimeType) ||
      Boolean(doc.textPreview?.trim());

    let cancelled = false;
    setLoading(true);
    setError("");
    setTextPreview(doc.textPreview?.trim() || null);

    const load = async () => {
      try {
        if (wantsText && !doc.textPreview?.trim()) {
          const detail = await api.getDocument(doc.id);
          if (!cancelled) {
            setTextPreview(detail.extracted_text_preview?.trim() || null);
          }
        }
        if (pdfOrImg) {
          const { blob } = await api.fetchDocumentBlob(doc.id, doc.name);
          if (cancelled) return;
          const url = URL.createObjectURL(blob);
          setBlobUrl(url);
        } else {
          setBlobUrl(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(
            e instanceof ApiError
              ? e.message
              : ar
                ? "تعذر تحميل المعاينة. حاول التحميل."
                : "Impossible de charger l'aperçu. Essayez le téléchargement.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void load();

    return () => {
      cancelled = true;
      cleanup();
    };
  }, [open, doc, ar, cleanup]);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (!open || !doc || typeof document === "undefined") return null;

  const showPdf = isPdf(doc.name, doc.mimeType);
  const showImg = isImage(doc.name, doc.mimeType);
  const showText =
    isDocx(doc.name, doc.mimeType) ||
    isPlainText(doc.name, doc.mimeType) ||
    Boolean(textPreview?.trim());

  return createPortal(
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-[#0B1A4D]/60 p-3 backdrop-blur-[3px] sm:p-6"
      role="dialog"
      aria-modal="true"
      aria-label={doc.name}
      onClick={onClose}
    >
      <div
        className="flex h-[min(92vh,900px)] w-full max-w-5xl flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex shrink-0 items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 py-3">
          <div className="flex min-w-0 items-center gap-2">
            <FileText className="h-5 w-5 shrink-0 text-[#0B1A4D]" />
            <p className="truncate font-medium text-[#0B1A4D]">{doc.name}</p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="gap-1.5"
              disabled={downloading}
              onClick={() => void handleDownload()}
            >
              {downloading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
              {ar ? "تحميل" : "Télécharger"}
            </Button>
            <button
              type="button"
              className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
              aria-label={ar ? "إغلاق" : "Fermer"}
              onClick={onClose}
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="relative min-h-0 flex-1 bg-[#525659]">
          {loading ? (
            <div className="flex h-full items-center justify-center gap-2 text-white/90">
              <Loader2 className="h-6 w-6 animate-spin" />
              {ar ? "جاري التحميل…" : "Chargement…"}
            </div>
          ) : error && !showText ? (
            <div className="flex h-full flex-col items-center justify-center gap-3 px-6 text-center text-white/90">
              <p className="text-sm">{error}</p>
              <Button type="button" variant="outline" onClick={() => void handleDownload()}>
                {ar ? "تحميل الملف" : "Télécharger le fichier"}
              </Button>
            </div>
          ) : showPdf && blobUrl ? (
            <iframe title={doc.name} src={blobUrl} className="h-full w-full border-0 bg-white" />
          ) : showImg && blobUrl ? (
            <div className="flex h-full items-center justify-center overflow-auto p-4">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={blobUrl} alt={doc.name} className="max-h-full max-w-full object-contain shadow-lg" />
            </div>
          ) : showText ? (
            <div className="h-full overflow-y-auto bg-white p-6">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                {ar ? "معاينة النص" : "Aperçu du contenu"}
              </p>
              {error ? <p className="mb-3 text-sm text-red-600">{error}</p> : null}
              {textPreview?.trim() ? (
                <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-800" dir="auto">
                  {textPreview.slice(0, 120_000)}
                </pre>
              ) : (
                <p className="text-sm text-slate-600">
                  {ar
                    ? "لا يوجد نص مستخرج بعد. حمّلوا الملف أو أعيدوا الاستخراج."
                    : "Aucun texte extractible pour l’instant. Téléchargez le fichier ou relancez l’extraction."}
                </p>
              )}
            </div>
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-3 px-6 text-center text-white/90">
              <p className="text-sm">
                {ar
                  ? "لا توجد معاينة لهذا النوع. استخدم التحميل."
                  : "Pas d'aperçu pour ce type de fichier. Utilisez le téléchargement."}
              </p>
              <Button type="button" variant="outline" onClick={() => void handleDownload()}>
                {ar ? "تحميل" : "Télécharger"}
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body,
  );
}
