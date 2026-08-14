"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Download, Info, Mic, RefreshCw } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { DocumentAsk } from "@/components/ai/document-ask";
import { DocumentStatusBadge } from "@/components/ai/document-status-badge";
import { ProcessingSteps } from "@/components/ai/processing-steps";
import { SynthesisPanel } from "@/components/ai/synthesis-panel";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, type DocumentDetail } from "@/lib/api";
import type { Locale } from "@/lib/i18n/translations";
import { useAuthStore } from "@/store/auth";
import { useLocaleStore } from "@/store/locale";

const EXTRACT_HINT: Record<Locale, string> = {
  fr: "Ce n'est pas un résumé IA. C'est le texte brut extrait du PDF (OCR ou lecture directe). La synthèse structurée est dans le panneau à droite.",
  ar: "هذا ليس ملخصاً بالذكاء الاصطناعي. إنه النص الخام المستخرج من ملف PDF (OCR أو قراءة مباشرة). التلخيص المنظم موجود في اللوحة اليمنى.",
};

const TRANSCRIPT_HINT: Record<Locale, string> = {
  fr: "Ce n'est pas un résumé IA. C'est la transcription Whisper (arabe) du fichier audio archivé. La synthèse structurée est dans le panneau à droite.",
  ar: "هذا ليس ملخصاً بالذكاء الاصطناعي. إنه تفريغ Whisper (عربي) للملف الصوتي المؤرشف. التلخيص المنظم موجود في اللوحة اليمنى.",
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
    reextract: string;
    retranscribe: string;
    extracting: string;
    noText: string;
    synthTitle: string;
    questionsTitle: string;
    questionsPending: string;
    audioPlayer: string;
    failed: string;
  }
> = {
  fr: {
    back: "Retour au dossier",
    loading: "Chargement du document…",
    extractTitle: "Aperçu extrait",
    transcriptTitle: "Transcription",
    download: "Télécharger",
    reextract: "Ré-extraire (arabe)",
    retranscribe: "Re-transcrire (Whisper)",
    extracting: "Extraction en cours…",
    noText: "Aucun texte extractible.",
    synthTitle: "Synthèse structurée",
    questionsTitle: "Questions sur le document",
    questionsPending: "Disponible une fois le document indexé.",
    audioPlayer: "Écoute du fichier audio",
    failed: "Échec du traitement",
  },
  ar: {
    back: "العودة إلى الملف",
    loading: "جاري تحميل الوثيقة…",
    extractTitle: "معاينة النص المستخرج",
    transcriptTitle: "التفريغ الصوتي",
    download: "تحميل",
    reextract: "إعادة الاستخراج",
    retranscribe: "إعادة التفريغ (Whisper)",
    extracting: "جاري الاستخراج…",
    noText: "لا يوجد نص قابل للاستخراج.",
    synthTitle: "تلخيص منظم",
    questionsTitle: "أسئلة حول الوثيقة",
    questionsPending: "متاح بعد فهرسة الوثيقة.",
    audioPlayer: "استماع الملف الصوتي",
    failed: "فشل المعالجة",
  },
};

export default function DocumentViewerPage() {
  const params = useParams();
  const docId = params.id as string;
  const user = useAuthStore((s) => s.user);
  const locale = useLocaleStore((s) => s.locale);
  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [reextracting, setReextracting] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const t = UI[locale];
  const canUseAI = user?.role !== "assistant_juridique";
  const isProcessing = doc?.status === "pending" || doc?.status === "processing";
  const isIndexed = doc?.status === "indexed";
  const isAudio = doc?.kind === "audio";
  const hasText = Boolean(doc?.extracted_text_preview?.trim());
  const suggestions = useMemo(() => DOC_SUGGESTIONS[locale], [locale]);

  const refresh = useCallback(() => {
    api.getDocument(docId).then(setDoc).catch(() => setDoc(null));
  }, [docId]);

  async function handleReextract() {
    setReextracting(true);
    try {
      const updated = await api.reextractDocument(docId);
      setDoc(updated);
    } catch {
      window.alert(
        locale === "ar"
          ? "تعذرت إعادة الاستخراج. حاول مرة أخرى."
          : "Ré-extraction impossible. Réessayez.",
      );
    } finally {
      setReextracting(false);
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
      return;
    }
    let revoked = false;
    let objectUrl: string | null = null;
    fetch(api.getDocumentDownloadUrl(docId), {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("sanad_token")}`,
      },
    })
      .then((r) => r.blob())
      .then((blob) => {
        if (revoked) return;
        objectUrl = URL.createObjectURL(blob);
        setAudioUrl(objectUrl);
      })
      .catch(() => {
        if (!revoked) setAudioUrl(null);
      });
    return () => {
      revoked = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [isAudio, docId]);

  if (!doc) {
    return (
      <AppShell>
        <div className="flex items-center gap-2 text-slate-500">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-sanad-blue border-t-transparent" />
          {t.loading}
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <Link
            href={`/cases/${doc.case_id}`}
            className="mb-2 inline-flex items-center gap-1 text-sm text-sanad-blue hover:underline"
          >
            <ArrowLeft className="h-4 w-4" />
            {t.back} {doc.case_reference}
          </Link>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-sanad-slate">
            {isAudio && <Mic className="h-6 w-6 text-sanad-blue" />}
            {doc.original_name}
          </h1>
          <DocumentStatusBadge
            className="mt-2"
            status={doc.status}
            ocrScore={isAudio ? null : doc.ocr_score}
            ocrAlert={isAudio ? false : doc.ocr_alert}
          />
          {doc.status === "failed" && doc.error_message && (
            <p className="mt-2 text-sm text-red-600">
              {t.failed} — {doc.error_message}
            </p>
          )}
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

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between gap-3">
              <CardTitle>{isAudio ? t.transcriptTitle : t.extractTitle}</CardTitle>
              <div className="flex flex-wrap items-center gap-2">
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
                  onClick={() => {
                    fetch(api.getDocumentDownloadUrl(docId), {
                      headers: {
                        Authorization: `Bearer ${localStorage.getItem("sanad_token")}`,
                      },
                    })
                      .then((r) => r.blob())
                      .then((blob) => window.open(URL.createObjectURL(blob)));
                  }}
                >
                  <Download className="h-4 w-4" />
                  {t.download}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-start gap-2 rounded-lg border border-sanad-gold/25 bg-sanad-cream/60 px-3 py-2.5 text-xs leading-relaxed text-sanad-navy/80">
                <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-sanad-gold" />
                <p>{isAudio ? TRANSCRIPT_HINT[locale] : EXTRACT_HINT[locale]}</p>
              </div>
              {doc.extracted_text_preview ? (
                <div
                  dir="auto"
                  className="max-h-[28rem] overflow-y-auto whitespace-pre-wrap rounded-lg border border-sanad-border bg-sanad-light/50 p-4 text-sm leading-relaxed text-slate-700"
                >
                  {doc.extracted_text_preview}
                  {doc.extracted_text_preview.length >= 2000 && "…"}
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

        {canUseAI && (
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
    </AppShell>
  );
}
