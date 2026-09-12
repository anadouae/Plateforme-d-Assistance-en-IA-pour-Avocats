"use client";

import { Suspense, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  CalendarDays,
  Download,
  FileText,
  Mic,
  Pencil,
  Sparkles,
  Trash2,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { DocumentStatusBadge } from "@/components/ai/document-status-badge";
import { DocumentUpload } from "@/components/documents/document-upload";
import {
  DocumentPreviewModal,
  type DocumentPreviewTarget,
} from "@/components/documents/document-preview-modal";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  api,
  type AgendaEventItem,
  type CaseAnalysisResult,
  type CaseCommentItem,
  type CaseDetail,
  type DocumentItem,
  type TeamMember,
} from "@/lib/api";
import { useBillingCredits } from "@/store/billing-credits";
import { FadeIn } from "@/components/motion/fade-in";
import { useAuthStore } from "@/store/auth";
import { useLocaleStore, useTranslations } from "@/store/locale";
import { caseDomainLabel, caseStatusLabel, caseStatusOptions, caseDomainOptions } from "@/lib/i18n/labels";
import {
  JURISDICTION_DEGREES,
  TRIBUNAL_OPTIONS,
  indicativeDeadlineHint,
  opposingRoleFor,
  partyRoleOptions,
  suggestTribunal,
} from "@/lib/case-legal";
import {
  PROCEDURE_STATUSES,
  DECISION_TYPES,
  EXHIBIT_TYPES,
  EXHIBIT_VERSIONS,
  PRODUCED_BY,
  computeAppealDeadline,
  appealDeadlineLabel,
  defaultAppealDays,
} from "@/lib/case-judicial";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { hasActivePleaSessionFor, loadPleaSession, pleaResumeHref } from "@/lib/plea-session";
import { courtSeatLabel } from "@/lib/morocco-courts";
import { canDeleteDocument } from "@/lib/ownership";
import { StructuredSynthesis } from "@/components/ai/structured-synthesis";

type Tab = "resume" | "documents" | "activite";
type DocTypeFilter = "all" | "pdf" | "docx" | "image" | "audio" | "other";

function toDateInput(iso?: string | null) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function fromDateInput(v: string): string | null {
  if (!v.trim()) return null;
  return `${v.trim()}T12:00:00.000Z`;
}

function docTypeCategory(doc: DocumentItem): DocTypeFilter {
  const name = (doc.original_name || "").toLowerCase();
  const mime = (doc.mime_type || "").toLowerCase();
  if (doc.kind === "audio" || mime.startsWith("audio/")) return "audio";
  if (mime.includes("pdf") || name.endsWith(".pdf")) return "pdf";
  if (mime.includes("word") || name.endsWith(".docx") || name.endsWith(".doc")) return "docx";
  if (mime.startsWith("image/") || /\.(png|jpe?g|gif|webp|bmp)$/i.test(name)) return "image";
  return "other";
}

function analysisStorageKey(caseId: string) {
  return `lexhub:case-analysis:${caseId}`;
}

async function downloadDocument(
  docId: string,
  filename: string,
  onProgress?: (pct: number) => void,
) {
  await api.downloadDocument(docId, filename, onProgress);
}

export default function CaseDetailPage() {
  return (
    <Suspense fallback={<div className="flex min-h-[40vh] items-center justify-center text-sm text-slate-500">…</div>}>
      <CaseDetailInner />
    </Suspense>
  );
}

