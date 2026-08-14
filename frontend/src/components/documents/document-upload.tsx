"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Upload, File, Mic, X, Loader2, CheckCircle2 } from "lucide-react";
import { ProcessingSteps } from "@/components/ai/processing-steps";
import { Button } from "@/components/ui/button";
import { api, ApiError, type DocumentItem } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useTranslations } from "@/store/locale";

interface DocumentUploadProps {
  caseId: string;
  onUploaded: () => void;
  onUpload: (caseId: string, file: File) => Promise<DocumentItem>;
}

const ALLOWED_EXTS = [
  "pdf",
  "docx",
  "png",
  "jpg",
  "jpeg",
  "tiff",
  "webm",
  "wav",
  "mp3",
  "m4a",
  "ogg",
  "mp4",
  "mpeg",
  "mpga",
];

const AUDIO_EXTS = new Set(["webm", "wav", "mp3", "m4a", "ogg", "mp4", "mpeg", "mpga"]);

function isAudioFile(name: string, kind?: string | null) {
  if (kind === "audio") return true;
  const ext = name.split(".").pop()?.toLowerCase() || "";
  return AUDIO_EXTS.has(ext);
}

export function DocumentUpload({ caseId, onUploaded, onUpload }: DocumentUploadProps) {
  const t = useTranslations().app.documents;
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [processingDoc, setProcessingDoc] = useState<DocumentItem | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => () => stopPolling(), [stopPolling]);

  const handleFile = useCallback(
    (f: File) => {
      setError("");
      setProcessingDoc(null);
      const ext = f.name.split(".").pop()?.toLowerCase();
      if (!ALLOWED_EXTS.includes(ext || "")) {
        setError(t.formatError);
        return;
      }
      if (f.size > 50 * 1024 * 1024) {
        setError(t.sizeError);
        return;
      }
      setFile(f);
    },
    [t.formatError, t.sizeError],
  );

  function startPolling(docId: string) {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const doc = await api.getDocument(docId);
        setProcessingDoc(doc);
        if (doc.status === "indexed" || doc.status === "failed") {
          stopPolling();
          setLoading(false);
          setFile(null);
          onUploaded();
        }
      } catch {
        stopPolling();
        setLoading(false);
      }
    }, 2000);
  }

  async function handleUpload() {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const uploaded = await onUpload(caseId, file);
      setProcessingDoc(uploaded);
      if (uploaded.status === "indexed") {
        setLoading(false);
        setFile(null);
        onUploaded();
      } else {
        startPolling(uploaded.id);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t.uploadError);
      setLoading(false);
    }
  }

  const isProcessing =
    loading &&
    processingDoc &&
    (processingDoc.status === "pending" || processingDoc.status === "processing");

  const isDone = processingDoc?.status === "indexed";
  const isFailed = processingDoc?.status === "failed";
  const audioProcessing =
    Boolean(processingDoc && isAudioFile(processingDoc.original_name, processingDoc.kind)) ||
    Boolean(file && isAudioFile(file.name));

  return (
    <div className="space-y-4">
      {!isProcessing && !isDone && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            const f = e.dataTransfer.files[0];
            if (f) handleFile(f);
          }}
          className={cn(
            "flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-colors",
            dragging
              ? "border-sanad-blue bg-sanad-blue/5"
              : "border-sanad-border bg-sanad-light/50",
          )}
        >
          <Upload className="mb-3 h-8 w-8 text-slate-400" />
          <p className="text-sm font-medium text-sanad-slate">{t.dropHint}</p>
          <p className="mt-1 text-xs text-slate-500">{t.formatsHint}</p>
          <label className="mt-4 cursor-pointer">
            <input
              type="file"
              className="hidden"
              accept=".pdf,.docx,.png,.jpg,.jpeg,.tiff,.webm,.wav,.mp3,.m4a,.ogg,.mp4,.mpeg,.mpga,audio/*"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
              }}
            />
            <span className="inline-flex h-9 items-center rounded-lg border border-sanad-border bg-white px-4 text-sm font-medium hover:bg-sanad-light">
              {t.chooseFile}
            </span>
          </label>
        </div>
      )}

      {file && !isProcessing && (
        <div className="flex items-center justify-between rounded-lg border border-sanad-border bg-white p-3">
          <div className="flex items-center gap-2">
            {isAudioFile(file.name) ? (
              <Mic className="h-4 w-4 text-sanad-blue" />
            ) : (
              <File className="h-4 w-4 text-sanad-blue" />
            )}
            <span className="text-sm text-sanad-slate">{file.name}</span>
            <span className="text-xs text-slate-400">
              ({(file.size / 1024).toFixed(0)} Ko)
            </span>
          </div>
          <button
            type="button"
            onClick={() => setFile(null)}
            className="text-slate-400 hover:text-red-500"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {isProcessing && processingDoc && (
        <div className="space-y-3 rounded-xl border border-sanad-blue/20 bg-sanad-blue/5 p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-sanad-blue">
            <Loader2 className="h-4 w-4 animate-spin" />
            {t.processingOf} {processingDoc.original_name}
          </div>
          <ProcessingSteps status={processingDoc.status} kind={audioProcessing ? "audio" : "file"} />
          <p className="text-xs text-slate-500">
            {audioProcessing ? t.processingAudioHint : t.processingHint}
          </p>
        </div>
      )}

      {isFailed && processingDoc && (
        <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          {processingDoc.error_message ||
            `${t.processingFailed} ${processingDoc.original_name}.`}
        </div>
      )}

      {isDone && processingDoc && (
        <div className="flex items-center gap-2 rounded-lg bg-green-50 px-4 py-3 text-sm text-green-800">
          <CheckCircle2 className="h-4 w-4" />
          {processingDoc.original_name} {t.indexedOk}
          {processingDoc.ocr_alert && ` ${t.ocrWeak}`}
        </div>
      )}

      {error && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
      )}

      {file && !isProcessing && (
        <Button onClick={handleUpload} disabled={loading} className="w-full">
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              {t.importing}
            </>
          ) : (
            t.importAnalyze
          )}
        </Button>
      )}
    </div>
  );
}
