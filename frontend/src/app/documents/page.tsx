"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/app-shell";
import {
  DocumentPreviewModal,
  type DocumentPreviewTarget,
} from "@/components/documents/document-preview-modal";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { api, type CaseListItem, type DocumentItem } from "@/lib/api";
import { inDateRange } from "@/lib/date-range";
import { isAssistant } from "@/lib/roles";
import { canDeleteDocument } from "@/lib/ownership";
import { useAuthStore } from "@/store/auth";
import { useLocaleStore, useTranslations } from "@/store/locale";

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} o`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
}

function isDocx(doc: DocumentItem) {
  return (
    doc.mime_type?.includes("word") ||
    doc.original_name.toLowerCase().endsWith(".docx") ||
    doc.original_name.toLowerCase().endsWith(".doc")
  );
}

function isProcessingStatus(doc: DocumentItem) {
  const st = (doc.status || "").toLowerCase();
  return st === "processing" || st === "pending";
}

function ocrPercent(doc: DocumentItem) {
  const st = (doc.status || "").toLowerCase();
  if (st === "failed" || st === "error") return -1;
  if (st === "ready" || st === "done" || st === "indexed" || st === "traité" || st === "traite")
    return 100;
  if (typeof doc.ocr_score === "number") return Math.min(100, Math.max(1, Math.round(doc.ocr_score)));
  if (isProcessingStatus(doc)) return 0; // indéterminé — barre animée
  if (isDocx(doc)) return 100;
  return 0;
}

function statusLabel(doc: DocumentItem, ar: boolean) {
  const st = (doc.status || "").toLowerCase();
  if (st === "failed" || st === "error") return ar ? "غير قابل للقراءة" : "Illisible";
  if (isProcessingStatus(doc)) return ar ? "جارٍ" : "En cours";
  const pct = ocrPercent(doc);
  if (pct >= 100) return ar ? "جاهز" : "Prêt";
  if (pct < 0) return ar ? "غير قابل للقراءة" : "Illisible";
  return ar ? "جارٍ" : "En cours";
}

function progressCaption(doc: DocumentItem, ar: boolean, failed: boolean, pct: number, indefinite: boolean) {
  if (failed) return doc.error_message || (ar ? "تعذّر قراءة الملف تلقائياً" : "Lecture automatique impossible");
  if (indefinite) return ar ? "تحليل جارٍ…" : "Analyse en cours…";
  if (isDocx(doc) && pct >= 100) return ar ? "Word · نص أصلي · 100%" : "Word · texte natif · 100%";
  if (doc.kind === "audio" && pct >= 100) return ar ? "تفريغ منتهٍ · 100%" : "Transcription terminée · 100%";
  if (pct >= 100) return ar ? "قراءة منتهية · 100%" : "Lecture terminée · 100%";
  return ar ? `تحليل جارٍ · ${pct}%` : `Analyse en cours · ${pct}%`;
}

export default function DocumentsPage() {
  const locale = useLocaleStore((s) => s.locale);
  const t = useTranslations().app.documents;
  const ar = locale === "ar";
  const confirm = useConfirm();
  const user = useAuthStore((s) => s.user);
  const assistant = isAssistant(user?.role);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [uploadHint, setUploadHint] = useState("");
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [previewDoc, setPreviewDoc] = useState<DocumentPreviewTarget | null>(null);
  /** Filtre liste : "" = tous les dossiers. */
  const [filterCaseId, setFilterCaseId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [uploadCaseId, setUploadCaseId] = useState("__none__");
  const [pendingFiles, setPendingFiles] = useState<File[] | null>(null);
  const [destChoice, setDestChoice] = useState("__none__");
  const inputRef = useRef<HTMLInputElement>(null);

  const loadCases = useCallback(() => {
    return api.getCases().then((cs) => {
      setCases(cs);
      setUploadCaseId((prev) => {
        if (prev && prev !== "__none__" && cs.some((c) => c.id === prev)) return prev;
        return prev || "__none__";
      });
      return cs;
    });
  }, []);

  const refresh = useCallback(() => {
    setLoading(true);
    setLoadError("");
    Promise.all([api.getDocuments(filterCaseId || undefined), loadCases()])
      .then(([docs]) => setDocuments(docs))
      .catch(() => {
        setDocuments([]);
        setCases([]);
        setLoadError(
          ar
            ? "تعذر تحميل الوثائق. تحقق من الاتصال ثم أعد المحاولة."
            : "Impossible de charger les documents. Vérifiez la connexion puis réessayez.",
        );
      })
      .finally(() => setLoading(false));
  }, [filterCaseId, loadCases, ar]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // Analyse en cours : rafraîchir jusqu’à fin / échec (barre indéterminée)
  const hasProcessing = useMemo(
    () => documents.some((d) => isProcessingStatus(d)),
    [documents],
  );
  useEffect(() => {
    if (!hasProcessing) return;
    const id = window.setInterval(() => {
      api
        .getDocuments(filterCaseId || undefined)
        .then(setDocuments)
        .catch(() => undefined);
    }, 2500);
    return () => window.clearInterval(id);
  }, [hasProcessing, filterCaseId]);

  function onCaseSelect(value: string) {
    setFilterCaseId(value);
    if (value) setUploadCaseId(value);
  }

  function openDestinationModal(files: FileList | File[] | null) {
    if (!files || (Array.isArray(files) ? files.length === 0 : !files.length)) return;
    const list = Array.from(files as FileList | File[]);
    setUploadHint("");
    setDragging(false);
    // Filtre dossier actif → upload direct sans modal
    if (filterCaseId) {
      void uploadToCase(filterCaseId, list);
      return;
    }
    setPendingFiles(list);
    setDestChoice(uploadCaseId && uploadCaseId !== "__new__" ? uploadCaseId : "__none__");
  }

  async function resolveTargetId(choice: string, caseList: CaseListItem[]): Promise<string | null> {
    if (choice === "__new__") {
      window.location.href = "/cases/new";
      return null;
    }
    if (choice && choice !== "__none__") return choice;
    const existing = caseList.find(
      (c) =>
        c.client_name === "غير مصنف" ||
        c.client_name === "Non classé" ||
        /غير\s*مصنف|non\s*class[eé]/i.test(c.client_name || ""),
    );
    if (existing) return existing.id;
    const created = await api.createCase({
      client_name: ar ? "غير مصنف" : "Non classé",
      case_type: "civil",
      status: "open",
      description: ar ? "وثائق مرفوعة بدون ملف محدد" : "Documents uploadés sans dossier",
    });
    await loadCases();
    return created.id;
  }

  async function uploadToCase(target: string, files: File[]) {
    setUploading(true);
    setUploadHint("");
    try {
      for (const file of files) {
        await api.uploadDocument(target, file);
      }
      setPendingFiles(null);
      void refresh();
    } catch (e) {
      setUploadHint(
        e instanceof Error
          ? e.message
          : ar
            ? "فشل الرفع."
            : "Échec du téléversement.",
      );
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  async function confirmDestinationUpload() {
    if (!pendingFiles?.length) return;
    setUploading(true);
    setUploadHint("");
    try {
      const fresh = await api.getCases().catch(() => cases);
      setCases(fresh);
      const target = await resolveTargetId(destChoice, fresh);
      if (!target) return;
      setUploadCaseId(target);
      for (const file of pendingFiles) {
        await api.uploadDocument(target, file);
      }
      setPendingFiles(null);
      void refresh();
    } catch (e) {
      setUploadHint(
        e instanceof Error
          ? e.message
          : ar
            ? "فشل الرفع."
            : "Échec du téléversement.",
      );
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  function cancelDestinationModal() {
    setPendingFiles(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  async function handleDelete(doc: DocumentItem) {
    if (!canDeleteDocument({ role: user?.role, userId: user?.id, uploadedBy: doc.uploaded_by })) {
      await confirm({
        title: ar ? "الحذف غير متاح" : "Suppression non autorisée",
        description: ar
          ? "يمكن حذف القطع التي رفعتموها فقط."
          : "Vous ne pouvez supprimer que les pièces que vous avez déposées.",
        confirmLabel: ar ? "حسناً" : "OK",
        cancelLabel: ar ? "إغلاق" : "Fermer",
      });
      return;
    }
    const ok = await confirm({
      title: ar ? "حذف الوثيقة" : "Supprimer le document",
      description:
        t.deleteConfirm ||
        (ar
          ? "سيتم حذف هذه الوثيقة نهائياً."
          : "Ce document sera définitivement supprimé."),
      tone: "danger",
      requireDeletePhrase: true,
      deleteVisual: "document",
    });
    if (!ok) return;
    setDeletingId(doc.id);
    try {
      await api.deleteDocument(doc.id);
      setDocuments((prev) => prev.filter((d) => d.id !== doc.id));
    } catch {
      await confirm({
        title: t.deleteFail || (ar ? "تعذّر الحذف." : "Suppression impossible."),
        confirmLabel: ar ? "حسناً" : "OK",
        cancelLabel: ar ? "إغلاق" : "Fermer",
      });
    } finally {
      setDeletingId(null);
    }
  }

  const visibleDocs = useMemo(() => {
    if (!dateFrom && !dateTo) return documents;
    return documents.filter((d) => inDateRange(d.created_at, dateFrom, dateTo));
  }, [documents, dateFrom, dateTo]);

  return (
    <AppShell>
      <div className="section-title">{t.title}</div>
      <div className="section-sub">
        {ar
          ? "أسقط ملفاتك — LexHub يقرأها ويصنّفها ويلخّصها."
          : "Déposez vos pièces — LexHub les lit, les classe et les synthétise."}
      </div>

      {loadError && (
        <div
          className="card"
          style={{
            marginBottom: 14,
            borderColor: "rgba(185,28,28,0.35)",
            background: "rgba(185,28,28,0.06)",
          }}
        >
          <p style={{ margin: 0, fontSize: 13.5 }}>{loadError}</p>
          <button type="button" className="btn-ghost" style={{ marginTop: 8 }} onClick={() => void refresh()}>
            {ar ? "إعادة المحاولة" : "Réessayer"}
          </button>
                          </div>
      )}

      {uploadHint && (
        <p className="section-sub" style={{ color: "#b91c1c", marginBottom: 10 }}>
          {uploadHint}
        </p>
      )}

      {cases.length === 0 && !loading && !loadError && (
        <p className="section-sub" style={{ marginBottom: 10 }}>
          {ar
            ? "لا يوجد ملف بعد — أنشئ ملفًا من «الملفات» ثم ارفع وثائقك هنا."
            : "Aucun dossier — créez-en un dans « Dossiers », puis déposez vos pièces ici."}
        </p>
      )}

      {cases.length > 0 && (
        <div
          className="cases-filters card"
          style={{
            marginBottom: 14,
            padding: "14px 16px",
            border: "1px solid rgba(76,124,255,0.16)",
            display: "grid",
            gap: 12,
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            alignItems: "end",
          }}
        >
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>
              {ar ? "الملف" : "Dossier"}
            </span>
            <select
              value={filterCaseId}
              onChange={(e) => onCaseSelect(e.target.value)}
              style={{
                border: "1px solid rgba(76,124,255,0.22)",
                borderRadius: 12,
                padding: "11px 14px",
                fontSize: 14,
                background: "var(--parchment)",
                color: "var(--ink)",
              }}
              aria-label={ar ? "تصفية حسب الملف" : "Filtrer par dossier"}
            >
              <option value="">{ar ? "كل الملفات" : "Tous les dossiers"}</option>
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.reference} — {c.client_name}
                </option>
              ))}
            </select>
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>
              {ar ? "من تاريخ" : "Du"}
            </span>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              style={{
                border: "1px solid rgba(76,124,255,0.22)",
                borderRadius: 12,
                padding: "11px 14px",
                fontSize: 14,
                background: "var(--parchment)",
                color: "var(--ink)",
              }}
            />
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>
              {ar ? "إلى تاريخ" : "Au"}
            </span>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              style={{
                border: "1px solid rgba(76,124,255,0.22)",
                borderRadius: 12,
                padding: "11px 14px",
                fontSize: 14,
                background: "var(--parchment)",
                color: "var(--ink)",
              }}
            />
          </label>
          {filterCaseId && (
            <p style={{ fontSize: 12, color: "var(--ink-soft)", alignSelf: "end", paddingBottom: 8 }}>
              {ar
                ? `الرفع إلى الملف المعروض في التصفية`
                : `Upload vers le dossier du filtre actif`}
            </p>
          )}
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
          openDestinationModal(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            inputRef.current?.click();
          }
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
              ? "اختاروا الملف أولاً — ثم حدّدوا الوجهة"
              : "Choisissez d’abord le fichier — puis la destination"}
        </p>
        <p style={{ fontSize: 12, opacity: 0.9, marginTop: 4 }}>
          {ar
            ? "PDF، Word، TXT، MD، صور، صوت"
            : "PDF, Word, TXT, MD, images, audio"}
        </p>
        <div className="drop-smart-float" aria-hidden="true">
          <span className="drop-smart-ico drop-smart-ico--1">📄</span>
          <span className="drop-smart-ico drop-smart-ico--2">🖼</span>
          <span className="drop-smart-ico drop-smart-ico--3">🎙</span>
        </div>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.txt,.md,.markdown,text/plain,text/markdown,.png,.jpg,.jpeg,.webp,.wav,.mp3,.m4a,.webm,audio/*"
          className="hidden"
          style={{ display: "none" }}
          onChange={(e) => {
            openDestinationModal(e.target.files);
          }}
        />
      </div>

      {pendingFiles && pendingFiles.length > 0 && (
        <div
          className="upload-dest-overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="upload-dest-title"
          onClick={(e) => {
            if (e.target === e.currentTarget && !uploading) cancelDestinationModal();
          }}
        >
          <div className="upload-dest-card" dir={ar ? "rtl" : "ltr"}>
            <p className="upload-dest-eyebrow">{ar ? "LexHub · رفع وثيقة" : "LexHub · Upload"}</p>
            <h3 id="upload-dest-title" className="upload-dest-title">
              {ar ? "أين تريدون حفظ الملف؟" : "Où enregistrer le fichier ?"}
            </h3>
            <p className="upload-dest-sub">
              {ar
                ? "تم اختيار الملفات — اختاروا الوجهة ثم أكّدوا."
                : "Fichiers sélectionnés — choisissez la destination puis confirmez."}
            </p>
            <ul className="upload-dest-files">
              {pendingFiles.map((f) => (
                <li key={`${f.name}-${f.size}-${f.lastModified}`}>
                  <span className="upload-dest-file-ico" aria-hidden>
                    📄
                  </span>
                  <span className="upload-dest-file-name" title={f.name}>
                    {f.name}
                  </span>
                  <span className="upload-dest-file-size">{formatSize(f.size)}</span>
                </li>
              ))}
            </ul>
            <label className="upload-dest-label">
              <span>{ar ? "الوجهة" : "Destination"}</span>
              <select
                value={destChoice}
                disabled={uploading}
                onChange={(e) => setDestChoice(e.target.value)}
              >
                <option value="__none__">
                  {ar ? "بدون ملف محدد → « غير مصنف »" : "Sans dossier → « Non classé »"}
                </option>
                <option value="__new__">
                  {ar ? "＋ إنشاء ملف جديد…" : "＋ Créer un nouveau dossier…"}
                </option>
                {cases.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.reference} — {c.client_name}
                  </option>
                ))}
              </select>
            </label>
            <div className="upload-dest-actions">
              <button
                type="button"
                className="chip-btn"
                disabled={uploading}
                onClick={cancelDestinationModal}
              >
                {ar ? "إلغاء" : "Annuler"}
              </button>
              <button
                type="button"
                className="chip-btn primary"
                disabled={uploading}
                onClick={() => void confirmDestinationUpload()}
              >
                {uploading
                  ? ar
                    ? "جارٍ الرفع…"
                    : "Envoi…"
                  : ar
                    ? "تأكيد الرفع"
                    : "Confirmer l’envoi"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="doc-table">
        {loading ? (
          <p className="section-sub">{t.loading}</p>
        ) : visibleDocs.length === 0 ? (
          <p className="section-sub">{t.empty}</p>
        ) : (
          visibleDocs.map((doc) => {
            const indefinite = isProcessingStatus(doc) && typeof doc.ocr_score !== "number";
            const pct = ocrPercent(doc);
            const failed = pct < 0 || ["failed", "error"].includes((doc.status || "").toLowerCase());
            const gold = isDocx(doc) || doc.kind === "audio";
            const busy = deletingId === doc.id;
            return (
              <div key={doc.id} className="doc-row">
                <div className="doc-row-main">
                  <div className="doc-name">
                    <div
                      className="doc-file-ico"
                      style={
                        failed
                          ? { background: "rgba(185,28,28,0.12)", color: "#b91c1c" }
                          : gold
                            ? { background: "rgba(255,106,0,0.14)", color: "var(--gold)" }
                            : undefined
                      }
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      </svg>
                    </div>
                    <div>
                      <div title={doc.original_name}>{doc.original_name}</div>
                      <div className="row-sub">
                        {doc.case_reference || "—"} · {formatSize(doc.file_size)}
                      </div>
                    </div>
                  </div>
                  <div>
                    <div className={`ocr-bar${indefinite && !failed ? " ocr-bar--indeterminate" : ""}`}>
                      {indefinite && !failed ? (
                        <span className="ocr-bar__runner" />
                      ) : (
                        <span
                          style={{
                            width: `${failed ? 100 : Math.max(0, pct)}%`,
                            background: failed ? "#b91c1c" : undefined,
                            animation: "none",
                          }}
                        />
                      )}
                    </div>
                    <div className="row-sub" style={{ marginTop: 6, color: failed ? "#b91c1c" : undefined }}>
                      {progressCaption(doc, ar, failed, pct, indefinite)}
                    </div>
                  </div>
                  <div
                    className={`status-pill${pct >= 100 && !failed ? " status-pill--closed" : ""}`}
                    style={failed ? { background: "rgba(185,28,28,0.12)", color: "#b91c1c" } : undefined}
                  >
                    {statusLabel(doc, ar)}
                    {!failed && !indefinite && pct > 0 && pct < 100 ? ` · ${pct}%` : null}
                  </div>
                </div>
                <div className="row-actions doc-row-actions" role="group" aria-label={t.actions}>
                  <button
                    type="button"
                    className="btn-action"
                    onClick={() =>
                      setPreviewDoc({
                        id: doc.id,
                        name: doc.original_name,
                        mimeType: doc.mime_type,
                      })
                    }
                  >
                    {ar ? "معاينة" : "Aperçu"}
                  </button>
                  <Link
                    href={`/documents/${doc.id}`}
                    className="btn-action btn-action--primary"
                  >
                    {t.consult || (ar ? "فتح" : "Ouvrir")}
                  </Link>
                  {doc.case_id ? (
                    <Link href={`/cases/${doc.case_id}`} className="btn-action">
                      {t.openCase || (ar ? "الملف" : "Dossier")}
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
                    disabled={busy}
                    aria-label={ar ? "حذف" : "Supprimer"}
                    title={ar ? "حذف" : "Supprimer"}
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      void handleDelete(doc);
                    }}
                  >
                    <svg
                      viewBox="0 0 24 24"
                      width="16"
                      height="16"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      aria-hidden="true"
                    >
                      <path d="M3 6h18" />
                      <path d="M8 6V4h8v2" />
                      <path d="M19 6l-1 14H6L5 6" />
                      <path d="M10 11v6M14 11v6" />
                    </svg>
                    {busy
                      ? ar
                        ? "جاري الحذف…"
                        : "Suppression…"
                      : ar
                        ? "حذف"
                        : "Supprimer"}
                  </button>
                  ) : null}
                </div>
                          </div>
            );
          })
                  )}
      </div>
      <DocumentPreviewModal
        doc={previewDoc}
        open={!!previewDoc}
        onClose={() => setPreviewDoc(null)}
        ar={ar}
      />
    </AppShell>
  );
}