function CaseDetailInner() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const caseId = params.id as string;
  const fromPlea = searchParams.get("from") === "plea";
  const tabParam = searchParams.get("tab");
  const user = useAuthStore((s) => s.user);
  const locale = useLocaleStore((s) => s.locale);
  const t = useTranslations().app.cases;
  const ar = locale === "ar";
  const confirm = useConfirm();
  const [tab, setTab] = useState<Tab>(() =>
    tabParam === "documents" || fromPlea ? "documents" : "resume",
  );
  const [pleaReturnHref, setPleaReturnHref] = useState<string | null>(null);

  useEffect(() => {
    const snap = loadPleaSession();
    if (!snap) {
      setPleaReturnHref(null);
      return;
    }
    const sameCase = !snap.caseId || snap.caseId === caseId;
    if ((fromPlea || snap.pendingReturn) && sameCase) {
      setPleaReturnHref(pleaResumeHref(snap.templateId || "libre"));
    } else if (hasActivePleaSessionFor(caseId)) {
      setPleaReturnHref(pleaResumeHref(snap.templateId || "libre"));
    } else {
      setPleaReturnHref(null);
    }
  }, [fromPlea, caseId]);
  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [caseLoading, setCaseLoading] = useState(true);
  const [caseLoadError, setCaseLoadError] = useState("");
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [agenda, setAgenda] = useState<AgendaEventItem[]>([]);
  const [analysis, setAnalysis] = useState<CaseAnalysisResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyseError, setAnalyseError] = useState<string | null>(null);
  const [cleBusy, setCleBusy] = useState(false);
  const [cleText, setCleText] = useState<string | null>(null);
  const [cleError, setCleError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [downloadPctById, setDownloadPctById] = useState<Record<string, number>>({});
  const [previewDoc, setPreviewDoc] = useState<DocumentPreviewTarget | null>(null);
  const [docTypeFilter, setDocTypeFilter] = useState<DocTypeFilter>("all");
  const [editingCase, setEditingCase] = useState(false);
  const [editClientName, setEditClientName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editCaseType, setEditCaseType] = useState("");
  const [editStatus, setEditStatus] = useState("");
  const [editDegree, setEditDegree] = useState("");
  const [editTribunal, setEditTribunal] = useState("");
  const [editClientRole, setEditClientRole] = useState("");
  const [editClientQuality, setEditClientQuality] = useState("");
  const [editClientDomicile, setEditClientDomicile] = useState("");
  const [editOpposingName, setEditOpposingName] = useState("");
  const [editOpposingQuality, setEditOpposingQuality] = useState("");
  const [editOpposingDomicile, setEditOpposingDomicile] = useState("");
  const [editCourtFileNumber, setEditCourtFileNumber] = useState("");
  const [editJudgeName, setEditJudgeName] = useState("");
  const [editChamber, setEditChamber] = useState("");
  const [editGreffe, setEditGreffe] = useState("");
  const [editProcedureStatus, setEditProcedureStatus] = useState("ouverture");
  const [editAssistantId, setEditAssistantId] = useState("");
  const [editLastDecisionType, setEditLastDecisionType] = useState("");
  const [editLastDecisionDate, setEditLastDecisionDate] = useState("");
  const [editNotificationDate, setEditNotificationDate] = useState("");
  const [editAppealDays, setEditAppealDays] = useState(30);
  const [savingCase, setSavingCase] = useState(false);
  const [caseSaveMsg, setCaseSaveMsg] = useState<string | null>(null);
  const [comments, setComments] = useState<CaseCommentItem[]>([]);
  const [commentDraft, setCommentDraft] = useState("");
  const [commentBusy, setCommentBusy] = useState(false);
  const [assistants, setAssistants] = useState<TeamMember[]>([]);
  const [bordereauBusy, setBordereauBusy] = useState(false);
  const [docMetaDraft, setDocMetaDraft] = useState<
    Record<
      string,
      {
        inventory_number: string;
        exhibit_type: string;
        produced_by: string;
        exhibit_version: string;
        cited_in_plea: string;
      }
    >
  >({});
  const [docMetaSaving, setDocMetaSaving] = useState<string | null>(null);

  const canUseAI = user?.role !== "assistant_juridique";
  const dateLocale = ar ? "ar-MA" : "fr-FR";

  function load() {
    setCaseLoading(true);
    setCaseLoadError("");
    const watchdog = window.setTimeout(() => {
      setCaseLoading(false);
      setCaseLoadError(
        ar
          ? "التحميل يستغرق وقتاً طويلاً. تحققوا من الشبكة ثم أعيدوا المحاولة."
          : "Le chargement met trop de temps. Vérifiez la connexion puis réessayez.",
      );
    }, 18000);
    api
      .getCase(caseId)
      .then((data) => {
        setCaseData(data);
        setCaseLoadError("");
      })
      .catch((err) => {
        setCaseData(null);
        setCaseLoadError(
          err instanceof Error
            ? err.message
            : ar
              ? "تعذّر فتح الملف."
              : "Impossible d’ouvrir le dossier.",
        );
      })
      .finally(() => {
        window.clearTimeout(watchdog);
        setCaseLoading(false);
      });
    api.getDocuments(caseId).then(setDocuments).catch(() => setDocuments([]));
    api.getAgenda(caseId).then(setAgenda).catch(() => setAgenda([]));
    api.listCaseComments(caseId).then(setComments).catch(() => setComments([]));
  }

  useEffect(() => {
    load();
    try {
      const raw = localStorage.getItem(analysisStorageKey(caseId));
      if (raw) setAnalysis(JSON.parse(raw) as CaseAnalysisResult);
    } catch {
      /* ignore */
    }
    api.listAssistants().then(setAssistants).catch(() => setAssistants([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId]);

  useEffect(() => {
    if (!caseData) return;
    setEditClientName(caseData.client_name);
    setEditDescription(caseData.description || "");
    setEditCaseType(caseData.case_type);
    setEditStatus(caseData.status);
    setEditDegree(caseData.jurisdiction_degree || "premiere_instance");
    setEditTribunal(caseData.tribunal || suggestTribunal(caseData.case_type, caseData.jurisdiction_degree || "premiere_instance"));
    setEditClientRole(caseData.client_role || partyRoleOptions(caseData.case_type)[0]?.value || "demandeur");
    setEditClientQuality(caseData.client_quality || "");
    setEditClientDomicile(caseData.client_domicile || "");
    setEditOpposingName(caseData.opposing_name || "");
    setEditOpposingQuality(caseData.opposing_quality || "");
    setEditOpposingDomicile(caseData.opposing_domicile || "");
    setEditCourtFileNumber(caseData.court_file_number || "");
    setEditJudgeName(caseData.judge_name || "");
    setEditChamber(caseData.chamber || "");
    setEditGreffe(caseData.greffe || "");
    setEditProcedureStatus(caseData.procedure_status || "ouverture");
    setEditAssistantId(caseData.assistant_id || "");
    setEditLastDecisionType(caseData.last_decision_type || "");
    setEditLastDecisionDate(toDateInput(caseData.last_decision_date));
    setEditNotificationDate(toDateInput(caseData.notification_date));
    setEditAppealDays(
      caseData.appeal_deadline_days ??
        defaultAppealDays(caseData.jurisdiction_degree),
    );
  }, [caseData]);

  useEffect(() => {
    setDocMetaDraft((prev) => {
      const next = { ...prev };
      for (const doc of documents) {
        if (next[doc.id]) continue;
        next[doc.id] = {
          inventory_number:
            doc.inventory_number != null ? String(doc.inventory_number) : "",
          exhibit_type: doc.exhibit_type || "",
          produced_by: doc.produced_by || "",
          exhibit_version: doc.exhibit_version || "",
          cited_in_plea: doc.cited_in_plea || "",
        };
      }
      return next;
    });
  }, [documents]);

  async function saveCaseEdits() {
    if (!caseData) return;
    setSavingCase(true);
    setCaseSaveMsg(null);
    const notifIso = fromDateInput(editNotificationDate);
    const days = Math.max(1, Number(editAppealDays) || defaultAppealDays(editDegree));
    const computedDeadline = computeAppealDeadline(notifIso, days);
    try {
      const updated = await api.updateCase(caseId, {
        client_name: editClientName.trim(),
        description: editDescription.trim() || undefined,
        case_type: editCaseType,
        status: editStatus,
        jurisdiction_degree: editDegree || undefined,
        tribunal: editTribunal || undefined,
        client_role: editClientRole || undefined,
        client_quality: editClientQuality.trim() || undefined,
        client_domicile: editClientDomicile.trim() || undefined,
        opposing_name: editOpposingName.trim() || undefined,
        opposing_role: opposingRoleFor(editClientRole),
        opposing_quality: editOpposingQuality.trim() || undefined,
        opposing_domicile: editOpposingDomicile.trim() || undefined,
        court_file_number: editCourtFileNumber.trim() || undefined,
        judge_name: editJudgeName.trim() || undefined,
        chamber: editChamber.trim() || undefined,
        greffe: editGreffe.trim() || undefined,
        procedure_status: editProcedureStatus || undefined,
        assistant_id: editAssistantId.trim() || null,
        last_decision_type: editLastDecisionType || undefined,
        last_decision_date: fromDateInput(editLastDecisionDate),
        notification_date: notifIso,
        appeal_deadline_days: days,
        appeal_deadline_at: computedDeadline
          ? computedDeadline.toISOString()
          : null,
      });
      setCaseData(updated);
      setEditingCase(false);
      setCaseSaveMsg(t.caseSaved);
    } catch {
      setCaseSaveMsg(t.caseSaveError);
    } finally {
      setSavingCase(false);
    }
  }

  function resetEditForm() {
    if (!caseData) return;
    setEditingCase(false);
    setEditClientName(caseData.client_name);
    setEditDescription(caseData.description || "");
    setEditCaseType(caseData.case_type);
    setEditStatus(caseData.status);
    setEditDegree(caseData.jurisdiction_degree || "premiere_instance");
    setEditTribunal(
      caseData.tribunal ||
        suggestTribunal(
          caseData.case_type,
          caseData.jurisdiction_degree || "premiere_instance",
        ),
    );
    setEditClientRole(
      caseData.client_role ||
        partyRoleOptions(caseData.case_type)[0]?.value ||
        "demandeur",
    );
    setEditClientQuality(caseData.client_quality || "");
    setEditClientDomicile(caseData.client_domicile || "");
    setEditOpposingName(caseData.opposing_name || "");
    setEditOpposingQuality(caseData.opposing_quality || "");
    setEditOpposingDomicile(caseData.opposing_domicile || "");
    setEditCourtFileNumber(caseData.court_file_number || "");
    setEditJudgeName(caseData.judge_name || "");
    setEditChamber(caseData.chamber || "");
    setEditGreffe(caseData.greffe || "");
    setEditProcedureStatus(caseData.procedure_status || "ouverture");
    setEditAssistantId(caseData.assistant_id || "");
    setEditLastDecisionType(caseData.last_decision_type || "");
    setEditLastDecisionDate(toDateInput(caseData.last_decision_date));
    setEditNotificationDate(toDateInput(caseData.notification_date));
    setEditAppealDays(
      caseData.appeal_deadline_days ??
        defaultAppealDays(caseData.jurisdiction_degree),
    );
    setCaseSaveMsg(null);
  }

  const liveAppealPreview = appealDeadlineLabel(
    computeAppealDeadline(
      fromDateInput(editNotificationDate),
      Math.max(1, Number(editAppealDays) || 30),
    ),
    ar,
  );

  const storedAppealLabel = appealDeadlineLabel(
    caseData?.appeal_deadline_at
      ? new Date(caseData.appeal_deadline_at)
      : computeAppealDeadline(
          caseData?.notification_date,
          caseData?.appeal_deadline_days ??
            defaultAppealDays(caseData?.jurisdiction_degree),
        ),
    ar,
  );

  const filteredDocuments =
    docTypeFilter === "all"
      ? documents
      : documents.filter((doc) => docTypeCategory(doc) === docTypeFilter);

  async function runAnalysis() {
    setAnalyzing(true);
    setAnalyseError(null);
    const watchdog = window.setTimeout(() => {
      setAnalyzing(false);
      setAnalyseError(
        t.analyseTimeout ||
          (ar
            ? "التحليل توقف — أعد المحاولة."
            : "Analyse interrompue — réessayez."),
      );
    }, 50_000);
    try {
      const result = await api.analyseCase(caseId);
      setAnalysis(result);
      void useBillingCredits.getState().notifySpend("analyse");
      try {
        localStorage.setItem(analysisStorageKey(caseId), JSON.stringify(result));
      } catch {
        /* quota */
      }
    } catch (e) {
      const raw = e instanceof Error ? e.message : "";
      const msg =
        /timeout|aborted|المهلة|يستجيب|اتصال|joindre|délai|internet|الإنترنت/i.test(raw) ||
        (e instanceof Error && (e.name === "TimeoutError" || e.name === "AbortError"))
          ? t.analyseTimeout
          : raw || t.analyseFail;
      setAnalyseError(msg);
    } finally {
      window.clearTimeout(watchdog);
      setAnalyzing(false);
    }
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "resume", label: t.tabResume },
    { id: "documents", label: t.tabDocuments },
    { id: "activite", label: t.tabActivity },
  ];

  if (caseLoading && !caseData) {
    return (
      <AppShell>
        <div dir={ar ? "rtl" : "ltr"} className="flex items-center gap-2 text-slate-500">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-sanad-blue border-t-transparent" />
          {t.loadingCase}
        </div>
      </AppShell>
    );
  }

  if (!caseData) {
    return (
      <AppShell>
        <div dir={ar ? "rtl" : "ltr"} className="space-y-3">
          <p className="text-sm text-red-600">
            {caseLoadError || (ar ? "تعذّر فتح الملف." : "Impossible d’ouvrir le dossier.")}
          </p>
          <Button type="button" variant="outline" onClick={() => load()}>
            {ar ? "إعادة المحاولة" : "Réessayer"}
          </Button>
          <Link href="/cases" className="block text-sm text-sanad-blue hover:underline">
            {t.backToCases}
          </Link>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div dir={ar ? "rtl" : "ltr"}>
      <FadeIn className="space-y-6">
        <div>
          <Link
            href="/cases"
            className="mb-2 inline-flex items-center gap-1 text-sm text-sanad-blue hover:underline"
          >
            <ArrowLeft className={`h-4 w-4 ${ar ? "rotate-180" : ""}`} />
            {t.backToCases}
          </Link>
          {(fromPlea || pleaReturnHref) && pleaReturnHref && canUseAI ? (
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-sanad-blue/20 bg-sanad-blue/5 px-4 py-3">
              <p className="text-sm text-sanad-navy">
                {ar
                  ? "ورشة المرافعة محفوظة — يمكنكم العودة دون فقدان الإملاء أو النص."
                  : "Atelier plaidoirie en cours — reprenez sans perdre dictée ni texte."}
              </p>
              <Button
                type="button"
                size="sm"
                className="shrink-0"
                onClick={() => router.push(pleaReturnHref)}
              >
                <ArrowLeft className={`h-4 w-4 ${ar ? "rotate-180" : ""}`} />
                {ar ? "العودة إلى المرافعة" : "Reprendre la plaidoirie"}
              </Button>
            </div>
          ) : null}
          <h1 className="font-display text-2xl font-semibold text-sanad-navy">
            {caseData.reference} — {caseData.client_name}
          </h1>
          <p className="text-sm text-slate-500">
            <span className="rounded-md bg-sanad-gold/15 px-1.5 py-0.5 font-medium text-sanad-navy">
              {caseDomainLabel(caseData.case_type, locale)}
            </span>{" "}
            · {caseStatusLabel(caseData.status, locale)}
          </p>
        </div>

        <div className="flex gap-1 overflow-x-auto border-b border-sanad-border">
          {tabs.map((tabItem) => (
            <button
              key={tabItem.id}
              type="button"
              className={`whitespace-nowrap px-4 py-2.5 text-sm font-medium transition-colors ${
                tab === tabItem.id
                  ? "border-b-2 border-sanad-blue text-sanad-blue"
                  : "text-slate-500 hover:text-sanad-slate"
              }`}
              onClick={() => setTab(tabItem.id)}
            >
              {tabItem.label}
            </button>
          ))}
        </div>

        {tab === "resume" && (
          <div className="space-y-6">
            <Card>
              <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
                <CardTitle>{t.infoTitle}</CardTitle>
                {!editingCase ? (
                  <Button type="button" size="sm" variant="outline" onClick={() => setEditingCase(true)}>
                    <Pencil className="h-4 w-4" />
                    {t.editCase}
                  </Button>
                ) : null}
              </CardHeader>
              <CardContent className="grid gap-3 text-sm sm:grid-cols-2">
                {caseSaveMsg ? (
                  <p className="sm:col-span-2 text-sm font-medium text-sanad-navy">{caseSaveMsg}</p>
                ) : null}
                {editingCase ? (
                  <>
                    <div className="sm:col-span-2">
                      <label className="mb-1 block text-slate-500">{t.client}</label>
                      <input
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editClientName}
                        onChange={(e) => setEditClientName(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-slate-500">{t.domain}</label>
                      <select
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editCaseType}
                        onChange={(e) => setEditCaseType(e.target.value)}
                      >
                        {caseDomainOptions(locale).map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="mb-1 block text-slate-500">{t.status}</label>
                      <select
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editStatus}
                        onChange={(e) => setEditStatus(e.target.value)}
                      >
                        {caseStatusOptions(locale).map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="mb-1 block text-slate-500">
                        {ar ? "درجة التقاضي" : "Degré de juridiction"}
                      </label>
                      <select
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editDegree}
                        onChange={(e) => {
                          const d = e.target.value;
                          setEditDegree(d);
                          setEditTribunal(suggestTribunal(editCaseType, d));
                          setEditAppealDays(defaultAppealDays(d));
                        }}
                      >
                        {JURISDICTION_DEGREES.map((d) => (
                          <option key={d.value} value={d.value}>
                            {ar ? d.ar : d.fr}
                          </option>
                        ))}
                      </select>
                      <p className="mt-1 text-[11px] text-slate-500">
                        {indicativeDeadlineHint(editDegree, !ar)}
                      </p>
                    </div>
                    <div>
                      <label className="mb-1 block text-slate-500">
                        {ar ? "المحكمة" : "Tribunal"}
                      </label>
                      <select
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editTribunal}
                        onChange={(e) => setEditTribunal(e.target.value)}
                      >
                        {TRIBUNAL_OPTIONS.map((tOpt) => (
                          <option key={tOpt.value} value={tOpt.value}>
                            {ar ? tOpt.ar : tOpt.fr}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="mb-1 block text-slate-500">
                        {ar ? "رقم الملف (ر.ج)" : "N° RG tribunal"}
                      </label>
                      <input
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editCourtFileNumber}
                        onChange={(e) => setEditCourtFileNumber(e.target.value)}
                        placeholder={ar ? "مثال: 1234/2024" : "ex. 1234/2024"}
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-slate-500">
                        {ar ? "حالة المسطرة" : "Statut procédure"}
                      </label>
                      <select
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editProcedureStatus}
                        onChange={(e) => setEditProcedureStatus(e.target.value)}
                      >
                        {PROCEDURE_STATUSES.map((s) => (
                          <option key={s.value} value={s.value}>
                            {ar ? s.ar : s.fr}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="mb-1 block text-slate-500">
                        {ar ? "القاضي" : "Juge"}
                      </label>
                      <input
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editJudgeName}
                        onChange={(e) => setEditJudgeName(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-slate-500">
                        {ar ? "الغرفة" : "Chambre"}
                      </label>
                      <input
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editChamber}
                        onChange={(e) => setEditChamber(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-slate-500">
                        {ar ? "كتابة الضبط" : "Greffe"}
                      </label>
                      <input
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editGreffe}
                        onChange={(e) => setEditGreffe(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-slate-500">
                        {ar ? "المساعد المعيّن" : "Assistant assigné"}
                      </label>
                      <select
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editAssistantId}
                        onChange={(e) => setEditAssistantId(e.target.value)}
                      >
                        <option value="">{ar ? "— بدون —" : "— Aucun —"}</option>
                        {assistants.map((a) => (
                          <option key={a.id} value={a.id}>
                            {a.full_name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="mb-1 block text-slate-500">
                        {ar ? "نوع آخر قرار" : "Dernière décision"}
                      </label>
                      <select
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editLastDecisionType}
                        onChange={(e) => setEditLastDecisionType(e.target.value)}
                      >
                        <option value="">{ar ? "— غير محدد —" : "— Non renseigné —"}</option>
                        {DECISION_TYPES.map((d) => (
                          <option key={d.value} value={d.value}>
                            {ar ? d.ar : d.fr}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="mb-1 block text-slate-500">
                        {ar ? "تاريخ القرار" : "Date de la décision"}
                      </label>
                      <input
                        type="date"
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editLastDecisionDate}
                        onChange={(e) => setEditLastDecisionDate(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-slate-500">
                        {ar ? "تاريخ التبليغ" : "Date de notification"}
                      </label>
                      <input
                        type="date"
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editNotificationDate}
                        onChange={(e) => setEditNotificationDate(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-slate-500">
                        {ar ? "أجل الطعن (أيام)" : "Délai de recours (jours)"}
                      </label>
                      <input
                        type="number"
                        min={1}
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editAppealDays}
                        onChange={(e) =>
                          setEditAppealDays(Math.max(1, Number(e.target.value) || 1))
                        }
                      />
                    </div>
                    {liveAppealPreview ? (
                      <div
                        className={`sm:col-span-2 rounded-lg border px-3 py-2 text-xs ${
                          liveAppealPreview.urgent
                            ? "border-amber-300 bg-amber-50 text-amber-950"
                            : "border-sanad-border bg-sanad-cream/40 text-sanad-navy"
                        }`}
                      >
                        {liveAppealPreview.text}
                      </div>
                    ) : (
                      <p className="sm:col-span-2 text-[11px] text-slate-500">
                        {ar
                          ? "أدخلوا تاريخ التبليغ لمعاينة أجل الطعن."
                          : "Saisissez la date de notification pour prévisualiser le délai de recours."}
                      </p>
                    )}
                    <div>
                      <label className="mb-1 block text-slate-500">
                        {ar ? "دور الموكل" : "Rôle du client"}
                      </label>
                      <select
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editClientRole}
                        onChange={(e) => setEditClientRole(e.target.value)}
                      >
                        {partyRoleOptions(editCaseType).map((r) => (
                          <option key={r.value} value={r.value}>
                            {ar ? r.ar : r.fr}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="mb-1 block text-slate-500">
                        {ar ? "صفة الموكل" : "Qualité"}
                      </label>
                      <input
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editClientQuality}
                        onChange={(e) => setEditClientQuality(e.target.value)}
                      />
                    </div>
                    <div className="sm:col-span-2">
                      <label className="mb-1 block text-slate-500">
                        {ar ? "موطن الموكل" : "Domicile / siège"}
                      </label>
                      <input
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editClientDomicile}
                        onChange={(e) => setEditClientDomicile(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-slate-500">
                        {ar ? "الطرف المقابل" : "Partie adverse"}
                      </label>
                      <input
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editOpposingName}
                        onChange={(e) => setEditOpposingName(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-slate-500">
                        {ar ? "صفة المقابل" : "Qualité adverse"}
                      </label>
                      <input
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editOpposingQuality}
                        onChange={(e) => setEditOpposingQuality(e.target.value)}
                      />
                    </div>
                    <div className="sm:col-span-2">
                      <label className="mb-1 block text-slate-500">
                        {ar ? "موطن المقابل" : "Domicile adverse"}
                      </label>
                      <input
                        className="w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editOpposingDomicile}
                        onChange={(e) => setEditOpposingDomicile(e.target.value)}
                      />
                    </div>
                    <div className="sm:col-span-2">
                      <label className="mb-1 block text-slate-500">{t.description}</label>
                      <textarea
                        className="min-h-[88px] w-full rounded-lg border border-sanad-border px-3 py-2"
                        value={editDescription}
                        onChange={(e) => setEditDescription(e.target.value)}
                      />
                    </div>
                    <div className="flex flex-wrap gap-2 sm:col-span-2">
                      <Button type="button" size="sm" disabled={savingCase} onClick={() => void saveCaseEdits()}>
                        {savingCase ? "…" : t.saveCase}
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        disabled={savingCase}
                        onClick={() => resetEditForm()}
                      >
                        {t.cancelEdit}
                      </Button>
                    </div>
                  </>
                ) : (
                  <>
                    <div>
                      <span className="text-slate-500">{t.client} :</span> {caseData.client_name}
                    </div>
                    <div>
                      <span className="text-slate-500">{t.responsible} :</span>{" "}
                      {caseData.responsible_name}
                    </div>
                    <div>
                      <span className="text-slate-500">{t.openedAt} :</span>{" "}
                      {new Date(caseData.opened_at).toLocaleDateString(dateLocale)}
                    </div>
                    <div>
                      <span className="text-slate-500">{t.status} :</span>{" "}
                      {caseStatusLabel(caseData.status, locale)}
                    </div>
                    <div>
                      <span className="text-slate-500">{t.domain} :</span>{" "}
                      {caseDomainLabel(caseData.case_type, locale)}
                    </div>
                    {caseData.jurisdiction_degree ? (
                      <div>
                        <span className="text-slate-500">{ar ? "الدرجة" : "Degré"} :</span>{" "}
                        {JURISDICTION_DEGREES.find((d) => d.value === caseData.jurisdiction_degree)?.[
                          ar ? "ar" : "fr"
                        ] || caseData.jurisdiction_degree}
                      </div>
                    ) : null}
                    {caseData.tribunal ? (
                      <div>
                        <span className="text-slate-500">{ar ? "المحكمة" : "Tribunal"} :</span>{" "}
                        {courtSeatLabel(caseData.tribunal, ar) ||
                          TRIBUNAL_OPTIONS.find((t) => t.value === caseData.tribunal)?.[
                            ar ? "ar" : "fr"
                          ] ||
                          caseData.tribunal}
                      </div>
                    ) : null}
                    {caseData.court_file_number ? (
                      <div>
                        <span className="text-slate-500">{ar ? "ر.ج" : "N° RG"} :</span>{" "}
                        {caseData.court_file_number}
                      </div>
                    ) : null}
                    {caseData.procedure_status ? (
                      <div>
                        <span className="text-slate-500">
                          {ar ? "المسطرة" : "Procédure"} :
                        </span>{" "}
                        {PROCEDURE_STATUSES.find((s) => s.value === caseData.procedure_status)?.[
                          ar ? "ar" : "fr"
                        ] || caseData.procedure_status}
                      </div>
                    ) : null}
                    {caseData.judge_name ? (
                      <div>
                        <span className="text-slate-500">{ar ? "القاضي" : "Juge"} :</span>{" "}
                        {caseData.judge_name}
                      </div>
                    ) : null}
                    {caseData.chamber ? (
                      <div>
                        <span className="text-slate-500">{ar ? "الغرفة" : "Chambre"} :</span>{" "}
                        {caseData.chamber}
                      </div>
                    ) : null}
                    {caseData.greffe ? (
                      <div>
                        <span className="text-slate-500">{ar ? "كتابة الضبط" : "Greffe"} :</span>{" "}
                        {caseData.greffe}
                      </div>
                    ) : null}
                    {caseData.assistant_id ? (
                      <div>
                        <span className="text-slate-500">
                          {ar ? "المساعد" : "Assistant"} :
                        </span>{" "}
                        {assistants.find((a) => a.id === caseData.assistant_id)?.full_name ||
                          caseData.assistant_id}
                      </div>
                    ) : null}
                    {caseData.last_decision_type || caseData.last_decision_date ? (
                      <div>
                        <span className="text-slate-500">
                          {ar ? "آخر قرار" : "Dernière décision"} :
                        </span>{" "}
                        {DECISION_TYPES.find((d) => d.value === caseData.last_decision_type)?.[
                          ar ? "ar" : "fr"
                        ] || caseData.last_decision_type || "—"}
                        {caseData.last_decision_date
                          ? ` · ${new Date(caseData.last_decision_date).toLocaleDateString(dateLocale)}`
                          : ""}
                      </div>
                    ) : null}
                    {caseData.notification_date ? (
                      <div>
                        <span className="text-slate-500">
                          {ar ? "التبليغ" : "Notification"} :
                        </span>{" "}
                        {new Date(caseData.notification_date).toLocaleDateString(dateLocale)}
                      </div>
                    ) : null}
                    {storedAppealLabel ? (
                      <div
                        className={`sm:col-span-2 rounded-lg border px-3 py-2 text-xs ${
                          storedAppealLabel.urgent
                            ? "border-amber-300 bg-amber-50 text-amber-950"
                            : "border-sanad-border bg-sanad-cream/40 text-sanad-navy"
                        }`}
                      >
                        {storedAppealLabel.text}
                      </div>
                    ) : null}
                    {caseData.client_role ? (
                      <div>
                        <span className="text-slate-500">{ar ? "دور الموكل" : "Rôle"} :</span>{" "}
                        {partyRoleOptions(caseData.case_type).find(
                          (r) => r.value === caseData.client_role,
                        )?.[ar ? "ar" : "fr"] || caseData.client_role}
                      </div>
                    ) : null}
                    {caseData.client_domicile ? (
                      <div className="sm:col-span-2">
                        <span className="text-slate-500">{ar ? "الموطن" : "Domicile"} :</span>{" "}
                        {caseData.client_domicile}
                      </div>
                    ) : null}
                    {caseData.opposing_name ? (
                      <div className="sm:col-span-2">
                        <span className="text-slate-500">{ar ? "المقابل" : "Adverse"} :</span>{" "}
                        {caseData.opposing_name}
                        {caseData.opposing_domicile ? ` — ${caseData.opposing_domicile}` : ""}
                      </div>
                    ) : null}
                    {caseData.jurisdiction_degree ? (
                      <div className="sm:col-span-2 text-[11px] text-slate-500">
                        {indicativeDeadlineHint(caseData.jurisdiction_degree, !ar)}
                      </div>
                    ) : null}
                    {caseData.description ? (
                      <div className="sm:col-span-2">
                        <span className="text-slate-500">{t.description} :</span>{" "}
                        {caseData.description}
                      </div>
                    ) : null}
                  </>
                )}
              </CardContent>
            </Card>

            <Card className="border-sanad-gold/25 shadow-luxe">
              <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Mic className="h-5 w-5 text-sanad-gold" />
                  {ar ? "المرافعة المرتبطة" : "Plaidoirie liée"}
                </CardTitle>
                {canUseAI ? (
                  <Link
                    href={
                      pleaReturnHref ||
                      `/redaction/libre?caseId=${encodeURIComponent(caseId)}&fresh=1`
                    }
                  >
                    <Button size="sm" variant="outline">
                      {pleaReturnHref
                        ? ar
                          ? "العودة إلى الورشة"
                          : "Reprendre l’atelier"
                        : ar
                          ? "فتح التحرير"
                          : "Ouvrir la rédaction"}
                    </Button>
                  </Link>
                ) : null}
              </CardHeader>
              <CardContent className="text-sm text-slate-600">
                {canUseAI
                  ? ar
                    ? "أنشئ أو راجع مرافعة لهذا الملف من مساحة التحرير. مكتبة المرافعات المنجزة مع فلاتر مفصّلة ستُضاف لاحقاً."
                    : "Créez ou révisez une plaidoirie pour ce dossier depuis la rédaction. Une bibliothèque filtrable (type, date…) viendra ensuite."
                  : ar
                    ? "المساعد يرى حالة الملف والوثائق. صياغة المرافعة وتصديرها من اختصاص المحامي أو مسؤول المكتب."
                    : "L’assistant voit le dossier et les pièces. La rédaction / export de plaidoirie reste réservée à l’avocat ou à l’admin cabinet."}
              </CardContent>
            </Card>

            <Card className="border-sanad-gold/25 shadow-luxe">
              <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <CalendarDays className="h-5 w-5 text-sanad-gold" />
                  {t.linkedPlanning}
                </CardTitle>
                <Link href="/agenda">
                  <Button size="sm" variant="outline">
                    {t.openPlanning}
                  </Button>
                </Link>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {agenda.length === 0 ? (
                  <p className="text-slate-500">{t.noEvents}</p>
                ) : (
                  <ul className="divide-y divide-sanad-border">
                    {agenda.map((e) => (
                      <li
                        key={e.id}
                        className="flex flex-wrap items-center justify-between gap-2 py-2"
                      >
                        <div>
                          <p className="font-medium text-sanad-navy">{e.title}</p>
                          <p className="text-xs text-slate-500">
                            {e.event_type} · {new Date(e.starts_at).toLocaleString(dateLocale)}
                          </p>
                        </div>
                        {e.case_id ? (
                          <Link href={`/cases/${e.case_id}`} className="text-xs text-sanad-blue hover:underline">
                            {ar ? "الملف" : "Dossier"}
                          </Link>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            {canUseAI && (
              <Card>
                <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-sanad-blue" />
                    {t.aiAnalysis}
                  </CardTitle>
                  <div className="flex flex-wrap items-center gap-2">
                    {analyzing ? (
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => {
                          setAnalyzing(false);
                          setAnalyseError(
                            ar ? "تم إيقاف التحليل." : "Analyse annulée.",
                          );
                        }}
                      >
                        {ar ? "إيقاف" : "Annuler"}
                      </Button>
                    ) : null}
                    <Button
                      type="button"
                      onClick={() => void runAnalysis()}
                      disabled={analyzing || documents.length === 0}
                    >
                      {analyzing ? t.analyzing : t.analyzeCase}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4 text-sm">
                  <p className="rounded-lg border border-amber-200/80 bg-amber-50/70 px-3 py-2 text-xs text-amber-950">
                    {ar
                      ? "للمراجعة — غير معتمد كرأي قانوني"
                      : "À relire — non validé comme avis juridique"}
                  </p>
                  {documents.length === 0 && (
                    <p className="text-slate-500">{t.needDocs}</p>
                  )}
                  {analyzing && (
                    <p className="rounded-lg border border-sanad-gold/30 bg-sanad-cream/50 px-3 py-2 text-xs text-sanad-navy">
                      {ar
                        ? "التحليل قد يستغرق حتى دقيقة — لا تغلق الصفحة."
                        : "L’analyse peut prendre jusqu’à 1 minute — ne fermez pas la page."}
                    </p>
                  )}
                  {analyseError && <p className="text-red-600">{analyseError}</p>}
                  {analysis && (
                    <div className="space-y-4">
                      <p className="text-xs font-semibold uppercase tracking-wide text-sanad-green">
                        {t.lastAnalysis}
                      </p>
                      <StructuredSynthesis text={analysis.summary} />
                      <div className="grid gap-3 sm:grid-cols-2">
                        <div>
                          <p className="font-medium text-sanad-slate">{t.parties}</p>
                          <ul className="mt-1 list-disc ps-5 text-slate-600">
                            {analysis.parties.map((p) => (
                              <li key={p}>{p}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <p className="font-medium text-sanad-slate">{t.keyDates}</p>
                          <ul className="mt-1 list-disc ps-5 text-slate-600">
                            {analysis.key_dates.map((d) => (
                              <li key={d}>{d}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <p className="font-medium text-sanad-slate">{t.risks}</p>
                          <ul className="mt-1 list-disc ps-5 text-slate-600">
                            {analysis.risks_and_deadlines.map((r) => (
                              <li key={r}>{r}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <p className="font-medium text-sanad-slate">{t.checklist}</p>
                          <ul className="mt-1 list-disc ps-5 text-slate-600">
                            {analysis.checklist.map((c) => (
                              <li key={c}>{c}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                      <p className="text-xs text-slate-400">
                        {t.confidence} {analysis.confidence_score}% · {analysis.disclaimer}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {canUseAI && (
              <Card>
                <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-sanad-navy" />
                    {ar ? "مذكرة المرافعة (clé de barre)" : "Clé de barre — fiche orale"}
                  </CardTitle>
                  <Button
                    type="button"
                    variant="outline"
                    disabled={cleBusy || documents.length === 0}
                    onClick={() => {
                      setCleBusy(true);
                      setCleError(null);
                      void api
                        .generateCleDeBarre(caseId)
                        .then((res) => {
                          setCleText(res.cle_de_barre);
                          void useBillingCredits.getState().notifySpend("cle_de_barre");
                        })
                        .catch((err) =>
                          setCleError(
                            err instanceof Error
                              ? err.message
                              : ar
                                ? "تعذر إنشاء المذكرة"
                                : "Impossible de générer la clé de barre (quota mensuel atteint ou service indisponible).",
                          ),
                        )
                        .finally(() => setCleBusy(false));
                    }}
                  >
                    {cleBusy
                      ? ar
                        ? "جاري الإعداد…"
                        : "Génération…"
                      : ar
                        ? "إعداد من القطع"
                        : "Préparer depuis les pièces"}
                  </Button>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <p className="text-slate-600">
                    {ar
                      ? "بطاقة شفهية للجلسة: وقائع، وسائل، طلبات — تُحضَّر من قطع الملف. ليست المرافعة المكتوبة."
                      : "Fiche orale d’audience (faits, moyens, demandes) préparée à partir des pièces. Ce n’est pas la plaidoirie écrite de l’atelier."}
                  </p>
                  {cleError ? <p className="text-red-600">{cleError}</p> : null}
                  {cleText ? (
                    <StructuredSynthesis text={cleText} className="max-h-[28rem] overflow-auto" />
                  ) : null}
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {tab === "documents" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>{t.importDoc}</CardTitle>
              </CardHeader>
              <CardContent>
                <DocumentUpload
                  caseId={caseId}
                  onUpload={(cid, file) => api.uploadDocument(cid, file)}
                  onUploaded={load}
                />
              </CardContent>
            </Card>

            <div className="rounded-xl border border-sanad-blue/15 bg-white px-4 py-3 text-sm text-slate-700">
              <p className="font-semibold text-sanad-navy">
                {ar ? "ماذا تعني حقول القطعة؟" : "À quoi servent les champs de la pièce ?"}
              </p>
              <ul className="mt-2 space-y-1 text-[13px] leading-relaxed text-slate-600">
                <li>
                  <strong>{ar ? "رقم القطعة" : "N° pièce"}</strong>
                  {ar
                    ? " — ترتيب الوثيقة في الملف (1، 2، 3) كما في بوردررو القطع."
                    : " — l’ordre dans le dossier (1, 2, 3), comme sur un bordereau."}
                </li>
                <li>
                  <strong>{ar ? "النوع" : "Type"}</strong>
                  {ar
                    ? " — طبيعة الوثيقة: عقد، هوية، محضر، فاتورة…"
                    : " — nature du document : contrat, identité, PV, facture…"}
                </li>
                <li>
                  <strong>{ar ? "المنتج" : "Producteur"}</strong>
                  {ar
                    ? " — من أحضر الوثيقة: موكلنا، الخصم، المحكمة أو طرف ثالث."
                    : " — qui a fourni le document : votre client, la partie adverse, le tribunal ou un tiers."}
                </li>
                <li>
                  <strong>{ar ? "النسخة" : "Version"}</strong>
                  {ar
                    ? " — أصل، صورة أو ترجمة."
                    : " — original, copie ou traduction."}
                </li>
                <li>
                  <strong>{ar ? "المرجع في المرافعة" : "Réf. dans la plaidoirie"}</strong>
                  {ar
                    ? " — اختياري. العبارة التي ستذكرونها شفهياً (« القطعة 2 — عقد الزواج »)."
                    : " — facultatif. La mention que vous citerez à l’audience (« pièce 2 — acte de mariage »)."}
                </li>
              </ul>
            </div>

            <Card>
              <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <CardTitle>
                  {t.docsCount} ({filteredDocuments.length}
                  {docTypeFilter !== "all" ? ` / ${documents.length}` : ""})
                </CardTitle>
                <div className="flex flex-wrap items-center gap-2">
                  <select
                    className="rounded-lg border border-sanad-border px-3 py-2 text-sm"
                    value={docTypeFilter}
                    onChange={(e) => setDocTypeFilter(e.target.value as DocTypeFilter)}
                    aria-label={ar ? "تصفية نوع المرفق" : "Filtrer par type de pièce"}
                  >
                    <option value="all">{t.docFilterAll}</option>
                    <option value="pdf">{t.docFilterPdf}</option>
                    <option value="docx">{t.docFilterDocx}</option>
                    <option value="image">{t.docFilterImage}</option>
                    <option value="audio">{t.docFilterAudio}</option>
                    <option value="other">{t.docFilterOther}</option>
                  </select>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    disabled={bordereauBusy || documents.length === 0}
                    onClick={() => {
                      setBordereauBusy(true);
                      void api
                        .exportBordereau(caseId)
                        .catch(async (err) => {
                          await confirm({
                            title:
                              err instanceof Error
                                ? err.message
                                : ar
                                  ? "تعذّر تصدير الجدول."
                                  : "Export du bordereau impossible.",
                            confirmLabel: ar ? "حسناً" : "OK",
                          });
                        })
                        .finally(() => setBordereauBusy(false));
                    }}
                  >
                    {bordereauBusy
                      ? "…"
                      : ar
                        ? "تصدير جدول القطع"
                        : "Exporter bordereau"}
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="divide-y divide-sanad-border">
                {filteredDocuments.length === 0 ? (
                  <p className="py-4 text-center text-slate-400">{t.noDocs}</p>
                ) : (
                  filteredDocuments.map((doc) => {
                    const meta = docMetaDraft[doc.id] || {
                      inventory_number: "",
                      exhibit_type: "",
                      produced_by: "",
                      exhibit_version: "",
                      cited_in_plea: "",
                    };
                    return (
                    <div
                      key={doc.id}
                      className="space-y-3 py-4 first:pt-0"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="flex min-w-0 items-start gap-3">
                        {doc.kind === "audio" ? (
                          <Mic className="mt-0.5 h-4 w-4 shrink-0 text-sanad-blue" />
                        ) : (
                          <FileText className="mt-0.5 h-4 w-4 shrink-0 text-sanad-blue" />
                        )}
                        <div className="min-w-0">
                          <p className="truncate font-medium text-sanad-slate">
                            {meta.inventory_number
                              ? `${ar ? "قطعة" : "Pièce"} ${meta.inventory_number} — `
                              : ""}
                            {doc.original_name}
                          </p>
                          <DocumentStatusBadge
                            className="mt-1"
                            status={doc.status}
                            ocrScore={doc.kind === "audio" ? null : doc.ocr_score}
                            ocrAlert={doc.kind === "audio" ? false : !!doc.ocr_alert}
                            kind={
                              doc.kind === "audio"
                                ? "audio"
                                : doc.original_name?.toLowerCase().endsWith(".docx")
                                  ? "docx"
                                  : doc.kind || "file"
                            }
                          />
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            setPreviewDoc({
                              id: doc.id,
                              name: doc.original_name,
                              mimeType: doc.mime_type,
                            })
                          }
                        >
                          {ar ? "معاينة" : "Aperçu"}
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          className="bg-sanad-navy text-white hover:bg-sanad-navy/90"
                          onClick={() => router.push(`/documents/${doc.id}`)}
                        >
                          {t.viewDoc}
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          disabled={downloadPctById[doc.id] != null}
                          onClick={() => {
                            setDownloadPctById((prev) => ({ ...prev, [doc.id]: 0 }));
                            void downloadDocument(doc.id, doc.original_name, (pct) => {
                              setDownloadPctById((prev) => ({ ...prev, [doc.id]: pct }));
                            })
                              .catch(async (err) => {
                                await confirm({
                                  title:
                                    err instanceof Error
                                      ? err.message
                                      : ar
                                        ? "تعذّر التحميل."
                                        : "Téléchargement impossible.",
                                  confirmLabel: ar ? "حسناً" : "OK",
                                });
                              })
                              .finally(() => {
                                window.setTimeout(() => {
                                  setDownloadPctById((prev) => {
                                    const next = { ...prev };
                                    delete next[doc.id];
                                    return next;
                                  });
                                }, 600);
                              });
                          }}
                        >
                          <Download className="h-3.5 w-3.5" />
                          {downloadPctById[doc.id] != null
                            ? ar
                              ? `تحميل ${downloadPctById[doc.id]}%`
                              : `${downloadPctById[doc.id]}%`
                            : t.downloadDoc}
                        </Button>
                        {canDeleteDocument({
                          role: user?.role,
                          userId: user?.id,
                          uploadedBy: doc.uploaded_by,
                        }) ? (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          className="border-red-200 text-red-700 hover:bg-red-50"
                          disabled={deletingId === doc.id}
                          onClick={() => {
                            void (async () => {
                              const ok = await confirm({
                                title: ar
                                  ? "حذف هذه الوثيقة نهائياً؟"
                                  : "Supprimer ce document définitivement ?",
                                tone: "danger",
                                requireDeletePhrase: true,
      deleteVisual: "document",
                              });
                              if (!ok) return;
                              setDeletingId(doc.id);
                              try {
                                await api.deleteDocument(doc.id);
                                await load();
                              } catch (err) {
                                await confirm({
                                  title:
                                    err instanceof Error
                                      ? err.message
                                      : ar
                                        ? "تعذّر الحذف."
                                        : "Suppression impossible.",
                                  description: ar
                                    ? "يمكن حذف القطع التي رفعتموها فقط."
                                    : "Vous ne pouvez supprimer que les pièces que vous avez déposées.",
                                  confirmLabel: ar ? "حسناً" : "OK",
                                  cancelLabel: ar ? "إغلاق" : "Fermer",
                                });
                              } finally {
                                setDeletingId(null);
                              }
                            })();
                          }}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          {deletingId === doc.id ? "…" : t.deleteDoc}
                        </Button>
                        ) : null}
                      </div>
                      </div>
                      <div className="grid gap-2 rounded-lg border border-sanad-border/80 bg-sanad-cream/30 p-3 text-xs sm:grid-cols-2 lg:grid-cols-5">
                        <label className="block" title={ar ? "ترتيب في الملف" : "Ordre dans le dossier"}>
                          <span className="mb-1 block text-slate-500">
                            {ar ? "رقم القطعة" : "N° pièce"}
                          </span>
                          <input
                            type="number"
                            min={1}
                            className="w-full rounded-md border border-sanad-border px-2 py-1.5"
                            value={meta.inventory_number}
                            onChange={(e) =>
                              setDocMetaDraft((prev) => ({
                                ...prev,
                                [doc.id]: { ...meta, inventory_number: e.target.value },
                              }))
                            }
                          />
                        </label>
                        <label className="block">
                          <span className="mb-1 block text-slate-500">
                            {ar ? "النوع" : "Type"}
                          </span>
                          <select
                            className="w-full rounded-md border border-sanad-border px-2 py-1.5"
                            value={meta.exhibit_type}
                            onChange={(e) =>
                              setDocMetaDraft((prev) => ({
                                ...prev,
                                [doc.id]: { ...meta, exhibit_type: e.target.value },
                              }))
                            }
                          >
                            <option value="">—</option>
                            {EXHIBIT_TYPES.map((x) => (
                              <option key={x.value} value={x.value}>
                                {ar ? x.ar : x.fr}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label className="block">
                          <span className="mb-1 block text-slate-500">
                            {ar ? "المنتج" : "Producteur"}
                          </span>
                          <select
                            className="w-full rounded-md border border-sanad-border px-2 py-1.5"
                            value={meta.produced_by}
                            onChange={(e) =>
                              setDocMetaDraft((prev) => ({
                                ...prev,
                                [doc.id]: { ...meta, produced_by: e.target.value },
                              }))
                            }
                          >
                            <option value="">—</option>
                            {PRODUCED_BY.map((x) => (
                              <option key={x.value} value={x.value}>
                                {ar ? x.ar : x.fr}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label className="block">
                          <span className="mb-1 block text-slate-500">
                            {ar ? "النسخة" : "Version"}
                          </span>
                          <select
                            className="w-full rounded-md border border-sanad-border px-2 py-1.5"
                            value={meta.exhibit_version}
                            onChange={(e) =>
                              setDocMetaDraft((prev) => ({
                                ...prev,
                                [doc.id]: { ...meta, exhibit_version: e.target.value },
                              }))
                            }
                          >
                            <option value="">—</option>
                            {EXHIBIT_VERSIONS.map((x) => (
                              <option key={x.value} value={x.value}>
                                {ar ? x.ar : x.fr}
                              </option>
                            ))}
                          </select>
                        </label>
                        <div className="flex flex-col gap-1.5">
                          <label className="block grow">
                            <span className="mb-1 block text-slate-500">
                              {ar ? "مرجع في المرافعة (اختياري)" : "Réf. dans la plaidoirie (optionnel)"}
                            </span>
                            <input
                              className="w-full rounded-md border border-sanad-border px-2 py-1.5"
                              value={meta.cited_in_plea}
                              onChange={(e) =>
                                setDocMetaDraft((prev) => ({
                                  ...prev,
                                  [doc.id]: { ...meta, cited_in_plea: e.target.value },
                                }))
                              }
                              placeholder={ar ? "مثال: قطعة 2 — عقد الزواج" : "Ex. pièce 2 — acte de mariage"}
                            />
                          </label>
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            disabled={docMetaSaving === doc.id}
                            onClick={() => {
                              setDocMetaSaving(doc.id);
                              const inv = meta.inventory_number.trim();
                              void api
                                .updateDocumentMeta(doc.id, {
                                  inventory_number: inv ? Number(inv) : null,
                                  exhibit_type: meta.exhibit_type || null,
                                  produced_by: meta.produced_by || null,
                                  exhibit_version: meta.exhibit_version || null,
                                  cited_in_plea: meta.cited_in_plea.trim() || null,
                                })
                                .then((updated) => {
                                  setDocuments((prev) =>
                                    prev.map((d) => (d.id === updated.id ? { ...d, ...updated } : d)),
                                  );
                                })
                                .catch(async (err) => {
                                  await confirm({
                                    title:
                                      err instanceof Error
                                        ? err.message
                                        : ar
                                          ? "تعذّر الحفظ."
                                          : "Enregistrement impossible.",
                                    confirmLabel: ar ? "حسناً" : "OK",
                                  });
                                })
                                .finally(() => setDocMetaSaving(null));
                            }}
                          >
                            {docMetaSaving === doc.id
                              ? "…"
                              : ar
                                ? "حفظ القطعة"
                                : "Enregistrer pièce"}
                          </Button>
                        </div>
                      </div>
                    </div>
                    );
                  })
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {tab === "activite" && (
          <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>{t.timeline}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="flex gap-3">
                <div className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-sanad-blue" />
                <div>
                  <p className="font-medium">{t.caseCreated}</p>
                  <p className="text-slate-500">
                    {new Date(caseData.opened_at).toLocaleString(dateLocale)}
                  </p>
                </div>
              </div>
              {documents.map((doc) => (
                <div key={doc.id} className="flex gap-3">
                  <div className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-sanad-gold" />
                  <div>
                    <p className="font-medium">
                      {t.documentPrefix} : {doc.original_name}
                    </p>
                    <p className="text-slate-500">
                      {new Date(doc.created_at).toLocaleString(dateLocale)} · {doc.status}
                    </p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{ar ? "مناقشة الملف" : "Discussion"}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <p className="rounded-lg border border-sanad-border bg-sanad-cream/40 px-3 py-2 text-xs text-slate-600">
                {ar
                  ? "الملاحظات تظهر هنا لكل أعضاء المكتب. يتلقون إشعاراً في الجرس أعلى الصفحة."
                  : "Les notes s’affichent ici pour tout le cabinet. Les collègues reçoivent une notification (cloche en haut)."}
              </p>
              <div className="space-y-3">
                {comments.length === 0 ? (
                  <p className="text-slate-400">
                    {ar
                      ? "لا تعليقات بعد — أضيفوا ملاحظة للفريق."
                      : "Aucun commentaire — ajoutez une note pour l’équipe."}
                  </p>
                ) : (
                  comments.map((c) => (
                    <div
                      key={c.id}
                      className="rounded-lg border border-sanad-border bg-white px-3 py-2"
                    >
                      <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
                        <p className="font-medium text-sanad-navy">{c.author_name}</p>
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] text-slate-400">
                            {new Date(c.created_at).toLocaleString(dateLocale)}
                          </span>
                          {canUseAI ? (
                            <button
                              type="button"
                              className="text-[11px] text-red-600 hover:underline"
                              onClick={() => {
                                void api
                                  .deleteCaseComment(caseId, c.id)
                                  .then(() =>
                                    setComments((prev) => prev.filter((x) => x.id !== c.id)),
                                  )
                                  .catch(() => {});
                              }}
                            >
                              {ar ? "حذف" : "Supprimer"}
                            </button>
                          ) : null}
                        </div>
                      </div>
                      <p className="whitespace-pre-wrap text-sanad-slate">{c.body}</p>
                    </div>
                  ))
                )}
              </div>
              <div className="space-y-2 border-t border-sanad-border pt-3">
                <textarea
                  className="min-h-[80px] w-full rounded-lg border border-sanad-border px-3 py-2 text-sm"
                  value={commentDraft}
                  onChange={(e) => setCommentDraft(e.target.value)}
                  placeholder={
                    ar ? "اكتبوا ملاحظة للفريق…" : "Écrire une note pour l’équipe…"
                  }
                />
                <Button
                  type="button"
                  size="sm"
                  disabled={commentBusy || !commentDraft.trim()}
                  onClick={() => {
                    setCommentBusy(true);
                    void api
                      .addCaseComment(caseId, { body: commentDraft.trim() })
                      .then((created) => {
                        setComments((prev) => [...prev, created]);
                        setCommentDraft("");
                      })
                      .catch(async (err) => {
                        await confirm({
                          title:
                            err instanceof Error
                              ? err.message
                              : ar
                                ? "تعذّر الإرسال."
                                : "Envoi impossible.",
                          confirmLabel: ar ? "حسناً" : "OK",
                        });
                      })
                      .finally(() => setCommentBusy(false));
                  }}
                >
                  {commentBusy ? "…" : ar ? "نشر" : "Publier"}
                </Button>
              </div>
            </CardContent>
          </Card>
          </div>
        )}
      </FadeIn>
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
