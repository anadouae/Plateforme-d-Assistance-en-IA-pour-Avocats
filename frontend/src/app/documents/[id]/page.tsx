"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Download, Eye, FolderOpen, Info, Mic, RefreshCw, Trash2 } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { DocumentAsk } from "@/components/ai/document-ask";
import { DocumentStatusBadge } from "@/components/ai/document-status-badge";
import { ProcessingSteps } from "@/components/ai/processing-steps";
import { SynthesisPanel } from "@/components/ai/synthesis-panel";
import { DocumentPreviewModal } from "@/components/documents/document-preview-modal";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, type DocumentDetail } from "@/lib/api";
import type { Locale } from "@/lib/i18n/translations";
import { isAssistant } from "@/lib/roles";
import { canDeleteDocument } from "@/lib/ownership";
import { useAuthStore } from "@/store/auth";
import { useLocaleStore } from "@/store/locale";
import { useConfirm } from "@/components/ui/confirm-dialog";

const EXTRACT_HINT: Record<Locale, string> = {
  fr: "Texte brut extrait du document (Word natif ou lecture PDF). Ce n’est pas le résumé IA — la synthèse est à droite.",
  ar: "النص الخام المستخرج من الوثيقة (Word أصلي أو قراءة PDF). هذا ليس ملخص الذكاء الاصطناعي — التلخيص على اليمين.",
};

const TRANSCRIPT_HINT: Record<Locale, string> = {
  fr: "Transcription audio du fichier archivé. Ce n’est pas le résumé IA — la synthèse structurée est à droite.",
  ar: "تفريغ الملف الصوتي المؤرشف. هذا ليس ملخص الذكاء الاصطناعي — التلخيص المنظم على اليمين.",
};

const DOC_SUGGESTIONS: Record<Locale, string[]> = {
  fr: [
    "De quoi parle ce document ?",
    "Quelles sont les parties concernées ?",
    "Y a-t-il des délais ou montants importants ?",
  ],
  ar: [
    "ما موضوع هذه الوثيقة؟",
    "من هم الأطراف المعنيون؟",
    "هل توجد آجال أو مبالغ مهمة؟",
  ],
};

const UI: Record<
  Locale,
  {
    back: string;
    loading: string;
    extractTitle: string;
    transcriptTitle: string;
    download: string;
    preview: string;
    previewHint: string;
    reextract: string;
    retranscribe: string;
    extracting: string;
    noText: string;
    synthTitle: string;
    questionsTitle: string;
    questionsPending: string;
    audioPlayer: string;
    failed: string;
    openCase: string;
    deleteDoc: string;
    deleteConfirm: string;
    deleteFail: string;
  }
> = {
  fr: {
    back: "Retour aux documents",
    loading: "Chargement du document…",
    extractTitle: "Aperçu extrait",
    transcriptTitle: "Transcription",
    download: "Télécharger",
    preview: "Aperçu",
    previewHint: "Ouvrir le fichier original (PDF, Word…) dans une fenêtre, comme sur le portail ENT.",
    reextract: "Ré-extraire le texte",
    retranscribe: "Relancer la transcription",
    extracting: "Extraction en cours…",
    noText: "Aucun texte extractible.",
    synthTitle: "Synthèse structurée",
    questionsTitle: "Questions sur le document",
    questionsPending: "Disponible une fois le document indexé.",
    audioPlayer: "Écoute du fichier audio",
    failed: "Fichier illisible — le traitement automatique a échoué",
    openCase: "Accéder au dossier",
    deleteDoc: "Supprimer",
    deleteConfirm: "Supprimer ce document définitivement ?",
    deleteFail: "Suppression impossible. Réessayez.",
  },
  ar: {
    back: "العودة إلى الوثائق",
    loading: "جاري تحميل الوثيقة…",
    extractTitle: "معاينة النص المستخرج",
    transcriptTitle: "التفريغ الصوتي",
    download: "تحميل",
    preview: "معاينة",
    previewHint: "افتح الملف الأصلي (PDF، Word…) في نافذة مثل بوابة ENT.",
    reextract: "إعادة الاستخراج",
    retranscribe: "إعادة التفريغ الصوتي",
    extracting: "جاري الاستخراج…",
    noText: "لا يوجد نص قابل للاستخراج.",
    synthTitle: "تلخيص منظم",
    questionsTitle: "أسئلة حول الوثيقة",
    questionsPending: "متاح بعد فهرسة الوثيقة.",
    audioPlayer: "استماع الملف الصوتي",
    failed: "الملف غير قابل للقراءة — فشلت المعالجة التلقائية",
    openCase: "الوصول إلى الملف",
    deleteDoc: "حذف",
    deleteConfirm: "حذف هذه الوثيقة نهائياً؟",
    deleteFail: "تعذّر الحذف. أعد المحاولة.",
  },
};

