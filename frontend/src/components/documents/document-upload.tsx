"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Upload, File, X, Loader2, CheckCircle2 } from "lucide-react";
import { ProcessingSteps } from "@/components/ai/processing-steps";
import { Button } from "@/components/ui/button";
import { api, ApiError, type DocumentItem } from "@/lib/api";
import { cn } from "@/lib/utils";

interface DocumentUploadProps {
  caseId: string;
  onUploaded: () => void;
  onUpload: (caseId: string, file: File) => Promise<DocumentItem>;
}

export function DocumentUpload({ caseId, onUploaded, onUpload }: DocumentUploadProps) {
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

  const handleFile = useCallback((f: File) => {
    setError("");
    setProcessingDoc(null);
    const ext = f.name.split(".").pop()?.toLowerCase();
    if (!["pdf", "docx", "png", "jpg", "jpeg", "tiff"].includes(ext || "")) {
      setError("Format non autorisé. Utilisez PDF, DOCX ou image.");
      return;
    }
    if (f.size > 50 * 1024 * 1024) {
      setError("Fichier trop volumineux (max 50 Mo).");
      return;
    }
    setFile(f);
  }, []);

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
      setError(e instanceof ApiError ? e.message : "Erreur lors de l'upload");
      setLoading(false);
    }
  }

  const isProcessing =
    loading &&
    processingDoc &&
    (processingDoc.status === "pending" || processingDoc.status === "processing");

  const isDone = processingDoc?.status === "indexed";
  const isFailed = processingDoc?.status === "failed";

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
          <p className="text-sm font-medium text-sanad-slate">
            Glissez-déposez un document ici
          </p>
          <p className="mt-1 text-xs text-slate-500">PDF, DOCX, PNG, JPG — max 50 Mo</p>
          <label className="mt-4 cursor-pointer">
            <input
              type="file"
              className="hidden"
              accept=".pdf,.docx,.png,.jpg,.jpeg,.tiff"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
              }}
            />
            <span className="inline-flex h-9 items-center rounded-lg border border-sanad-border bg-white px-4 text-sm font-medium hover:bg-sanad-light">
              Choisir un fichier
            </span>
          </label>
        </div>
      )}

      {file && !isProcessing && (
        <div className="flex items-center justify-between rounded-lg border border-sanad-border bg-white p-3">
          <div className="flex items-center gap-2">
            <File className="h-4 w-4 text-sanad-blue" />
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
            Traitement de {processingDoc.original_name}
          </div>
          <ProcessingSteps status={processingDoc.status} />
          <p className="text-xs text-slate-500">
            Extraction OCR et indexation en cours — quelques instants...
          </p>
        </div>
      )}

      {isFailed && processingDoc && (
        <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          Échec du traitement de {processingDoc.original_name}. Vérifiez le format ou réessayez.
        </div>
      )}

      {isDone && processingDoc && (
        <div className="flex items-center gap-2 rounded-lg bg-green-50 px-4 py-3 text-sm text-green-800">
          <CheckCircle2 className="h-4 w-4" />
          {processingDoc.original_name} indexé avec succès.
          {processingDoc.ocr_alert && " Attention : qualité OCR faible."}
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
              Import en cours...
            </>
          ) : (
            "Importer et analyser"
          )}
        </Button>
      )}
    </div>
  );
}
