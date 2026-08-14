"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/app-shell";
import { api, type CaseListItem, type DocumentItem } from "@/lib/api";
import { useLocaleStore, useTranslations } from "@/store/locale";

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} o`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
}

function ocrPercent(doc: DocumentItem) {
  if (doc.status === "ready" || doc.status === "done" || doc.status === "Traité") return 100;
  if (typeof doc.ocr_score === "number") return Math.min(100, Math.max(8, Math.round(doc.ocr_score)));
  if (doc.status === "processing" || doc.status === "pending") return 62;
  return 100;
}

function statusLabel(doc: DocumentItem, ar: boolean) {
  const pct = ocrPercent(doc);
  if (pct >= 100) return ar ? "معالَج" : "Traité";
  return ar ? "جارٍ" : "En cours";
}

export default function DocumentsPage() {
  const locale = useLocaleStore((s) => s.locale);
  const t = useTranslations().app.documents;
  const ar = locale === "ar";
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [caseId, setCaseId] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([api.getDocuments(), api.getCases()])
      .then(([docs, cs]) => {
        setDocuments(docs);
        setCases(cs);
        if (!caseId && cs[0]) setCaseId(cs[0].id);
      })
      .catch(() => {
        setDocuments([]);
        setCases([]);
      })
      .finally(() => setLoading(false));
  }, [caseId]);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleFiles(files: FileList | null) {
    if (!files?.length || !caseId) return;
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        await api.uploadDocument(caseId, file);
      }
      load();
    } finally {
      setUploading(false);
      setDragging(false);
    }
  }

  return (
    <AppShell>
      <div className="section-title">{t.title}</div>
      <div className="section-sub">
        {ar
          ? "أسقط ملفاتك — سند يقرأها ويصنّفها ويلخّصها."
          : "Déposez vos pièces — Sanad les lit, les classe et les synthétise."}
      </div>

      {cases.length > 0 && (
        <div className="dossiers-top" style={{ marginBottom: 12 }}>
          <div className="search-fluid" style={{ maxWidth: 360 }}>
            <select
              value={caseId}
              onChange={(e) => setCaseId(e.target.value)}
              style={{ border: "none", outline: "none", flex: 1, background: "transparent", fontSize: 13.5 }}
              aria-label={ar ? "ملف الوجهة" : "Dossier cible"}
            >
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.reference} — {c.client_name}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      <div
        className={`drop-zone${dragging ? " is-dragover" : ""}`}
        onDragEnter={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          void handleFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
      >
        <div className="icon-up">
          <svg viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round">
            <path d="M12 16V4" />
            <path d="M7 9l5-5 5 5" />
            <path d="M4 20h16" />
          </svg>
        </div>
        <h4>{ar ? "أسقط ملفاتك هنا" : "Glissez vos fichiers ici"}</h4>
        <p>
          {uploading
            ? ar
              ? "جارٍ الرفع…"
              : "Téléversement…"
            : ar
              ? "PDF، Word، صور — OCR تلقائي"
              : "PDF, Word, images — OCR automatique"}
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.webp,.txt,.audio/*,.wav,.mp3,.m4a,.webm"
          className="hidden"
          style={{ display: "none" }}
          onChange={(e) => void handleFiles(e.target.files)}
        />
      </div>

      <div className="doc-table">
        {loading ? (
          <p className="section-sub">{t.loading}</p>
        ) : documents.length === 0 ? (
          <p className="section-sub">{t.empty}</p>
        ) : (
          documents.map((doc) => {
            const pct = ocrPercent(doc);
            const gold =
              doc.mime_type?.includes("word") ||
              doc.original_name.toLowerCase().endsWith(".docx") ||
              doc.kind === "audio";
            return (
              <div key={doc.id} className="doc-row">
                <div className="doc-name">
                  <div
                    className="doc-file-ico"
                    style={
                      gold
                        ? { background: "rgba(199,151,63,0.14)", color: "var(--gold)" }
                        : undefined
                    }
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    </svg>
                  </div>
                  <div>
                    <div>{doc.original_name}</div>
                    <div className="row-sub">
                      {doc.case_reference || "—"} · {formatSize(doc.file_size)}
                    </div>
                  </div>
                </div>
                <div>
                  <div className="ocr-bar">
                    <span style={{ width: `${pct}%` }} />
                  </div>
                  <div className="row-sub" style={{ marginTop: 6 }}>
                    {pct >= 100
                      ? ar
                        ? "OCR منتهٍ"
                        : "OCR terminé"
                      : ar
                        ? "تحليل جارٍ"
                        : "Analyse en cours"}
                  </div>
                </div>
                <div
                  className={`status-pill${pct >= 100 ? " status-pill--closed" : ""}`}
                >
                  {statusLabel(doc, ar)}
                </div>
                <div style={{ textAlign: "right", color: "var(--ink-soft)" }}>
                  <Link href={`/documents/${doc.id}`} style={{ color: "inherit", textDecoration: "none" }}>
                    ⋯
                  </Link>
                </div>
              </div>
            );
          })
        )}
      </div>
    </AppShell>
  );
}