export default function DocumentViewerPage() {
  const params = useParams();
  const router = useRouter();
  const docId = params.id as string;
  const user = useAuthStore((s) => s.user);
  const locale = useLocaleStore((s) => s.locale);
  const confirm = useConfirm();
  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [loadState, setLoadState] = useState<"loading" | "ok" | "error">("loading");
  const [reextracting, setReextracting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [downloadPct, setDownloadPct] = useState<number | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioError, setAudioError] = useState("");

  const t = UI[locale];
  const assistant = isAssistant(user?.role);
  const canUseAI = !assistant && user?.role !== "assistant_juridique";
  const isProcessing = doc?.status === "pending" || doc?.status === "processing";
  const isIndexed = doc?.status === "indexed";
  const isAudio = doc?.kind === "audio";
  const hasText = Boolean(doc?.extracted_text_preview?.trim());
  const suggestions = useMemo(() => DOC_SUGGESTIONS[locale], [locale]);

  const refresh = useCallback(() => {
    setLoadState((prev) => (prev === "ok" ? "ok" : "loading"));
    api
      .getDocument(docId)
      .then((d) => {
        setDoc(d);
        setLoadState("ok");
      })
      .catch(() => {
        setDoc(null);
        setLoadState("error");
      });
  }, [docId]);

  async function handleReextract() {
    setReextracting(true);
    try {
      const updated = await api.reextractDocument(docId);
      setDoc(updated);
      if (updated.status === "pending" || updated.status === "processing") {
        void confirm({
          title:
            locale === "ar"
              ? "جاري إعادة الاستخراج في الخلفية…"
              : "Ré-extraction lancée en arrière-plan…",
          confirmLabel: "OK",
        });
      }
    } catch {
      void confirm({
        title:
          locale === "ar"
            ? "تعذرت إعادة الاستخراج. حاول مرة أخرى."
            : "Ré-extraction impossible. Réessayez.",
        confirmLabel: "OK",
      });
    } finally {
      setReextracting(false);
    }
  }

  async function handleDelete() {
    const ok = await confirm({
      title: t.deleteConfirm,
      tone: "danger",
      requireDeletePhrase: true,
      deleteVisual: "document",
    });
    if (!ok) return;
    setDeleting(true);
    try {
      await api.deleteDocument(docId);
      router.push("/documents");
    } catch {
      await confirm({ title: t.deleteFail, confirmLabel: "OK" });
    } finally {
      setDeleting(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (!isProcessing) return;
    const timer = setInterval(refresh, 2500);
    return () => clearInterval(timer);
  }, [isProcessing, refresh]);

  useEffect(() => {
    if (!isAudio) {
      setAudioUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
      setAudioError("");
      return;
    }
    let revoked = false;
    let objectUrl: string | null = null;
    const token = api.getAuthToken();
    setAudioError("");
    fetch(api.getDocumentDownloadUrl(docId), {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })
      .then(async (r) => {
        if (!r.ok) throw new Error(String(r.status));
        return r.blob();
      })
      .then((blob) => {
        if (revoked) return;
        objectUrl = URL.createObjectURL(blob);
        setAudioUrl(objectUrl);
      })
      .catch(() => {
        if (!revoked) {
          setAudioUrl(null);
          setAudioError(
            locale === "ar"
              ? "تعذر تشغيل الصوت (جلسة منتهية أو ملف غير متاح)."
              : "Lecture audio impossible (session expirée ou fichier indisponible).",
          );
        }
      });
    return () => {
      revoked = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [isAudio, docId, locale]);

  if (loadState === "loading" && !doc) {
    return (
      <AppShell>
        <div className="flex items-center gap-2 text-slate-500">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-sanad-blue border-t-transparent" />
          {t.loading}
        </div>
      </AppShell>
    );
  }

  if (loadState === "error" || !doc) {
    return (
      <AppShell>
        <div className="space-y-3">
          <p className="text-slate-600">
            {locale === "ar"
              ? "تعذر فتح الوثيقة. ربما حُذفت أو انتهت الجلسة."
              : "Document introuvable ou session expirée."}
          </p>
          <button type="button" className="btn-ghost" onClick={() => refresh()}>
            {locale === "ar" ? "إعادة المحاولة" : "Réessayer"}
          </button>
          <Link href="/documents" className="text-sm text-sanad-blue hover:underline">
            {locale === "ar" ? "العودة إلى الوثائق" : "Retour aux documents"}
          </Link>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Link
              href="/documents"
              className="mb-2 inline-flex items-center gap-1 text-sm text-sanad-blue hover:underline"
            >
              <ArrowLeft className="h-4 w-4" />
              {t.back}
            </Link>
            <h1 className="flex items-center gap-2 text-2xl font-bold text-sanad-slate">
              {isAudio && <Mic className="h-6 w-6 text-sanad-blue" />}
              {doc.original_name}
            </h1>
            <DocumentStatusBadge
              className="mt-2"
              status={doc.status}
              ocrScore={isAudio ? null : doc.ocr_score}
              ocrAlert={isAudio ? false : !!doc.ocr_alert}
              kind={
                isAudio
                  ? "audio"
                  : doc.original_name?.toLowerCase().endsWith(".docx")
                    ? "docx"
                    : doc.kind || "file"
              }
            />
            {doc.status === "failed" && (
              <div className="mt-2 flex flex-wrap items-center gap-3">
                <p className="text-sm text-red-600">
                  {t.failed}
                  {doc.error_message
                    ? ` — ${
                        /BadZipFile|zipfile|not a zip/i.test(doc.error_message)
                          ? locale === "ar"
                            ? "الملف تالف أو ليس Word/PDF صالحاً. حمّلوا الأصل أو أعيدوا الرفع."
                            : "Fichier endommagé ou invalide. Téléchargez l’original ou réuploadez une copie saine."
                          : doc.error_message
                      }`
                    : ""}
                </p>
                <Button
                  type="button"
                  size="sm"
                  className="bg-sanad-blue text-white hover:bg-sanad-blue/90"
                  disabled={reextracting}
                  onClick={() => void handleReextract()}
                >
                  <RefreshCw className={`h-4 w-4 ${reextracting ? "animate-spin" : ""}`} />
                  {reextracting
                    ? t.extracting
                    : locale === "ar"
                      ? "إعادة المحاولة"
                      : "Réessayer"}
                </Button>
              </div>
            )}
          </div>
          <div className="row-actions">
            {!isAudio ? (
              <button
                type="button"
                className="btn-action btn-action--primary"
                onClick={() => setPreviewOpen(true)}
              >
                <Eye className="h-3.5 w-3.5" />
                {t.preview}
              </button>
            ) : null}
            {doc.case_id ? (
              <Link href={`/cases/${doc.case_id}`} className="btn-action btn-action--primary">
                <FolderOpen className="h-3.5 w-3.5" />
                {t.openCase}
                {doc.case_reference ? ` · ${doc.case_reference}` : ""}
              </Link>
            ) : null}
            {canDeleteDocument({
              role: user?.role,
              userId: user?.id,
              uploadedBy: doc.uploaded_by,
            }) ? (
            <button
              type="button"
              className="btn-action btn-action--danger"
              disabled={deleting}
              onClick={() => void handleDelete()}
            >
              <Trash2 className="h-3.5 w-3.5" />
              {t.deleteDoc}
            </button>
            ) : null}
          </div>
        </div>

        {isProcessing && (
          <ProcessingSteps status={doc.status} kind={isAudio ? "audio" : "file"} />
        )}

        {isAudio && audioUrl && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Mic className="h-4 w-4" />
                {t.audioPlayer}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <audio controls className="w-full" src={audioUrl} preload="metadata">
                <track kind="captions" />
              </audio>
            </CardContent>
          </Card>
        )}

        {isAudio && !audioUrl && audioError && (
          <p className="text-sm text-red-600">{audioError}</p>
        )}

        {assistant ? (
          <Card>
            <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
              <CardTitle>
                {locale === "ar" ? "معاينة الوثيقة" : "Aperçu du document"}
              </CardTitle>
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="default"
                  size="sm"
                  className="bg-sanad-blue text-white hover:bg-sanad-blue/90"
                  onClick={() => setPreviewOpen(true)}
                >
                  <Eye className="h-4 w-4" />
                  {t.preview}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={downloadPct !== null}
                  onClick={() => {
                    setDownloadPct(0);
                    void api
                      .downloadDocument(docId, doc.original_name, (pct) => setDownloadPct(pct))
                      .catch((err) => {
                        void confirm({
                          title:
                            err instanceof Error
                              ? err.message
                              : locale === "ar"
                                ? "تعذّر التحميل."
                                : "Téléchargement impossible.",
                          confirmLabel: "OK",
                        });
                      })
                      .finally(() => {
                        window.setTimeout(() => setDownloadPct(null), 600);
                      });
                  }}
                >
                  <Download className="h-4 w-4" />
                  {downloadPct !== null
                    ? locale === "ar"
                      ? `تحميل ${downloadPct}%`
                      : `Téléchargement ${downloadPct}%`
                    : t.download}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600">{t.previewHint}</p>
            </CardContent>
          </Card>
        ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between gap-3">
              <CardTitle>{isAudio ? t.transcriptTitle : t.extractTitle}</CardTitle>
              <div className="flex flex-wrap items-center gap-2">
                <Button
                  variant="default"
                  size="sm"
                  className="bg-sanad-navy text-white hover:bg-sanad-navy/90"
                  onClick={() => setPreviewOpen(true)}
                >
                  <Eye className="h-4 w-4" />
                  {t.preview}
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  className="bg-sanad-blue text-white hover:bg-sanad-blue/90"
                  disabled={reextracting}
                  onClick={() => void handleReextract()}
                  title={isAudio ? t.retranscribe : t.reextract}
                >
                  <RefreshCw className={`h-4 w-4 ${reextracting ? "animate-spin" : ""}`} />
                  {reextracting ? t.extracting : isAudio ? t.retranscribe : t.reextract}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={downloadPct !== null}
                  onClick={() => {
                    setDownloadPct(0);
                    void api
                      .downloadDocument(docId, doc.original_name, (pct) => setDownloadPct(pct))
                      .catch((err) => {
                        void confirm({
                          title:
                            err instanceof Error
                              ? err.message
                              : locale === "ar"
                                ? "تعذّر التحميل."
                                : "Téléchargement impossible.",
                          confirmLabel: "OK",
                        });
                      })
                      .finally(() => {
                        window.setTimeout(() => setDownloadPct(null), 600);
                      });
                  }}
                >
                  <Download className="h-4 w-4" />
                  {downloadPct !== null
                    ? locale === "ar"
                      ? `تحميل ${downloadPct}%`
                      : `Téléchargement ${downloadPct}%`
                    : t.download}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-start gap-2 rounded-lg border border-sanad-gold/25 bg-sanad-cream/60 px-3 py-2.5 text-xs leading-relaxed text-sanad-navy/80">
                <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-sanad-gold" />
                <p>{isAudio ? TRANSCRIPT_HINT[locale] : EXTRACT_HINT[locale]}</p>
              </div>
              {doc.extracted_text_preview ? (
                <div className="space-y-2">
                  <p className="text-xs text-slate-500">
                    {locale === "ar"
                      ? `النص الكامل · ${doc.extracted_text_preview.length.toLocaleString("ar-MA")} حرف — مرّروا للأسفل لقراءة كل الصفحات`
                      : `Texte complet · ${doc.extracted_text_preview.length.toLocaleString("fr-FR")} caractères — faites défiler pour tout lire`}
                  </p>
                  <div
                    dir="auto"
                    className="max-h-[40rem] overflow-y-auto whitespace-pre-wrap rounded-lg border border-sanad-border bg-sanad-light/50 p-4 text-sm leading-relaxed text-slate-700"
                  >
                    {doc.extracted_text_preview}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-slate-400">
                  {isProcessing ? t.extracting : t.noText}
                </p>
              )}
            </CardContent>
          </Card>

          {canUseAI && (
            <Card>
              <CardHeader>
                <CardTitle>{t.synthTitle}</CardTitle>
              </CardHeader>
              <CardContent>
                <SynthesisPanel
                  documentId={docId}
                  documentName={doc.original_name}
                  canAnalyze={hasText}
                  hasText={hasText}
                  kind={isAudio ? "audio" : "file"}
                />
              </CardContent>
          </Card>
        )}
        </div>
        )}

        {!assistant && canUseAI && (
          <Card>
            <CardHeader>
              <CardTitle>{t.questionsTitle}</CardTitle>
            </CardHeader>
            <CardContent>
              {isIndexed && hasText ? (
                <DocumentAsk documentId={docId} suggestions={suggestions} />
              ) : (
                <p className="text-sm text-slate-500">{t.questionsPending}</p>
              )}
            </CardContent>
          </Card>
        )}
      </div>
      {!isAudio && doc ? (
        <DocumentPreviewModal
          doc={{
            id: docId,
            name: doc.original_name,
            mimeType: doc.mime_type,
            textPreview: doc.extracted_text_preview,
          }}
          open={previewOpen}
          onClose={() => setPreviewOpen(false)}
          ar={locale === "ar"}
        />
      ) : null}
    </AppShell>
  );
}
