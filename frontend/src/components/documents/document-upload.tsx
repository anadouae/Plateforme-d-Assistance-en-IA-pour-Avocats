"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Upload, File, Mic, X, Loader2, CheckCircle2, Plus } from "lucide-react";
import { ProcessingSteps } from "@/components/ai/processing-steps";
import { Button } from "@/components/ui/button";
import { api, ApiError, type DocumentItem } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useClientLocale, useTranslations } from "@/store/locale";

interface DocumentUploadProps {
  caseId: string;
  onUploaded: () => void;
  onUpload: (caseId: string, file: File) => Promise<DocumentItem>;
}

const ALLOWED_EXTS = [
  "pdf",
  "docx",
  "txt",
  "md",
  "markdown",
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
const ACCEPT =
  ".pdf,.docx,.txt,.md,.markdown,.png,.jpg,.jpeg,.tiff,.webm,.wav,.mp3,.m4a,.ogg,.mp4,.mpeg,.mpga,audio/*,text/plain,text/markdown";

function isAudioFile(name: string, kind?: string | null) {
  if (kind === "audio") return true;
  const ext = name.split(".").pop()?.toLowerCase() || "";
  return AUDIO_EXTS.has(ext);
}

type DoneItem = { name: string; ocrWeak?: boolean };

export function DocumentUpload({ caseId, onUploaded, onUpload }: DocumentUploadProps) {
  const t = useTranslations().app.documents;
  const ar = useClientLocale() === "ar";
  const [dragging, setDragging] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [processingDoc, setProcessingDoc] = useState<DocumentItem | null>(null);
  const [currentName, setCurrentName] = useState("");
  const [progress, setProgress] = useState<{ done: number; total: number } | null>(null);
  const [doneItems, setDoneItems] = useState<DoneItem[]>([]);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => () => stopPolling(), [stopPolling]);

  const addFiles = useCallback(
    (list: FileList | File[] | null) => {
      if (!list || list.length === 0) return;
      setError("");
      const incoming = Array.from(list);
      const accepted: File[] = [];
      const rejected: string[] = [];
      for (const f of incoming) {
        const ext = f.name.split(".").pop()?.toLowerCase() || "";
        if (!ALLOWED_EXTS.includes(ext)) {
          rejected.push(f.name);
          continue;
        }
        if (f.size > 50 * 1024 * 1024) {
          rejected.push(`${f.name} (>50 Mo)`);
          continue;
        }
        accepted.push(f);
      }
      if (rejected.length) {
        setError(
          `${t.formatError}${rejected.length ? ` — ${rejected.slice(0, 3).join(", ")}` : ""}`,
        );
      }
      if (!accepted.length) return;
      setFiles((prev) => {
        const keys = new Set(prev.map((p) => `${p.name}:${p.size}:${p.lastModified}`));
        const next = accepted.filter((f) => !keys.has(`${f.name}:${f.size}:${f.lastModified}`));
        return [...prev, ...next];
      });
    },
    [t.formatError],
  );

  function waitUntilSettled(docId: string): Promise<DocumentItem> {
    return new Promise((resolve, reject) => {
      stopPolling();
      pollRef.current = setInterval(async () => {
        try {
          const doc = await api.getDocument(docId);
          setProcessingDoc(doc);
          if (doc.status === "indexed" || doc.status === "failed") {
            stopPolling();
            resolve(doc);
          }
        } catch (e) {
          stopPolling();
          reject(e);
        }
      }, 800);
    });
  }

  async function handleUpload() {
    if (!files.length || loading) return;
    setLoading(true);
    setError("");
    setDoneItems([]);
    const queue = [...files];
    setFiles([]);
    setProgress({ done: 0, total: queue.length });
    let okCount = 0;
    const successes: DoneItem[] = [];

    try {
      for (let i = 0; i < queue.length; i++) {
        const file = queue[i]!;
        setCurrentName(file.name);
        setProcessingDoc(null);
        setProgress({ done: i, total: queue.length });
        try {
          const uploaded = await onUpload(caseId, file);
          setProcessingDoc(uploaded);
          const settled =
            uploaded.status === "indexed" || uploaded.status === "failed"
              ? uploaded
              : await waitUntilSettled(uploaded.id);
          setProcessingDoc(settled);
          if (settled.status === "indexed") {
            okCount += 1;
            successes.push({
              name: settled.original_name || file.name,
              ocrWeak: Boolean(settled.ocr_alert),
            });
            setDoneItems([...successes]);
          } else {
            setError(
              settled.error_message ||
                `${t.processingFailed} ${settled.original_name || file.name}.`,
            );
          }
        } catch (e) {
          setError(e instanceof ApiError ? e.message : t.uploadError);
        }
        setProgress({ done: i + 1, total: queue.length });
      }
      if (okCount > 0) onUploaded();
    } finally {
      setLoading(false);
      setCurrentName("");
      setProcessingDoc(null);
      stopPolling();
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  const isProcessing = loading;
  const audioProcessing =
    Boolean(processingDoc && isAudioFile(processingDoc.original_name, processingDoc.kind)) ||
    (currentName ? isAudioFile(currentName) : false);

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (!loading) addFiles(e.dataTransfer.files);
        }}
        className={cn(
          "flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 transition-colors sm:p-8",
          dragging
            ? "border-sanad-blue bg-sanad-blue/5"
            : "border-sanad-border bg-sanad-light/50",
          loading && "pointer-events-none opacity-60",
        )}
      >
        <Upload className="mb-3 h-8 w-8 text-slate-400" />
        <p className="text-sm font-medium text-sanad-slate">{t.dropHint}</p>
        <p className="mt-1 text-center text-xs text-slate-500">{t.formatsHint}</p>
        <p className="mt-1 text-xs text-slate-500">
          {ar
            ? "يمكن اختيار عدة ملفات دفعة واحدة."
            : "Vous pouvez sélectionner plusieurs fichiers à la fois."}
        </p>
        <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
          <label className="cursor-pointer">
            <input
              ref={inputRef}
              type="file"
              className="hidden"
              multiple
              accept={ACCEPT}
              disabled={loading}
              onChange={(e) => {
                addFiles(e.target.files);
                e.target.value = "";
              }}
            />
            <span className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-sanad-border bg-white px-4 text-sm font-medium hover:bg-sanad-light">
              <Plus className="h-4 w-4" />
              {ar ? "إضافة قطع" : "Ajouter des pièces"}
            </span>
          </label>
        </div>
      </div>

      {files.length > 0 && !isProcessing ? (
        <ul className="space-y-2">
          {files.map((file) => (
            <li
              key={`${file.name}-${file.size}-${file.lastModified}`}
              className="flex items-center justify-between rounded-lg border border-sanad-border bg-white p-3"
            >
              <div className="flex min-w-0 items-center gap-2">
                {isAudioFile(file.name) ? (
                  <Mic className="h-4 w-4 shrink-0 text-sanad-blue" />
                ) : (
                  <File className="h-4 w-4 shrink-0 text-sanad-blue" />
                )}
                <span className="truncate text-sm text-sanad-slate">{file.name}</span>
                <span className="shrink-0 text-xs text-slate-400">
                  ({(file.size / 1024).toFixed(0)} Ko)
                </span>
              </div>
              <button
                type="button"
                onClick={() =>
                  setFiles((prev) =>
                    prev.filter(
                      (f) =>
                        !(
                          f.name === file.name &&
                          f.size === file.size &&
                          f.lastModified === file.lastModified
                        ),
                    ),
                  )
                }
                className="text-slate-400 hover:text-red-500"
                aria-label={ar ? "إزالة" : "Retirer"}
              >
                <X className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      {isProcessing ? (
        <div className="space-y-3 rounded-xl border border-sanad-blue/20 bg-sanad-blue/5 p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-sanad-blue">
            <Loader2 className="h-4 w-4 animate-spin" />
            {t.processingOf} {processingDoc?.original_name || currentName}
            {progress ? ` (${progress.done + 1}/${progress.total})` : null}
          </div>
          <ProcessingSteps
            status={processingDoc?.status || "pending"}
            kind={audioProcessing ? "audio" : "file"}
          />
          <p className="text-xs text-slate-500">
            {audioProcessing ? t.processingAudioHint : t.processingHint}
          </p>
        </div>
      ) : null}

      {doneItems.length > 0 && !isProcessing ? (
        <div className="space-y-2">
          {doneItems.map((item) => (
            <div
              key={item.name}
              className="flex items-center gap-2 rounded-lg bg-green-50 px-4 py-3 text-sm text-green-800"
            >
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span>
                {item.name} {t.indexedOk}
                {item.ocrWeak ? ` ${t.ocrWeak}` : ""}
              </span>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            className="w-full"
            onClick={() => {
              setDoneItems([]);
              inputRef.current?.click();
            }}
          >
            <Plus className="h-4 w-4" />
            {ar ? "إضافة قطعة أخرى" : "Ajouter une autre pièce"}
          </Button>
        </div>
      ) : null}

      {error ? (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
      ) : null}

      {files.length > 0 && !isProcessing ? (
        <Button onClick={() => void handleUpload()} disabled={loading} className="w-full">
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              {t.importing}
            </>
          ) : files.length === 1 ? (
            t.importAnalyze
          ) : ar ? (
            `استيراد وتحليل ${files.length} ملفات`
          ) : (
            `Importer et analyser ${files.length} fichiers`
          )}
        </Button>
      ) : null}
    </div>
  );
}
