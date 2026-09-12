"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowRight,
  Check,
  ChevronDown,
  Download,
  Eye,
  FileText,
  FolderOpen,
  Loader2,
  Mic,
  Pause,
  Play,
  Sparkles,
  Wand2,
  RefreshCw,
  Trash2,
  Copy,
  X,
  Upload,
} from "lucide-react";
import { PlaidoirieDocumentPreview } from "@/components/redaction/plaidoirie-document-preview";
import {
  DocumentPreviewModal,
  type DocumentPreviewTarget,
} from "@/components/documents/document-preview-modal";
import { VoiceMeter } from "@/components/ai/voice-meter";
import { VoiceOrb, VoiceWave } from "@/components/ai/voice-orb";
import { setFocusMode } from "@/hooks/use-ui-prefs";
import {
  api,
  ApiError,
  type CabinetPlaidoirieTemplate,
  type CaseListItem,
  type DocumentItem,
} from "@/lib/api";
import { useBillingCredits } from "@/store/billing-credits";
import { useActionToast } from "@/store/action-toast";
import {
  structurePlaidoirieBody,
} from "@/lib/export-official-doc";
import {
  arabicFieldProps,
  fixArabicBidiDisplay,
  renderArabicPreviewHtml,
} from "@/lib/arabic-bidi";
import {
  getPlaidoirieTemplate,
  PLAIDOIRIE_DOMAIN_GROUPS,
} from "@/lib/plaidoirie-templates";
import { DocumentUpload } from "@/components/documents/document-upload";
import {
  ACT_TYPES,
  JURISDICTION_DEGREES,
  QUALITY_OPTIONS,
  TRIBUNAL_OPTIONS,
  actTypeToTemplate,
  degreeToBriefJurisdiction,
  indicativeDeadlineHint,
  missingLegalFields,
  opposingRoleFor,
  partyRoleOptions,
  qualityHelp,
  roleHelp,
  roleToBriefPosture,
  suggestTribunal,
} from "@/lib/case-legal";
import { NewCaseModal } from "@/components/cases/new-case-modal";
import { cleanDictationNoise, lightCleanDictation, useSpeechInput } from "@/hooks/use-speech-input";
import { useWhisperDictation } from "@/hooks/use-whisper-dictation";
import { useAuthStore } from "@/store/auth";
import { useLocaleStore } from "@/store/locale";
import { useConfirm } from "@/components/ui/confirm-dialog";
import {
  PleaStepCarousel,
  PLEA_STEPS,
  type PleaStepStatus,
} from "@/components/redaction/plea-step-carousel";
import { DocumentWorkspace } from "@/components/redaction/document-workspace";
import {
  PleaAssistPanel,
  type FormEdit,
  type PleaVariable,
} from "@/components/redaction/plea-assist-panel";
import {
  PLEA_DRAFT_RESTORE_KEY,
  PLEA_DRAFT_RESTORE_KEY_LEGACY,
} from "@/components/redaction/template-picker";
import {
  clearPleaSession,
  loadPleaSession,
  markPleaPendingReturn,
  savePleaSession,
  type PleaSessionSnapshot,
} from "@/lib/plea-session";
import { looksLikeGibberish } from "@/lib/dictation-quality";
import { useRouter } from "next/navigation";
import { ComposeProgressOverlay } from "@/components/redaction/compose-progress";
import {
  PleaClarifySheet,
  type ClarifyAnswer,
} from "@/components/redaction/plea-clarify-sheet";
import type { ClarifyDictationResult } from "@/lib/api";

function inferComposeType(source: string, templateId: string, customBase?: string): string {
  // Le type choisi dans l'UI prime toujours — l'IA / postprocess s'alignent dessus.
  if (customBase && customBase !== "custom") return customBase;
  if (templateId && templateId !== "libre") return templateId;
  if (customBase === "custom") return "custom";
  // Heuristique soft uniquement pour page vierge (libre)
  if (/ضحا|جرائم|مخدر|اتجار\s*بالبشر|عصاب|شبكة/i.test(source)) return "partie-civile";
  if (/متهم|ظنين|دفاع\s*جنائي/i.test(source)) return "penal-defense";
  return templateId || "libre";
}

function stripStars(text: string): string {
  return text
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*\n]+)\*/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^\s*[-*•]\s+/gm, "— ")
    .replace(/\*{1,3}/g, "")
    .trim();
}

type PleaDraftRestore = {
  title?: string;
  body?: string;
  case_id?: string;
  checks?: string[];
};

function readPleaDraftRestore(): PleaDraftRestore | null {
  if (typeof window === "undefined") return null;
  try {
    const raw =
      sessionStorage.getItem(PLEA_DRAFT_RESTORE_KEY) ||
      sessionStorage.getItem(PLEA_DRAFT_RESTORE_KEY_LEGACY);
    if (!raw) return null;
    sessionStorage.removeItem(PLEA_DRAFT_RESTORE_KEY);
    sessionStorage.removeItem(PLEA_DRAFT_RESTORE_KEY_LEGACY);
    return JSON.parse(raw) as PleaDraftRestore;
  } catch {
    return null;
  }
}

type Props = {
  templateId: string;
  /** Rouvrir un brouillon existant (évite le bug Next soft-nav même template). */
  draftId?: string;
  /** Dossier pré-lié (ex. depuis la fiche dossier). */
  initialCaseId?: string;
  /** Reprendre une session locale après visite dossier / pièces. */
  resume?: boolean;
  /** Page vierge : ne jamais restaurer l’ancien brouillon local. */
  fresh?: boolean;
};

function resolveSessionRestore(
  templateId: string,
  resume?: boolean,
  fresh?: boolean,
): PleaSessionSnapshot | null {
  if (fresh) return null;
  const s = loadPleaSession();
  if (!s) return null;
  if (resume) return s;
  if (s.pendingReturn && s.templateId === templateId) return s;
  return null;
}

/**
 * Espace dictée / document — AR + FR (micro navigateur + polish/compose).
 */
export function PlaidoirieWorkspace({ templateId, draftId, initialCaseId, resume, fresh }: Props) {
  const notifySpend = useBillingCredits((s) => s.notifySpend);
  const pushToast = useActionToast((s) => s.push);
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const locale = useLocaleStore((s) => s.locale);
  /** Langue de l’interface (topbar FR / عربي) — pas la langue de dictée. */
  const uiFr = locale === "fr";
  const restoreDraftRef = useRef(readPleaDraftRestore());
  const restored = restoreDraftRef.current;
  const sessionRestoreRef = useRef(
    restored || fresh ? null : resolveSessionRestore(templateId, resume, fresh),
  );
  const sessionRestored = sessionRestoreRef.current;
  const cabinetNameFr = user?.cabinet_name || undefined;
  const cabinetNameAr = user?.cabinet_name_ar || user?.cabinet_name || undefined;
  const cabinetDisplayName = cabinetNameAr || cabinetNameFr;
  const lawyerDisplayName = user?.full_name_ar || user?.full_name || undefined;
  const [cabinetLogoUrl, setCabinetLogoUrl] = useState<string | undefined>();
  const [logoPromptOpen, setLogoPromptOpen] = useState(false);
  const [skipLogoForCompose, setSkipLogoForCompose] = useState(false);
  const confirm = useConfirm();
  const [raw, setRaw] = useState(() => sessionRestored?.raw || "");
  const [polished, setPolished] = useState(() => sessionRestored?.polished || "");
  const [docTitle, setDocTitle] = useState(() =>
    (restored?.title || sessionRestored?.docTitle || "").trim() || "",
  );
  const [docBody, setDocBody] = useState(() => {
    const body = restored?.body?.trim()
      ? restored.body
      : sessionRestored?.docBody || "";
    return body ? stripStars(body) : "";
  });
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [caseId, setCaseId] = useState(
    () => restored?.case_id || sessionRestored?.caseId || initialCaseId || "",
  );
  const [caseDocCount, setCaseDocCount] = useState<number | null>(null);
  const [caseDocs, setCaseDocs] = useState<DocumentItem[]>([]);
  const [previewDoc, setPreviewDoc] = useState<DocumentPreviewTarget | null>(null);
  const [step1Open, setStep1Open] = useState<"identite" | "pieces" | "suite">("identite");
  const [showNewCase, setShowNewCase] = useState(false);
  const [draftsHint, setDraftsHint] = useState("");
  const [busy, setBusy] = useState<
    | "polish"
    | "compose"
    | "save"
    | "saveTpl"
    | "word"
    | "pdf"
    | "previewWord"
    | "previewPdf"
    | "revise"
    | "audioFile"
    | null
  >(null);
  const [reviseInstruction, setReviseInstruction] = useState("");
  const [reviseChat, setReviseChat] = useState<
    { id: string; role: "user" | "assistant"; content: string; at: number; provider?: string }[]
  >([]);
  const [docEditorKey, setDocEditorKey] = useState(0);
  const docEditorRef = useRef<HTMLDivElement | null>(null);
  const [wordPreviewOpen, setWordPreviewOpen] = useState(false);
  const [error, setError] = useState("");
  const [senseAlert, setSenseAlert] = useState("");
  const [message, setMessage] = useState(() =>
    restored?.body?.trim()
      ? uiFr
        ? "Brouillon rouvert depuis l’historique."
        : "تم فتح المسودة من السجل."
      : sessionRestored
        ? uiFr
          ? "Atelier repris — vos saisies ont été restaurées."
          : "استُؤنفت الورشة — تمت استعادة مدخلاتكم."
        : "",
  );
  const [provider, setProvider] = useState("");
  const [sttReady, setSttReady] = useState<boolean | null>(null);
  const [sttPipeline, setSttPipeline] = useState("");
  const [lastSttMs, setLastSttMs] = useState<number | null>(null);
  const dictationLang = "ar" as const;
  const isMobileDevice = () => {
    if (typeof navigator === "undefined") return false;
    const ua = navigator.userAgent || "";
    return (
      /Android|iPhone|iPad|iPod|Mobile/i.test(ua) ||
      (navigator.maxTouchPoints > 1 && typeof window !== "undefined" && window.innerWidth < 920)
    );
  };

  const [customTemplates, setCustomTemplates] = useState<CabinetPlaidoirieTemplate[]>(
    [],
  );
  const [composeChecks, setComposeChecks] = useState<string[]>(
    () => restored?.checks || sessionRestored?.composeChecks || [],
  );
  const [checksOpen, setChecksOpen] = useState(false);
  const [contradictions, setContradictions] = useState<
    { kind: string; values: string[]; message_ar: string; message_fr: string }[]
  >([]);
  /** verified = contrôle exécuté | unchecked = service KO (ne jamais dire « rien trouvé ») */
  const [contradictionCheck, setContradictionCheck] = useState<"idle" | "verified" | "unchecked">(
    "idle",
  );
  const [editingPolished, setEditingPolished] = useState(false);
  const [formEdits, setFormEdits] = useState<FormEdit[]>([]);
  const [pleaVariables, setPleaVariables] = useState<PleaVariable[]>([]);
  const [ready, setReady] = useState(false);
  const [step, setStep] = useState(() =>
    restored?.body?.trim()
      ? 3
      : typeof sessionRestored?.step === "number"
        ? Math.max(0, Math.min(4, sessionRestored.step))
        : 0,
  );
  const [exportedDone, setExportedDone] = useState(false);
  const [savedDraftId, setSavedDraftId] = useState<string | undefined>(draftId);
  const [settingsVisited, setSettingsVisited] = useState(
    () =>
      !!restored?.body?.trim() ||
      !!initialCaseId ||
      !!sessionRestored?.settingsVisited ||
      !!sessionRestored?.caseId,
  );
  const [pleaType, setPleaType] = useState(() =>
    sessionRestored?.pleaType ||
    (templateId && templateId !== "libre" && templateId !== "new" ? templateId : "civil-general"),
  );
  const [actType, setActType] = useState(
    () => (sessionRestored as { actType?: string } | null)?.actType || "plaidoirie_orale",
  );
  const [legalDraft, setLegalDraft] = useState({
    jurisdiction_degree: "premiere_instance",
    tribunal: "tpi",
    client_role: "demandeur",
    client_quality: "personne_physique",
    client_domicile: "",
    opposing_name: "",
    opposing_quality: "personne_physique",
    opposing_domicile: "",
  });
  const [legalSaving, setLegalSaving] = useState(false);
  const [clarifyOpen, setClarifyOpen] = useState(false);
  const [clarifyLoading, setClarifyLoading] = useState(false);
  const [clarifyData, setClarifyData] = useState<ClarifyDictationResult | null>(null);
  const [briefPosture, setBriefPosture] = useState(
    () => sessionRestored?.briefPosture || "demandeur",
  );
  const [briefJurisdiction, setBriefJurisdiction] = useState(
    () => sessionRestored?.briefJurisdiction || "tpi",
  );

  const selectedTemplate = getPlaidoirieTemplate(templateId);
  const selectedCustom = customTemplates.find((t) => t.id === templateId);
  const templateLabel = selectedCustom
    ? selectedCustom.name
    : uiFr
      ? selectedTemplate?.labelFr || selectedTemplate?.labelAr || "Plaidoirie"
      : selectedTemplate?.labelAr || "مرافعة";
  /** Direction / labels du texte dicté (indépendant de l’UI). */
  const dictFr = dictationLang === "fr";
  const arabicField = arabicFieldProps(dictFr);
  const textDir = arabicField.dir;

  const {
    recording,
    transcribing,
    error: whisperError,
    startRecording,
    pauseRecording,
    resumeRecording,
    stopRecordingAndTranscribe,
    cancelTranscribing,
    transcribeFile,
    supported: recorderOk,
    analyser,
    setLanguage: setWhisperLanguage,
  } = useWhisperDictation("ar");

  const {
    startListening: startLivePreview,
    stopListening: stopLivePreview,
    supported: livePreviewOk,
    error: livePreviewError,
  } = useSpeechInput(dictationLang);

  const sessionBaseRef = useRef("");
  const polishGenRef = useRef(0);
  const chromeFinalsRef = useRef("");
  const sessionStartRawRef = useRef("");
  const recStartedAtRef = useRef(0);
  /** true = dictée Chrome seule (pas de MediaRecorder — évite conflit micro) */
  const chromeOnlyRef = useRef(false);
  const audioFileInputRef = useRef<HTMLInputElement | null>(null);
  const [liveCaption, setLiveCaption] = useState("");
  const [recElapsedSec, setRecElapsedSec] = useState(0);
  const [dictationActive, setDictationActive] = useState(false);
  const [dictationPaused, setDictationPaused] = useState(false);
  const isLive = dictationActive || recording || transcribing;

  useEffect(() => {
    setFocusMode(isLive);
    return () => setFocusMode(false);
  }, [isLive]);

  useEffect(() => {
    if (!dictationActive || dictationPaused) return;
    const id = window.setInterval(() => {
      if (!recStartedAtRef.current) return;
      setRecElapsedSec(Math.floor((Date.now() - recStartedAtRef.current) / 1000));
    }, 500);
    return () => window.clearInterval(id);
  }, [dictationActive, dictationPaused]);

  useEffect(() => {
    setWhisperLanguage("ar");
  }, [setWhisperLanguage]);

  useEffect(() => {
    api.getCases().then(setCases).catch(() => setCases([]));
    // Dictée = micro navigateur (SpeechRecognition) uniquement
    setSttReady(!!livePreviewOk);
    setSttPipeline("browser-speech");
  }, [livePreviewOk]);

  useEffect(() => {
    if (!caseId) {
      setCaseDocCount(null);
      setCaseDocs([]);
      return;
    }
    let cancelled = false;
    void api
      .getDocuments(caseId)
      .then((docs) => {
        if (!cancelled) {
          setCaseDocs(docs);
          setCaseDocCount(docs.length);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCaseDocCount(null);
          setCaseDocs([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [caseId]);

  function refreshCaseDocs() {
    if (!caseId) return;
    void api
      .getDocuments(caseId)
      .then((docs) => {
        setCaseDocs(docs);
        setCaseDocCount(docs.length);
      })
      .catch(() => undefined);
  }

  useEffect(() => {
    if (!fresh) return;
    clearPleaSession();
  }, [fresh]);

  // Autosave atelier → localStorage (retour dossier / pièces sans perte)
  useEffect(() => {
    if (exportedDone) return;
    const t = window.setTimeout(() => {
      savePleaSession({
        v: 1,
        templateId,
        step,
        caseId,
        raw,
        polished,
        docTitle,
        docBody,
        composeChecks,
        pleaType,
        actType,
        briefPosture,
        briefJurisdiction,
        settingsVisited,
        editingPolished,
        savedAt: Date.now(),
        pendingReturn: false,
      });
    }, 400);
    return () => window.clearTimeout(t);
  }, [
    templateId,
    step,
    caseId,
    raw,
    polished,
    docTitle,
    docBody,
    composeChecks,
    pleaType,
    actType,
    briefPosture,
    briefJurisdiction,
    settingsVisited,
    editingPolished,
    exportedDone,
  ]);

  function openLinkedCase(opts?: { tab?: "documents" | "resume" }) {
    if (!caseId) return;
    markPleaPendingReturn(templateId);
    savePleaSession({
      v: 1,
      templateId,
      step,
      caseId,
      raw,
      polished,
      docTitle,
      docBody,
      composeChecks,
      pleaType,
      actType,
      briefPosture,
      briefJurisdiction,
      settingsVisited,
      editingPolished,
      savedAt: Date.now(),
      pendingReturn: true,
    });
    const tab = opts?.tab || "documents";
    router.push(`/cases/${caseId}?from=plea&tab=${tab}`);
  }

  useEffect(() => {
    if (!draftId) return;
    let cancelled = false;
    void api
      .getPlaidoirieDraft(draftId)
      .then((d) => {
        if (cancelled) return;
        setSavedDraftId(d.id);
        if (d.title?.trim()) setDocTitle(d.title.trim());
        if (d.body?.trim()) {
          setDocBody(stripStars(d.body));
          setStep(d.status === "finalized" ? 4 : 3);
          if (d.status === "finalized") setExportedDone(true);
          setMessage(
            d.status === "finalized"
              ? uiFr
                ? "Plaidoirie finalisée rouverte."
                : "فُتحت المرافعة المنتهية."
              : uiFr
                ? "Brouillon rouvert depuis l’historique."
                : "تم فتح المسودة من السجل.",
          );
        }
        if (d.case_id) setCaseId(d.case_id);
        setReady(true);
      })
      .catch(() => {
        /* sessionStorage restore already applied if present */
      });
    return () => {
      cancelled = true;
    };
  }, [draftId, uiFr]);

  useEffect(() => {
    if (user?.cabinet_has_logo) {
      void api
        .getCabinetLogoDataUrl()
        .then((url) => setCabinetLogoUrl(url || undefined))
        .catch(() => setCabinetLogoUrl(undefined));
    } else {
      setCabinetLogoUrl(undefined);
    }
  }, [user?.cabinet_has_logo]);

  useEffect(() => {
    const skipTemplateBody = !!restoreDraftRef.current?.body?.trim();
    api
      .listCabinetPlaidoirieTemplates()
      .then((list) => {
        setCustomTemplates(list);
        if (skipTemplateBody) {
          setReady(true);
          return;
        }
        const custom = list.find((t) => t.id === templateId);
        const sys = getPlaidoirieTemplate(templateId);
        if (custom) {
          setDocTitle(custom.name);
          setDocBody(stripStars(custom.body));
        } else if (sys) {
          setDocTitle(sys.labelAr);
          setDocBody(sys.body);
        } else {
          const libre = getPlaidoirieTemplate("libre");
          setDocTitle(libre?.labelAr || "مرافعة");
          setDocBody(libre?.body || "");
        }
        setReady(true);
      })
      .catch(() => {
        if (skipTemplateBody) {
          setReady(true);
          return;
        }
        const sys = getPlaidoirieTemplate(templateId) || getPlaidoirieTemplate("libre");
        setDocTitle(sys?.labelAr || "مرافعة");
        setDocBody(sys?.body || "");
        setReady(true);
      });
  }, [templateId]);

  function finalizeDictation(text: string, fromProvider?: string) {
    const fromServer =
      !!fromProvider &&
      (fromProvider.startsWith("whisper") || fromProvider.startsWith("groq"));
    const cleaned = fromServer ? lightCleanDictation(text) : cleanDictationNoise(text);
    if (!cleaned) return;
    const bidi = fixArabicBidiDisplay(cleaned);
    setRaw(bidi);
    setPolished(fixArabicBidiDisplay(lightCleanDictation(cleaned)));
    if (fromProvider) setProvider(fromProvider);
    setMessage("");
    setError("");
    sessionBaseRef.current = "";
  }


  function cancelPolish() {
    polishGenRef.current += 1;
    setBusy(null);
    setMessage("");
  }

  function resetLiveBuffers() {
    setLiveCaption("");
  }


  async function startDictation() {
    if (dictationActive || busy) return;
    // Chrome SpeechRecognition en priorité ; sinon Whisper (MediaRecorder) — ne jamais laisser le micro « mort »
    if (livePreviewOk) {
      setDictationActive(true);
      setDictationPaused(false);
      chromeOnlyRef.current = true;
      const base = cleanDictationNoise(raw);
      sessionStartRawRef.current = base;
      sessionBaseRef.current = base;
      chromeFinalsRef.current = "";
      resetLiveBuffers();
      setError("");
      setLastSttMs(null);
      recStartedAtRef.current = Date.now();
      setRecElapsedSec(0);
      setLiveCaption("");
      startLivePreview((finals, interim) => {
        chromeFinalsRef.current = finals;
        const live = [finals, interim].filter(Boolean).join(" ").trim();
        setLiveCaption(live);
        const merged = [base, finals].filter(Boolean).join(" ").trim();
        if (merged) setRaw(merged);
      });
      return;
    }
    if (recorderOk) {
      setDictationActive(true);
      setDictationPaused(false);
      chromeOnlyRef.current = false;
      const base = cleanDictationNoise(raw);
      sessionStartRawRef.current = base;
      sessionBaseRef.current = base;
      chromeFinalsRef.current = "";
      resetLiveBuffers();
      setError("");
      setMessage(
        uiFr
          ? "Dictée serveur (Whisper) — parlez clairement, puis validez."
          : "إملاء عبر الخادم — تكلّموا بوضوح ثم أكّدوا.",
      );
      setLastSttMs(null);
      recStartedAtRef.current = Date.now();
      setRecElapsedSec(0);
      try {
        await startRecording();
      } catch {
        setDictationActive(false);
        setError(
          uiFr
            ? "Impossible d’accéder au micro. Autorisez le micro dans le navigateur."
            : "تعذر الوصول إلى الميكروفون. اسمحوا بالميكروفون في المتصفح.",
        );
      }
      return;
    }
    setError(
      uiFr
        ? "Micro indisponible. Utilisez Chrome/Edge, autorisez le micro, ou saisissez le texte à l’étape Transcription."
        : "الميكروفون غير متاح. استخدموا Chrome/Edge أو اكتبوا النص في خطوة التفريغ.",
    );
  }

  function pauseDictation() {
    if (!dictationActive || dictationPaused) return;
    setDictationPaused(true);
    if (!chromeOnlyRef.current) pauseRecording();
    stopLivePreview();
    setMessage(
      uiFr ? "Dictée en pause — Reprendre pour continuer." : "الإملاء متوقف مؤقتاً — استأنفوا للمتابعة.",
    );
  }

  function resumeDictation() {
    if (!dictationActive || !dictationPaused) return;
    setDictationPaused(false);
    if (!chromeOnlyRef.current) resumeRecording();
    sessionBaseRef.current = [sessionBaseRef.current, chromeFinalsRef.current]
      .filter(Boolean)
      .join(" ")
      .trim();
    chromeFinalsRef.current = "";
    if (chromeOnlyRef.current || livePreviewOk) {
      const base = sessionBaseRef.current;
      startLivePreview((finals, interim) => {
        chromeFinalsRef.current = finals;
        setLiveCaption([finals, interim].filter(Boolean).join(" ").trim());
        const merged = [base, finals].filter(Boolean).join(" ").trim();
        if (merged) setRaw(merged);
      });
    }
    setError("");
    setMessage(uiFr ? "Reprise — continuez à parler." : "استئناف — واصلوا الحديث.");
  }

  async function handleAudioFile(file: File | undefined) {
    if (!file || dictationActive || recording || transcribing) return;
    const okType = /\.(webm|wav|mp3|ogg|m4a|mp4|aac)$/i.test(file.name) || file.type.startsWith("audio/");
    if (!okType) {
      setError(uiFr ? "Fichier audio attendu (webm, wav, mp3, ogg, m4a)." : "ملف صوتي مطلوب (webm, wav, mp3, ogg, m4a).");
      return;
    }
    setBusy("audioFile");
    setError("");
    setMessage(uiFr ? "Transcription du fichier…" : "جاري تفريغ الملف…");
    try {
      const res = await transcribeFile(file);
      const text = cleanDictationNoise(res?.text || "");
      if (!text) {
        setError(uiFr ? "Aucune parole détectée dans le fichier." : "لم يُكتشف كلام في الملف.");
        return;
      }
      setRaw(text);
      setLiveCaption(text);
      setPolished("");
      setFormEdits([]);
      setContradictions([]);
      setContradictionCheck("idle");
      goStep(2);
      pushToast(
        uiFr ? "Fichier transcrit — relisez puis Corriger." : "تم تفريغ الملف — راجعوا ثم «تصحيح».",
        "success",
      );
      setMessage(uiFr ? "Texte extrait du fichier. Relisez puis Corriger." : "تم استخراج النص. راجعوا ثم صحّحوا.");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : (uiFr ? "Transcription du fichier impossible." : "تعذّر تفريغ الملف."));
    } finally {
      setBusy(null);
      if (audioFileInputRef.current) audioFileInputRef.current.value = "";
    }
  }

  function pickDictationText(serverText: string, serverProvider: string): { text: string; provider: string } {
    const chrome = cleanDictationNoise(
      [sessionBaseRef.current, chromeFinalsRef.current].filter(Boolean).join(" "),
    );
    const server = lightCleanDictation(serverText || "");
    const chromeWords = chrome.split(/\s+/).filter(Boolean).length;
    const serverWords = server.split(/\s+/).filter(Boolean).length;

    // Mobile / Whisper : privilégier le serveur s'il est plus riche (Chrome live souvent absent).
    if (serverWords >= 3 && serverWords >= chromeWords) {
      return { text: server, provider: serverProvider || "whisper" };
    }
    if (chromeWords >= 2 && chromeWords > serverWords) {
      return { text: chrome, provider: "chrome-live" };
    }
    if (serverWords >= 4 && !/^(انا\s*){2,}$/i.test(server.replace(/\s+/g, " ").trim())) {
      return { text: server, provider: serverProvider || "whisper" };
    }
    if (chrome) return { text: chrome, provider: "chrome-live" };
    return { text: "", provider: "none" };
  }

  async function captureLiveText() {
    const t0 = Date.now();
    const chromeSnapshot = chromeFinalsRef.current;
    stopLivePreview();

    if (chromeOnlyRef.current) {
      const ms = Date.now() - t0;
      setLastSttMs(ms);
      resetLiveBuffers();
      chromeFinalsRef.current = chromeSnapshot;
      const text = cleanDictationNoise(
        [sessionBaseRef.current, chromeSnapshot].filter(Boolean).join(" "),
      );
      return { text, provider: text ? "chrome-live" : "none", ms };
    }

    setMessage(uiFr ? "Finalisation…" : "جاري الإنهاء…");
    let result: Awaited<ReturnType<typeof stopRecordingAndTranscribe>> = null;
    try {
      result = await stopRecordingAndTranscribe({ skipFinalTranscribe: false });
    } catch {
      result = null;
    }
    chromeFinalsRef.current = chromeSnapshot;
    const ms = Date.now() - t0;
    setLastSttMs(ms);
    resetLiveBuffers();
    const picked = pickDictationText(result?.text?.trim() || "", result?.provider || "none");
    return { text: picked.text, provider: picked.provider, ms };
  }

  function ignoreDictation() {
    setDictationActive(false);
    setDictationPaused(false);
    chromeOnlyRef.current = false;
    stopLivePreview();
    cancelTranscribing();
    resetLiveBuffers();
    sessionBaseRef.current = "";
    chromeFinalsRef.current = "";
    setRaw(sessionStartRawRef.current);
    setPolished("");
    setError("");
    setMessage("");
    setLastSttMs(null);
  }

  async function validateDictation() {
    setDictationActive(false);
    setDictationPaused(false);
    stopLivePreview();
    const { text, provider: from } = await captureLiveText();
    if (!text) {
      setMessage("");
      setError(
        uiFr
          ? "Aucun texte — reparlez puis Extraire."
          : "لا نص — أعيدوا الإملاء ثم «تم».",
      );
      return;
    }
    finalizeDictation(text, from);
    // « تم » = extraire le brut seulement — la correction fusḥā se fait via « تصحيح »
    setPolished("");
    setContradictions([]);
    setContradictionCheck("idle");
    setFormEdits([]);
    setPleaVariables([]);
    setMessage(
      uiFr
        ? "Texte extrait. Cliquez « Corriger » pour la version fusḥā (forme), sans résumé."
        : "تم استخراج النص الخام. اضغطوا «تصحيح» للحصول على الصيغة الفصحى (شكل فقط، بدون تلخيص).",
    );
    goStep(1);
  }

  async function handlePreviewWord() {
    if (!docBody.trim()) return;
    setWordPreviewOpen(true);
  }

  async function handlePreviewPdf() {
    if (!docBody.trim()) return;
    setBusy("previewPdf");
    setError("");
    try {
      const { blob } = await api.fetchPlaidoiriePdf({
        title: docTitle || "مرافعة",
        body: structurePlaidoirieBody(docBody),
        cabinet_name: cabinetNameFr || undefined,
        lawyer_name: lawyerDisplayName,
        city: user?.cabinet_city || undefined,
        case_reference: cases.find((c) => c.id === caseId)?.reference,
        client_name: cases.find((c) => c.id === caseId)?.client_name,
        include_esignature: false,
      });
      const url = URL.createObjectURL(blob);
      const win = window.open(url, "_blank");
      if (!win) {
        setError(
          uiFr
            ? "Autorisez les pop-ups pour l’aperçu PDF, ou utilisez Télécharger."
            : "اسمحوا بالنوافذ المنبثقة لمعاينة PDF، أو استخدموا التحميل.",
        );
        URL.revokeObjectURL(url);
        return;
      }
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
      setMessage(uiFr ? "Aperçu PDF ouvert dans un nouvel onglet." : "فُتحت معاينة PDF في تبويب جديد.");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Aperçu PDF échoué.");
    } finally {
      setBusy(null);
    }
  }

  async function handleRevise() {
    if (!docBody.trim() || !reviseInstruction.trim()) return;
    const instruction = reviseInstruction.trim();
    const userMsg = {
      id: `u-${Date.now()}`,
      role: "user" as const,
      content: instruction,
      at: Date.now(),
    };
    setReviseChat((prev) => [...prev, userMsg]);
    setBusy("revise");
    setError("");
    setMessage("");
    setWordPreviewOpen(false);
    try {
      const beforeHead = docBody.replace(/\s+/g, " ").trim().slice(0, 160);
      const res = await api.reviseDictation({
        title: docTitle,
        body: docBody,
        instruction,
        case_id: caseId || undefined,
        language: dictationLang,
      });
      const nextTitle = stripStars(res.title || docTitle);
      const nextBody = fixArabicBidiDisplay(
        structurePlaidoirieBody(stripStars(res.body || "")),
      );
      const beforeNorm = docBody.replace(/\s+/g, " ").trim();
      const afterNorm = nextBody.replace(/\s+/g, " ").trim();
      const grew = afterNorm.length - beforeNorm.length;
      const expandAsk =
        /d[ée]vel+o*p|eplsu|plus\s+(cette|ce|la|le)|élargir|enrichir|d[ée]taill|allong|وسع|طور|فصل|طوّل|المزيد/i.test(
          instruction,
        );
      const fillAsk =
        /rien\s+[eé]crit|n['’ ]?a\s*s?\s+rien|pas\s+[eé]crit|est\s+vide|compl[eè]t|remplir|écris|ecris|فارغ|أكمل|املأ|خامساً?|لهذه\s*الأسباب/i.test(
          instruction,
        );
      const sectionPayload = (text: string, marker: string) => {
        const base = marker.replace(/ً$/, "");
        const re = new RegExp(`${base}ً?\\s*[:：]?\\s*`);
        const m = re.exec(text);
        if (!m || m.index < 0) return "";
        const rest = text.slice(m.index + m[0].length);
        const nxt =
          /(?:أولاً?|ثانياً?|ثالثاً?|رابعاً?|خامساً?|سادساً?|سابعاً?|لهذه\s*الأسباب|وبناءً?\s*عليه|الملتمسات)\s*[:：]?/.exec(
            rest,
          );
        const chunk = nxt ? rest.slice(0, nxt.index) : rest;
        return chunk.replace(/\s+/g, " ").replace(/^[:：\s]+|[:：\s]+$/g, "");
      };
      const sectionStillThin = (marker: string) => {
        const compact = sectionPayload(nextBody, marker).replace(
          /[\s:：.،؛\-–—]/g,
          "",
        );
        return compact.length < 48;
      };
      const weakFill =
        fillAsk &&
        ((/خامساً?/.test(instruction) && sectionStillThin("خامساً")) ||
          (/لهذه\s*الأسباب/.test(instruction) && sectionStillThin("لهذه الأسباب")) ||
          ((!/خامساً?|لهذه\s*الأسباب/.test(instruction) &&
            (sectionStillThin("خامساً") || sectionStillThin("لهذه الأسباب")))));
      const afterHead = afterNorm.slice(0, 160);
      const visiblyChanged =
        beforeHead !== afterHead || Math.abs(docBody.length - nextBody.length) >= 40;
      const weakExpand = expandAsk && grew < 80;
      const weakChange = weakExpand || weakFill;
      setDocTitle(nextTitle);
      setDocBody(nextBody);
      setDocEditorKey((k) => k + 1);
      setReviseInstruction("");
      setProvider(res.provider || "openai");
      const chatMsg = weakFill
        ? uiFr
          ? "L’IA n’a pas encore rempli les passages vides (خامساً / لهذه الأسباب). Renvoyez simplement la même demande — le langage naturel suffit."
          : "الذكاء الاصطناعي لم يملأ بعد المقاطع الفارغة. أعيدوا نفس الطلب بصياغتكم العادية."
        : weakExpand
          ? uiFr
            ? "L’IA n’a presque pas développé le passage. Renvoyez la demande en collant le début du paragraphe à allonger."
            : "الذكاء الاصطناعي لم يطوّر المقطع تقريباً. أعيدوا الطلب مع لصق بداية الفقرة."
          : visiblyChanged
            ? uiFr
              ? `Modification appliquée (${res.provider || "ChatGPT"}). Relisez le document ci-dessus — le passage visé a été mis à jour.`
              : `طُبّق التعديل (${res.provider || "ChatGPT"}). راجعوا الوثيقة أعلاه — تم تحديث المقطع.`
            : uiFr
              ? "Réponse reçue, mais le texte n’a presque pas changé. Reformulez en une phrase simple ce que vous voulez."
              : "وصلت الإجابة لكن النص لم يتغيّر تقريباً. اكتبوا المطلوب بجملة بسيطة.";
      setReviseChat((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          content: chatMsg,
          at: Date.now(),
          provider: res.provider || undefined,
        },
      ]);
      setMessage(chatMsg);
      pushToast(
        weakChange || !visiblyChanged
          ? uiFr
            ? "Peu de changement — reformulez la consigne"
            : "تغيير ضعيف — أعيدوا صياغة الطلب"
          : uiFr
            ? "Modification ChatGPT appliquée"
            : "طُبّق تعديل ChatGPT",
        weakChange || !visiblyChanged ? "info" : "success",
      );
      void notifySpend("revise");
      try {
        const d = await api.savePlaidoirieDraft({
          title: nextTitle || "مرافعة",
          body: nextBody,
          template_id: templateId,
          case_id: caseId || undefined,
          checks: composeChecks,
        });
        if (d?.id) setSavedDraftId(d.id);
      } catch {
        /* draft optionnel */
      }
      requestAnimationFrame(() => {
        docEditorRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    } catch (e) {
      setReviseChat((prev) => [
        ...prev,
        {
          id: `a-err-${Date.now()}`,
          role: "assistant",
          content:
            e instanceof ApiError
              ? e.message
              : uiFr
                ? "Révision IA indisponible."
                : "التعديل غير متاح.",
          at: Date.now(),
        },
      ]);
      setError(e instanceof ApiError ? e.message : "Révision IA indisponible.");
    } finally {
      setBusy(null);
    }
  }

  async function markFinalizedAfterExport() {
    setExportedDone(true);
    setComposeChecks([]);
    clearPleaSession();
    try {
      if (savedDraftId) {
        await api.updatePlaidoirieDraft(savedDraftId, {
          status: "finalized",
          checks: [],
          title: docTitle || "مرافعة",
          body: structurePlaidoirieBody(docBody),
        });
      } else {
        const d = await api.savePlaidoirieDraft({
          title: docTitle || "مرافعة",
          body: structurePlaidoirieBody(docBody),
          template_id: templateId,
          case_id: caseId || undefined,
          checks: [],
          status: "finalized",
        });
        if (d?.id) setSavedDraftId(d.id);
      }
      setDraftsHint(
        uiFr
          ? "Plaidoirie marquée finalisée dans l’historique."
          : "عُلّمت المرافعة كمنتهية في السجل.",
      );
    } catch {
      /* non bloquant */
    }
  }

  async function handleExportWord(): Promise<boolean> {
    if (!docBody.trim()) return false;
    const ok = await confirm({
      title: uiFr ? "Exporter en Word ?" : "تصدير Word؟",
      description: uiFr
        ? "Le fichier sort à l’en-tête de votre cabinet (logo, barreau). Prêt à joindre au dossier."
        : "يخرج الملف بترويسة مكتبكم (الشعار، الهيئة). جاهز لإرفاقه بالملف.",
      confirmLabel: uiFr ? "Télécharger Word" : "تحميل Word",
    });
    if (!ok) return false;
    setBusy("word");
    setError("");
    try {
      const filename = await api.downloadPlaidoirieDocx({
        title: docTitle || "مرافعة",
        body: structurePlaidoirieBody(docBody),
        cabinet_name: cabinetNameFr || undefined,
        lawyer_name: lawyerDisplayName,
        city: user?.cabinet_city || undefined,
        case_reference: cases.find((c) => c.id === caseId)?.reference,
        client_name: cases.find((c) => c.id === caseId)?.client_name,
        include_esignature: false,
      });
      setMessage(filename ? `Word : ${filename}` : "Word téléchargé.");
      pushToast(uiFr ? "Export Word réussi — finalisée" : "تم تصدير Word — منتهية", "success");
      await markFinalizedAfterExport();
      return true;
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Export Word échoué.");
      return false;
    } finally {
      setBusy(null);
    }
  }

  async function handleExportPdf(): Promise<boolean> {
    if (!docBody.trim()) return false;
    const ok = await confirm({
      title: uiFr ? "Exporter en PDF ?" : "تصدير PDF؟",
      description: uiFr
        ? "Document final, en-tête cabinet, prêt à imprimer pour l’audience."
        : "وثيقة نهائية بترويسة المكتب، جاهزة للطباعة للجلسة.",
      confirmLabel: uiFr ? "Télécharger PDF" : "تحميل PDF",
    });
    if (!ok) return false;
    setBusy("pdf");
    setError("");
    try {
      const filename = await api.downloadPlaidoiriePdf({
        title: docTitle || "مرافعة",
        body: structurePlaidoirieBody(docBody),
        cabinet_name: cabinetNameFr || undefined,
        lawyer_name: lawyerDisplayName,
        city: user?.cabinet_city || undefined,
        case_reference: cases.find((c) => c.id === caseId)?.reference,
        client_name: cases.find((c) => c.id === caseId)?.client_name,
        include_esignature: false,
      });
      setMessage(filename ? `PDF : ${filename}` : (uiFr ? "PDF téléchargé." : "تم تحميل PDF."));
      pushToast(uiFr ? "Export PDF réussi — finalisée" : "تم تصدير PDF — منتهية", "success");
      await markFinalizedAfterExport();
      return true;
    } catch (e) {
      setError(e instanceof ApiError ? e.message : (uiFr ? "Export PDF échoué." : "فشل تصدير PDF."));
      return false;
    } finally {
      setBusy(null);
    }
  }

  async function handlePolish(source?: string) {
    const cleaned = cleanDictationNoise(source ?? raw);
    if (!cleaned) return;
    const refuseSense = (whyFr: string, whyAr: string) => {
      setSenseAlert(uiFr ? whyFr : whyAr);
      setError("");
      setMessage("");
      setPolished("");
      setContradictions([]);
      setContradictionCheck("idle");
      setFormEdits([]);
      setPleaVariables([]);
      pushToast(
        uiFr ? "Ce texte n’a pas de sens — correction refusée" : "النص بلا معنى — رُفض التصحيح",
        "info",
      );
    };
    if (looksLikeGibberish(cleaned)) {
      refuseSense(
        "Ce texte n’a pas de sens (touches au hasard, lettres isolées, pas une phrase). ChatGPT ne le « corrige » pas : dictez ou écrivez une vraie phrase, sinon la rédaction IA n’aura rien de solide.",
        "هذا النص بلا معنى (نقرات عشوائية، حروف بلا جملة). لن يُصلحه ChatGPT: أملوا أو اكتبوا جملة حقيقية، وإلا لن تستطيع الصياغة بناء مرافعة.",
      );
      return;
    }
    setRaw(cleaned);
    const gen = ++polishGenRef.current;
    setBusy("polish");
    setError("");
    setSenseAlert("");
    setMessage("");
    setContradictions([]);
    setContradictionCheck("idle");
    try {
      const res = await api.polishDictation(cleaned, dictationLang, "audio");
      if (gen !== polishGenRef.current) return;
      if ((res.provider || "") === "nonsense") {
        refuseSense(
          "ChatGPT a lu le texte : il n’a pas de sens utilisable pour une plaidoirie. Réécrivez ou dictez les faits (qui, quoi, quelle demande).",
          "قرأ ChatGPT النص: لا معنى صالحاً لمرافعة. أعيدوا الكتابة أو الإملاء (من، ماذا، أي طلب).",
        );
        setBusy(null);
        return;
      }
      // Ne pas repasser lightCleanDictation : détruit paragraphes et balises ‹ ›
      const out = stripStars((res.polished || cleaned).replace(/\r\n/g, "\n")).trim();
      setPolished(fixArabicBidiDisplay(out || cleaned));
      setProvider(res.provider || "fidelity");
      setContradictions(res.contradictions || []);
      setContradictionCheck("verified");
      void notifySpend("polish");
      // Ignorer suggestions identiques / bruit — le corrigé contient déjà les vrais fixes
      const realEdits = (res.edits || []).filter((e) => {
        const o = (e.original || "").replace(/\s+/g, " ").trim();
        const p = (e.proposed || "").replace(/\s+/g, " ").trim();
        if (!o || !p || o === p || o === "…") return false;
        const norm = (s: string) =>
          s
            .replace(/[\u064B-\u065F\u0670\u0640]/g, "")
            .replace(/[،,.;:؟!?()[\]‹›«»"'\-–—/]/g, "")
            .replace(/[أإآ]/g, "ا")
            .replace(/ة/g, "ه")
            .replace(/\s+/g, "");
        return norm(o) !== norm(p);
      });
      setFormEdits(realEdits);
      setPleaVariables(res.variables || []);
      setEditingPolished(false);
      const guessed = Array.isArray(res.guessed_words)
        ? res.guessed_words.length
        : (out.match(/‹[^›]{1,80}›/g) || []).length;
      const nAlert = (res.contradictions || []).length;
      const degraded = (res.provider || "") === "fidelity" || (res.provider || "") === "none";
      const plainOut = (out || "").replace(/[‹›]/g, "").replace(/\s+/g, " ").trim();
      const plainIn = cleaned.replace(/[‹›]/g, "").replace(/\s+/g, " ").trim();
      const changed = plainOut !== plainIn;
      // Ne pas afficher « aucune contradiction » comme succès de réécriture si rien n’a bougé
      // et qu’il n’y a pas non plus d’alertes — le bandeau message suffit (peu de changements).
      setMessage(
        uiFr
          ? [
              degraded
                ? changed
                  ? guessed
                    ? `Correction de forme (fusḥā locale) — faits conservés · ${guessed} substitution(s) STT ‹…›`
                    : "Correction de forme (fusḥā locale) — faits conservés."
                  : "Correction locale — peu de changements détectés (texte déjà correct ?)."
                : guessed
                  ? `Correction ChatGPT (fusḥā) — ${guessed} mot(s) STT ‹…›`
                  : "Correction ChatGPT appliquée (forme fusḥā, sans résumé inventé).",
              nAlert ? `· ${nAlert} alerte(s)` : "",
            ]
              .filter(Boolean)
              .join(" ")
          : [
              degraded
                ? changed
                  ? guessed
                    ? `تم التصحيح الشكلي (فصحى محلية) — مع الحفاظ على الوقائع · ${guessed} استبدال STT ‹…›`
                    : "تم التصحيح الشكلي (فصحى محلية) — مع الحفاظ على كل الوقائع."
                  : "تصحيح محلي — تغييرات قليلة (النص قد يكون سليماً أصلاً)."
                : guessed
                  ? `تصحيح ChatGPT (فصحى) — ${guessed} استبدال ‹…›`
                  : "طُبّق تصحيح ChatGPT (فصحى شكلية دون تلخيص).",
              nAlert ? `· ${nAlert} تنبيه` : "",
            ]
              .filter(Boolean)
              .join(" "),
      );
      pushToast(
        degraded
          ? uiFr
            ? "Correction locale appliquée"
            : "طُبّق التصحيح المحلي"
          : uiFr
            ? "Correction ChatGPT réussie"
            : "نجاح تصحيح ChatGPT",
        degraded ? "info" : "success",
      );
      setStep(2);
    } catch (e) {
      if (gen !== polishGenRef.current) return;
      // Secours : dédoublonnage local minimal — JAMAIS « aucune contradiction »
      const fallback = stripStars(
        lightCleanDictation(cleaned).replace(/(\S+)(?:\s+\1)+/gu, "$1"),
      );
      setPolished(fallback);
      setProvider("fidelity");
      setContradictions([]);
      setContradictionCheck("unchecked");
      setFormEdits([]);
      setPleaVariables([]);
      setMessage(
        uiFr
          ? "⚠️ Service de vérification indisponible. Les contradictions (n°, dates, noms, montants) n’ont PAS été vérifiées. Relisez attentivement ou réessayez."
          : "⚠️ خدمة التحقق غير متاحة. لم يتم فحص التناقضات (أرقام، تواريخ، أسماء، مبالغ). راجعوا النص بعناية أو أعيدوا المحاولة.",
      );
      setError(e instanceof ApiError ? e.message : "");
    } finally {
      if (gen === polishGenRef.current) setBusy(null);
    }
  }

  function applyContradictionChoice(kind: string, chosen: string | null) {
    // null = garder les deux
    if (!chosen) {
      setContradictions((prev) => prev.filter((c) => c.kind !== kind));
      return;
    }
    const alert = contradictions.find((c) => c.kind === kind);
    if (!alert) return;
    let next = polished || raw;
    const expandVariants = (v: string) => {
      const forms = new Set<string>([v]);
      if (v.includes("/")) forms.add(v.replace(/\//g, " على "));
      if (v.includes(" على ")) forms.add(v.replace(/\s*على\s*/g, "/"));
      return [...forms];
    };
    for (const v of alert.values) {
      if (v === chosen) continue;
      for (const form of expandVariants(v)) {
        const esc = form.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        next = next.replace(new RegExp(esc, "g"), chosen.includes("/") && form.includes(" على ")
          ? chosen.replace(/\//g, " على ")
          : chosen);
      }
    }
    setPolished(next);
    setContradictions((prev) => prev.filter((c) => c.kind !== kind));
    setMessage(
      uiFr
        ? `Choix enregistré (${kind}): ${chosen}`
        : `تم اعتماد الاختيار: ${chosen}`,
    );
  }

  async function startClarifyFlow(): Promise<void> {
    const source = cleanDictationNoise(
      (polished || raw).replace(/‹([^›]+)›/g, "$1"),
    );
    if (!source) {
      setError(
        uiFr
          ? "L’IA ne rédige pas une plaidoirie à partir de rien : dictez, importez un audio, ou joignez des pièces. Elle n’invente pas les faits."
          : "الذكاء الاصطناعي لا يحرر مرافعة من فراغ: أملوا أو ارفعوا صوتاً أو قطعاً. لا يختلق الوقائع.",
      );
      return;
    }
    if (looksLikeGibberish(source)) {
      setSenseAlert(
        uiFr
          ? "Impossible de rédiger : le texte corrigé n’a pas de sens. Dictez les faits (parties, objet, demande) avant de lancer l’IA."
          : "تعذّرت الصياغة: النص بلا معنى. أملوا الوقائع (الأطراف، الموضوع، الطلب) قبل تشغيل الذكاء.",
      );
      goStep(2);
      return;
    }
    if (!caseId) {
      setError(
        uiFr
          ? "Un dossier est obligatoire. Les pièces jointes sont facultatives : sans pièces, l’IA s’appuie sur votre dictée et la fiche du dossier."
          : "الملف إلزامي للصياغة (المرفقات وإخفاء أسماء الأطراف).",
      );
      goStep(0);
      return;
    }
    const caseNow = cases.find((c) => c.id === caseId);
    if (caseNow) {
      const gaps = missingLegalFields(caseNow);
      if (gaps.length) {
        setError(
          uiFr
            ? "⚠️ Complétez et enregistrez l’identité juridique avant de générer."
            : "⚠️ أكملوا الهوية القانونية قبل التوليد.",
        );
        goStep(0);
        return;
      }
    }
    // Logo cabinet : proposer upload ou continuer sans (sans perdre le formulaire)
    if (!cabinetLogoUrl && !skipLogoForCompose && !user?.cabinet_has_logo) {
      setLogoPromptOpen(true);
      return;
    }
    setError("");
    setMessage("");
    setClarifyData(null);
    setClarifyOpen(true);
    setClarifyLoading(true);
    try {
      const composeType =
        actTypeToTemplate(actType, caseNow?.case_type) ||
        pleaType ||
        inferComposeType(
          source,
          templateId,
          selectedCustom ? selectedCustom.base_type || "custom" : undefined,
        );
      const postureLabel =
        briefPosture === "defendeur"
          ? "défendeur"
          : briefPosture === "partie-civile"
            ? "partie civile"
            : briefPosture === "appelant"
              ? "appelant"
              : "demandeur";
      const tribunalOpt = TRIBUNAL_OPTIONS.find((t) => t.value === caseNow?.tribunal);
      const degreeOpt = JURISDICTION_DEGREES.find(
        (d) => d.value === caseNow?.jurisdiction_degree,
      );
      const jurLabel =
        tribunalOpt?.fr ||
        (briefJurisdiction === "commerce"
          ? "tribunal de commerce"
          : briefJurisdiction === "admin"
            ? "tribunal administratif"
            : briefJurisdiction === "appel"
              ? "cour d’appel"
              : briefJurisdiction === "cassation"
                ? "Cour de cassation"
                : "tribunal de première instance");
      const actLabel = ACT_TYPES.find((a) => a.value === actType)?.fr || actType;
      const res = await api.clarifyDictation({
        text: source,
        case_id: caseId,
        plaidoirie_type: composeType,
        language: dictationLang,
        brief_posture: postureLabel,
        brief_jurisdiction: [jurLabel, degreeOpt?.fr, actLabel].filter(Boolean).join(" · ").slice(0, 180),
      });
      void notifySpend("clarify");
      setClarifyData(res);
      if (!res.questions?.length) {
        setClarifyOpen(false);
        await runComposeWithClarifications([]);
      }
    } catch (e) {
      setClarifyOpen(false);
      setMessage(
        uiFr
          ? "Clarification indisponible — rédaction directe…"
          : "التوضيح غير متاح — صياغة مباشرة…",
      );
      await runComposeWithClarifications([]);
      if (e instanceof ApiError) {
        /* already composing */
      }
    } finally {
      setClarifyLoading(false);
    }
  }

  async function runComposeWithClarifications(
    clarifications: ClarifyAnswer[],
  ): Promise<boolean> {
    const source = cleanDictationNoise(
      (polished || raw).replace(/‹([^›]+)›/g, "$1"),
    );
    if (!source || !caseId) return false;
    const caseNow = cases.find((c) => c.id === caseId);
    setClarifyOpen(false);
    setBusy("compose");
    setError("");
    setMessage("");
    try {
      const composeType =
        actTypeToTemplate(actType, caseNow?.case_type) ||
        pleaType ||
        inferComposeType(
          source,
          templateId,
          selectedCustom ? selectedCustom.base_type || "custom" : undefined,
        );
      const postureLabel =
        briefPosture === "defendeur"
          ? "défendeur"
          : briefPosture === "partie-civile"
            ? "partie civile"
            : briefPosture === "appelant"
              ? "appelant"
              : "demandeur";
      const tribunalOpt = TRIBUNAL_OPTIONS.find((t) => t.value === caseNow?.tribunal);
      const degreeOpt = JURISDICTION_DEGREES.find(
        (d) => d.value === caseNow?.jurisdiction_degree,
      );
      const jurLabel =
        tribunalOpt?.fr ||
        (briefJurisdiction === "commerce"
          ? "tribunal de commerce"
          : briefJurisdiction === "admin"
            ? "tribunal administratif"
            : briefJurisdiction === "appel"
              ? "cour d’appel"
              : briefJurisdiction === "cassation"
                ? "Cour de cassation"
                : "tribunal de première instance");
      const actLabel = ACT_TYPES.find((a) => a.value === actType)?.fr || actType;
      const res = await api.composeDictation({
        text: source,
        doc_type: "plaidoirie",
        polish_first: false,
        plaidoirie_type: composeType,
        title: docTitle || selectedCustom?.name || selectedTemplate?.labelAr,
        language: dictationLang,
        case_id: caseId || undefined,
        brief_posture: postureLabel,
        brief_jurisdiction: [jurLabel, degreeOpt?.fr, actLabel].filter(Boolean).join(" · ").slice(0, 180),
        clarifications: clarifications.length ? clarifications : undefined,
      });
      if (res.polished) setPolished(fixArabicBidiDisplay(res.polished));
      setDocTitle(
        stripStars(
          res.title || selectedCustom?.name || selectedTemplate?.labelAr || "مرافعة",
        ),
      );
      setDocBody(fixArabicBidiDisplay(structurePlaidoirieBody(stripStars(res.body))));
      setComposeChecks(res.checks || []);
      setProvider(res.provider);
      void notifySpend("compose");
      try {
        const d = await api.savePlaidoirieDraft({
          title: stripStars(res.title || docTitle || "مرافعة"),
          body: stripStars(structurePlaidoirieBody(res.body || "")),
          template_id: templateId,
          case_id: caseId || undefined,
          checks: res.checks || [],
        });
        if (d?.id) setSavedDraftId(d.id);
        setDraftsHint(
          uiFr
            ? "Trace enregistrée dans l’historique des plaidoiries."
            : "تم حفظ أثر المرافعة في السجل.",
        );
      } catch {
        /* non bloquant */
      }
      if (res.degraded || res.provider === "none") {
        setMessage(
          res.message ||
            (uiFr
              ? "Rédaction IA indisponible — document minimal à partir de votre texte."
              : "التحرير بالذكاء الاصطناعي غير متاح — وثيقة مبسطة من نصك."),
        );
      } else if (res.pii_masked) {
        setMessage(
          uiFr
            ? "Plaidoirie générée. Confidentialité : noms des parties remplacés par PARTIE_A / PARTIE_B avant l’IA, puis remis dans le texte final."
            : "تمت الصياغة. السرية: أُبدلت أسماء الأطراف بـ PARTIE_A / PARTIE_B قبل الذكاء الاصطناعي ثم أُعيدت في النص النهائي.",
        );
      } else if (res.case_enriched) {
        setMessage(
          uiFr
            ? "Plaidoirie générée à partir du dossier, des pièces et de votre dictée."
            : "تمت الصياغة من الملف والمرفقات وإملائكم.",
        );
      } else {
        setMessage(
          uiFr
            ? `Plaidoirie rédigée par ChatGPT (${res.provider || "gpt-4o"}).`
            : `صاغ ChatGPT المرافعة (${res.provider || "gpt-4o"}).`,
        );
      }
      pushToast(
        uiFr ? "Plaidoirie générée par l’IA" : "أُنشئت المرافعة بالذكاء",
        res.degraded ? "info" : "success",
      );
      goStep(3);
      return true;
    } catch (e) {
      setDocTitle(selectedCustom?.name || selectedTemplate?.labelAr || "مرافعة");
      setDocBody(structurePlaidoirieBody(source));
      setComposeChecks([]);
      setProvider("none");
      setError(e instanceof ApiError ? e.message : "Génération indisponible.");
      return true;
    } finally {
      setBusy(null);
    }
  }

  /** @deprecated use startClarifyFlow — kept for any residual calls */
  async function handleCompose(): Promise<boolean> {
    await startClarifyFlow();
    return true;
  }

  const titledDoc = docTitle || "مرافعة";
  const selectedCase = cases.find((c) => c.id === caseId);
  const legalGaps = selectedCase
    ? missingLegalFields({
        ...selectedCase,
        jurisdiction_degree: selectedCase.jurisdiction_degree || legalDraft.jurisdiction_degree,
        client_role: selectedCase.client_role || legalDraft.client_role,
      })
    : ["dossier"];
  // Gaps based on saved case only (not draft) — pour le bouton Continuer
  const savedLegalGaps = selectedCase ? missingLegalFields(selectedCase) : ["dossier"];
  const rolesHelp = roleHelp(uiFr);

  async function saveLegalInline(): Promise<boolean> {
    if (!caseId || !selectedCase) return false;
    if (!legalDraft.jurisdiction_degree || !legalDraft.client_role) {
      setError(
        uiFr
          ? "⚠️ Indiquez le degré de juridiction et le rôle de votre client."
          : "⚠️ حدّدوا درجة التقاضي ودور الموكل.",
      );
      return false;
    }
    setLegalSaving(true);
    setError("");
    try {
      const updated = await api.updateCase(caseId, {
        jurisdiction_degree: legalDraft.jurisdiction_degree,
        tribunal: legalDraft.tribunal || suggestTribunal(selectedCase.case_type, legalDraft.jurisdiction_degree),
        client_role: legalDraft.client_role,
        client_quality: legalDraft.client_quality || undefined,
        client_domicile: legalDraft.client_domicile.trim() || undefined,
        opposing_name: legalDraft.opposing_name.trim() || undefined,
        opposing_role: opposingRoleFor(legalDraft.client_role),
        opposing_quality: legalDraft.opposing_quality || undefined,
        opposing_domicile: legalDraft.opposing_domicile.trim() || undefined,
      });
      setCases((prev) => prev.map((c) => (c.id === caseId ? { ...c, ...updated } : c)));
      setMessage(
        uiFr
          ? "Identité juridique enregistrée sur le dossier — vous pouvez continuer."
          : "تم حفظ الهوية القانونية على الملف — يمكن المتابعة.",
      );
      return true;
    } catch (e) {
      setError(e instanceof ApiError ? e.message : uiFr ? "Enregistrement impossible." : "تعذر الحفظ.");
      return false;
    } finally {
      setLegalSaving(false);
    }
  }

  useEffect(() => {
    if (!selectedCase) return;
    setBriefPosture(roleToBriefPosture(selectedCase.client_role));
    setBriefJurisdiction(
      degreeToBriefJurisdiction(selectedCase.jurisdiction_degree, selectedCase.tribunal),
    );
    setLegalDraft({
      jurisdiction_degree: selectedCase.jurisdiction_degree || "premiere_instance",
      tribunal:
        selectedCase.tribunal ||
        suggestTribunal(selectedCase.case_type, selectedCase.jurisdiction_degree || "premiere_instance"),
      client_role:
        selectedCase.client_role ||
        partyRoleOptions(selectedCase.case_type)[0]?.value ||
        "demandeur",
      client_quality: selectedCase.client_quality || "personne_physique",
      client_domicile: selectedCase.client_domicile || "",
      opposing_name: selectedCase.opposing_name || "",
      opposing_quality: selectedCase.opposing_quality || "personne_physique",
      opposing_domicile: selectedCase.opposing_domicile || "",
    });
    if (selectedCase.case_type) {
      setPleaType(actTypeToTemplate(actType, selectedCase.case_type));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    selectedCase?.id,
    selectedCase?.client_role,
    selectedCase?.jurisdiction_degree,
    selectedCase?.tribunal,
    selectedCase?.case_type,
    selectedCase?.client_quality,
    selectedCase?.client_domicile,
    selectedCase?.opposing_name,
    selectedCase?.opposing_quality,
    selectedCase?.opposing_domicile,
  ]);

  useEffect(() => {
    setPleaType(actTypeToTemplate(actType, selectedCase?.case_type));
  }, [actType, selectedCase?.case_type]);

  const exportPayload = {
    title: titledDoc,
    body: structurePlaidoirieBody(docBody),
    cabinet_name: cabinetNameFr || undefined,
    lawyer_name: lawyerDisplayName,
    city: user?.cabinet_city || undefined,
    case_reference: selectedCase?.reference,
    client_name: selectedCase?.client_name,
    include_esignature: false as const,
  };
  const exportOpts = {
    title: titledDoc,
    body: structurePlaidoirieBody(docBody),
    cabinetName: cabinetNameFr || cabinetDisplayName,
    cabinetNameAr: cabinetNameAr,
    headerFr: cabinetNameFr || cabinetDisplayName,
    headerAr: cabinetNameAr,
    lawyerName: lawyerDisplayName,
    city: user?.cabinet_city || undefined,
    cabinetLogoUrl,
    includeEsignature: false,
  };

  async function handleSaveToCase() {
    if (!docBody.trim()) return;
    if (!caseId) {
      setError("Choisissez un dossier.");
      return;
    }
    const ok = await confirm({
      title: uiFr ? "Joindre au dossier ?" : "إرفاق بالملف؟",
      description: uiFr
        ? "Le Word est ajouté aux pièces du dossier lié. Vous pourrez toujours ré-exporter."
        : "يُضاف ملف Word إلى مرفقات الملف المرتبط. يمكن إعادة التصدير لاحقًا.",
      confirmLabel: uiFr ? "Joindre au dossier" : "إرفاق بالملف",
    });
    if (!ok) return;
    setBusy("save");
    setError("");
    setMessage("");
    try {
      const { blob, filename } = await api.fetchPlaidoirieDocx(exportPayload);
      const file = new File(
        [blob],
        filename.endsWith(".docx") ? filename : "plaidoirie.docx",
        { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" },
      );
      await api.uploadDocument(caseId, file);
      setMessage("Enregistré.");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Échec de l’enregistrement");
    } finally {
      setBusy(null);
    }
  }

  if (!ready) {
    return (
      <div className="section-sub" style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <Loader2 className="h-4 w-4 animate-spin" />
        …
      </div>
    );
  }

  const stepStatuses: PleaStepStatus[] = PLEA_STEPS.map((s, i) => {
    if (i === step) return "current";
    const done =
      (s.id === "dictate" && (raw.trim().length > 0 || recording || transcribing)) ||
      (s.id === "transcript" && (raw.trim().length > 12 || !!polished.trim())) ||
      (s.id === "settings" && (settingsVisited || !!caseId)) ||
      (s.id === "document" && !!docBody.trim()) ||
      (s.id === "export" && exportedDone);
    return done ? "done" : "todo";
  });

  function goStep(i: number) {
    if (i === 0) setSettingsVisited(true);
    if (i > 0 && !caseId) {
      setError(
        uiFr
          ? "Liez d’abord un dossier : la plaidoirie s’appuie sur les pièces et les parties."
          : "اربطوا ملفاً أولاً: المرافعة تعتمد على القطع والأطراف.",
      );
      setStep(0);
      return;
    }
    if (i > 0 && selectedCase) {
      const gaps = missingLegalFields(selectedCase);
      if (gaps.length) {
        setError(
          uiFr
            ? "⚠️ Complétez et enregistrez l’identité juridique ci-dessous (degré + rôle) avant de continuer — sans quitter cet écran."
            : "⚠️ أكملوا واحفظوا الهوية القانونية أدناه قبل المتابعة — دون مغادرة الشاشة.",
        );
        setStep(0);
        return;
      }
    }
    if (i > 0 && !actType) {
      setError(
        uiFr
          ? "⚠️ Choisissez le type d’acte à produire pour ce dossier."
          : "⚠️ اختاروا نوع الوثيقة المراد إنتاجها لهذا الملف.",
      );
      setStep(0);
      return;
    }
    setError("");
    if (i === 4) setComposeChecks([]);
    setStep(i);
  }

  const usefulChecks = composeChecks.filter((c) => {
    const t = (c || "").trim().toLowerCase();
    return t && t !== "لا شيء" && t !== "aucun" && t !== "none" && t !== "—" && t !== "-";
  });
  const showMissingChecks = usefulChecks.length > 0 && step < 4 && !exportedDone;

  return (
    <>
    <ComposeProgressOverlay open={busy === "compose"} uiFr={uiFr} hasPieces={(caseDocCount || 0) > 0} />
      {logoPromptOpen ? (
        <div
          className="fixed inset-0 z-[9990] flex items-center justify-center bg-[#0B1A4D]/45 p-4"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl">
            <h3 className="text-lg font-semibold text-[#0B1A4D]">
              {uiFr ? "Logo du cabinet manquant" : "شعار المكتب غير محمّل"}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              {uiFr
                ? "Vous n’avez pas encore uploadé le logo. Continuer sans logo (noms AR/FR seulement) ou uploader maintenant — votre dictée et le formulaire sont conservés."
                : "لم ترفعوا شعار المكتب بعد. يمكن المتابعة بلا شعار (الأسماء فقط) أو الرفع الآن — الإملاء والنموذج محفوظان."}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-[#0B1A4D]"
                onClick={() => {
                  setSkipLogoForCompose(true);
                  setLogoPromptOpen(false);
                  void startClarifyFlow();
                }}
              >
                {uiFr ? "Continuer sans logo" : "المتابعة بلا شعار"}
              </button>
              <button
                type="button"
                className="rounded-lg bg-[#0B1A4D] px-3 py-2 text-sm font-medium text-white"
                onClick={() => {
                  setLogoPromptOpen(false);
                  window.open("/settings#cabinet", "_blank", "noopener,noreferrer");
                }}
              >
                {uiFr ? "Uploader le logo" : "رفع الشعار"}
              </button>
              <button
                type="button"
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-600"
                onClick={() => setLogoPromptOpen(false)}
              >
                {uiFr ? "Annuler" : "إلغاء"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    <PleaClarifySheet
      open={clarifyOpen}
      uiFr={uiFr}
      loading={clarifyLoading}
      data={clarifyData}
      onClose={() => {
        setClarifyOpen(false);
        setClarifyLoading(false);
      }}
      onSkip={() => void runComposeWithClarifications([])}
      onConfirm={(answers) => void runComposeWithClarifications(answers)}
    />
    <div>
      <div className="dossiers-top" style={{ marginBottom: 20, display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div className="section-title" style={{ marginBottom: 4 }} dir={uiFr ? "ltr" : "rtl"}>
            {templateLabel}
          </div>
          <div className="section-sub" style={{ marginBottom: 0 }}>
            {uiFr
              ? "Dossier & pièces → dictée → transcription → rédaction IA → export"
              : "الملف والمرفقات ← إملاء ← تفريغ ← صياغة بالذكاء ← تصدير"}
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
          {step === 4 ? (
            <a href="/redaction/new" className="chip-btn primary" style={{ whiteSpace: "nowrap" }}>
              {uiFr ? "Nouvelle plaidoirie" : "مرافعة جديدة"}
            </a>
          ) : null}
          <a
            href="/redaction"
            className="chip-btn"
            title={uiFr ? "Retour aux modèles de plaidoirie" : "العودة إلى نماذج المرافعات"}
            aria-label={uiFr ? "Fermer" : "إغلاق"}
            style={{
              width: 40,
              height: 40,
              padding: 0,
              borderRadius: 999,
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <X width={18} height={18} />
          </a>
        </div>
      </div>

      {(message || error || senseAlert) && (
        <div className="space-y-2" style={{ marginBottom: 14 }} dir={uiFr ? "ltr" : "rtl"}>
          {senseAlert ? (
            <p
              role="alert"
              style={{
                margin: 0,
                fontSize: 13.5,
                fontWeight: 650,
                color: "#9a3412",
                background: "rgba(255, 237, 213, 0.95)",
                border: "1px solid rgba(234, 88, 12, 0.45)",
                borderRadius: 12,
                padding: "10px 13px",
                lineHeight: 1.55,
              }}
            >
              {senseAlert}
            </p>
          ) : null}
          {message ? (
            <p
              role="status"
              style={{
                margin: 0,
                fontSize: 13,
                fontWeight: 600,
                color: "#b45309",
                background: "rgba(245, 158, 11, 0.12)",
                border: "1px solid rgba(180, 83, 9, 0.35)",
                borderRadius: 10,
                padding: "8px 12px",
              }}
            >
              {message}
            </p>
          ) : null}
          {error ? (
            <p
              role="alert"
              style={{
                margin: 0,
                fontSize: 13,
                fontWeight: 600,
                color: "#b91c1c",
                background: "rgba(185, 28, 28, 0.08)",
                border: "1px solid rgba(185, 28, 28, 0.3)",
                borderRadius: 10,
                padding: "8px 12px",
              }}
            >
              {error}
            </p>
          ) : null}
        </div>
      )}

      {showMissingChecks && (
        <div dir={uiFr ? "ltr" : "rtl"} style={{ marginBottom: 14 }}>
          <button
            type="button"
            onClick={() => setChecksOpen((v) => !v)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 10,
              borderRadius: 999,
              border: "1px solid rgba(180, 83, 9, 0.35)",
              background: "rgba(245, 158, 11, 0.12)",
              padding: "6px 12px",
              fontSize: 13,
              fontWeight: 700,
              color: "#92400e",
              cursor: "pointer",
            }}
          >
            <span>
              {uiFr
                ? `${usefulChecks.length} info${usefulChecks.length > 1 ? "s" : ""} manquante${usefulChecks.length > 1 ? "s" : ""}`
                : `${usefulChecks.length} معلومة ناقصة`}
            </span>
            <span
              style={{
                width: 72,
                height: 6,
                borderRadius: 99,
                background: "rgba(146, 64, 14, 0.2)",
                overflow: "hidden",
              }}
            >
              <span
                style={{
                  display: "block",
                  height: "100%",
                  width: `${Math.max(15, 100 - usefulChecks.length * 18)}%`,
                  background: "#d97706",
                  borderRadius: 99,
                }}
              />
            </span>
            <span style={{ fontSize: 11, fontWeight: 600 }}>
              {Math.max(15, 100 - usefulChecks.length * 18)}%
            </span>
          </button>
          {checksOpen && (
            <div
              style={{
                marginTop: 8,
                padding: "10px 14px",
                borderRadius: 12,
                background: "rgba(255,255,255,0.92)",
                border: "1px solid rgba(14,21,38,0.1)",
                fontSize: 13,
              }}
            >
              <p style={{ margin: "0 0 8px", color: "var(--ink-soft)", lineHeight: 1.5 }}>
                {uiFr
                  ? "Ces éléments manquent dans votre dictée. Complétez-les dans le texte (étape Transcription) ou dans le document avant export — ils ne seront pas inventés automatiquement."
                  : "هذه المعلومات ناقصة في إملائكم. أضيفوها في التفريغ أو في الوثيقة قبل التصدير — لن تُختلَق تلقائياً."}
              </p>
              <ul style={{ margin: 0, paddingInlineStart: 28 }}>
              {usefulChecks.map((c) => (
                <li key={c} style={{ marginBottom: 4 }}>
                  {c}
                </li>
              ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 10,
          marginBottom: 12,
          padding: "10px 14px",
          borderRadius: 14,
          border: "1px solid rgba(27,63,156,0.14)",
          background: "rgba(27,63,156,0.05)",
        }}
      >
        <p style={{ margin: 0, fontSize: 12, color: "var(--ink-soft)", lineHeight: 1.45 }}>
          {uiFr
            ? "Progression sauvegardée automatiquement. Restez dans cet atelier jusqu’à l’export — pas besoin de retourner aux dossiers."
            : "يُحفظ التقدّم تلقائياً. ابقوا في هذه الورشة حتى التصدير — لا حاجة للعودة إلى الملفات."}
        </p>
      </div>

      <PleaStepCarousel
        step={step}
        onStepChange={goStep}
        statuses={stepStatuses}
        uiFr={uiFr}
      />

      <div className="plea-workspace">
        {/* 0 — Dossier & pièces */}
        <div className="plea-step-panel" style={{ display: step === 0 ? "block" : "none" }}>
          <div className="card doc-preview">
            <span className="badge">{uiFr ? "Étape 1 · Dossier" : "الخطوة ١ · الملف"}</span>
            <p style={{ fontSize: 12, lineHeight: 1.45, color: "var(--ink-soft)", margin: "0 0 12px", padding: "8px 10px", borderRadius: 10, background: "rgba(27,63,156,0.06)", border: "1px solid rgba(27,63,156,0.12)" }}>
              {uiFr
                ? "L’IA rédige à partir de 3 sources : fiche dossier (matière, degré, tribunal, rôles, nature personne physique/morale) + pièces OCR + votre dictée. Confidentialité cabinet : les vrais noms deviennent PARTIE_A / PARTIE_B avant l’IA, puis sont restaurés dans le document final."
                : "الذكاء الاصطناعي يصوغ من 3 مصادر: بطاقة الملف + المرفقات + إملاؤكم. السرية: تُستبدل الأسماء بـ PARTIE_A قبل الإرسال ثم تُعاد في الوثيقة النهائية."}
            </p>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 12, padding: "12px 14px", borderRadius: 12, border: "1px solid var(--line)", background: "rgba(255,252,246,0.9)", direction: "ltr" }}>
              <div style={{ flex: 1, textAlign: "right", direction: "rtl", fontWeight: 700, color: "#1a3a2a", fontSize: 13 }}>
                {cabinetNameAr || (uiFr ? "Nom arabe du cabinet" : "اسم المكتب بالعربية")}
              </div>
              <div style={{ flex: "0 0 auto", minWidth: 72, minHeight: 44, display: "flex", alignItems: "center", justifyContent: "center" }}>
                {cabinetLogoUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={cabinetLogoUrl} alt="Logo cabinet" style={{ height: 44, width: "auto", maxWidth: 120, objectFit: "contain" }} />
                ) : (
                  <span style={{ fontSize: 11, color: "var(--ink-soft)" }}>{uiFr ? "(logo)" : "(شعار)"}</span>
                )}
              </div>
              <div style={{ flex: 1, textAlign: "left", direction: "ltr", fontWeight: 700, color: "#0B1A4D", fontSize: 13 }}>
                {cabinetNameFr || (uiFr ? "Nom français du cabinet" : "الاسم بالفرنسية")}
              </div>
            </div>
            {!cabinetLogoUrl ? (
              <p style={{ fontSize: 12, color: "var(--ink-soft)", margin: "0 0 12px" }}>
                {uiFr
                  ? "Astuce : uploadez le logo dans Paramètres → Cabinet pour l’en-tête Word."
                  : "نصيحة: ارفعوا الشعار من الإعدادات ← المكتب لترويسة Word."}
              </p>
            ) : null}

            <label style={{ display: "block", fontSize: 12, fontWeight: 700, color: "var(--ink-soft)", marginBottom: 6 }}>
              {uiFr ? "Dossier lié" : "الملف المرتبط"}
            </label>
            <select
              value={caseId}
              onChange={(e) => {
                const v = e.target.value;
                if (v === "__new__") {
                  setShowNewCase(true);
                  return;
                }
                const s = loadPleaSession();
                if (v && s?.caseId && s.caseId !== v) {
                  setRaw("");
                  setPolished("");
                  setComposeChecks([]);
                  setDocBody("");
                }
                setCaseId(v);
              }}
              style={{ width: "100%", border: "1px solid var(--line)", borderRadius: 12, padding: "11px 12px", marginBottom: 8, background: "var(--parchment)" }}
            >
              <option value="">{uiFr ? "— Choisissez un dossier (obligatoire) —" : "— اختاروا ملفاً (إلزامي) —"}</option>
              <option value="__new__">{uiFr ? "＋ Créer un nouveau dossier…" : "＋ إنشاء ملف جديد…"}</option>
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.reference} — {c.client_name}
                </option>
              ))}
            </select>
            {selectedCase ? (
              <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10, marginBottom: 12, fontSize: 12, color: "var(--ink-soft)" }}>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                  <FolderOpen size={14} />
                  {caseDocCount != null
                    ? uiFr
                      ? `${caseDocCount} pièce(s) indexée(s)`
                      : `${caseDocCount} مرفق(ات) مفهرسة`
                    : uiFr
                      ? "Chargement des pièces…"
                      : "جاري تحميل المرفقات…"}
                </span>
                <button
                  type="button"
                  className="chip-btn"
                  style={{ fontSize: 11, padding: "4px 10px" }}
                  onClick={() => setStep1Open("pieces")}
                >
                  {uiFr ? "Voir / ajouter des pièces" : "عرض / إضافة مرفقات"}
                </button>
              </div>
            ) : (
              <p style={{ fontSize: 11, color: "#b45309", marginBottom: 14, fontWeight: 600 }}>
                {uiFr
                  ? "Sans dossier, pas de dictée ni de rédaction. Les pièces, elles, sont optionnelles."
                  : "بدون ملف لا إملاء ولا صياغة. المرفقات اختيارية."}
              </p>
            )}

            {caseId ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 14 }}>
                {/* —— Accordion 1 : Identité —— */}
                <div style={{ border: "1px solid var(--line)", borderRadius: 14, overflow: "hidden", background: "#fff" }}>
                  <button
                    type="button"
                    onClick={() => setStep1Open(step1Open === "identite" ? "suite" : "identite")}
                    style={{
                      width: "100%",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: 10,
                      padding: "12px 14px",
                      border: "none",
                      background: step1Open === "identite" ? "rgba(27,63,156,0.06)" : "transparent",
                      cursor: "pointer",
                      textAlign: "start",
                    }}
                  >
                    <span style={{ fontSize: 13, fontWeight: 700, color: "#1B3F9C" }}>
                      {uiFr ? "1 · Identité juridique & type d’acte" : "١ · الهوية القانونية ونوع الوثيقة"}
                    </span>
                    <ChevronDown
                      size={18}
                      style={{
                        flexShrink: 0,
                        color: "var(--ink-soft)",
                        transform: step1Open === "identite" ? "rotate(180deg)" : "none",
                        transition: "transform .2s ease",
                      }}
                    />
                  </button>
                  {step1Open === "identite" && selectedCase ? (
                    <div
                      style={{
                        padding: "4px 14px 14px",
                        borderTop: "1px solid var(--line)",
                        border: savedLegalGaps.length
                          ? "1px solid rgba(185,28,28,0.35)"
                          : undefined,
                        background: savedLegalGaps.length ? "rgba(254,226,226,0.25)" : undefined,
                      }}
                    >
                      <p style={{ margin: "10px 0 10px", fontSize: 11, color: "var(--ink-soft)", lineHeight: 1.45 }}>
                        {qualityHelp(uiFr)}
                      </p>
                      <p style={{ margin: "0 0 10px", fontSize: 11, color: "var(--ink-soft)", lineHeight: 1.45 }}>
                        {rolesHelp.demandeur} {rolesHelp.defendeur}
                      </p>
                      {savedLegalGaps.length > 0 ? (
                        <p style={{ margin: "0 0 10px", fontSize: 12, fontWeight: 600, color: "#991b1b" }}>
                          {uiFr
                            ? `À compléter : ${savedLegalGaps.join(", ")}. Enregistrez ci-dessous — sans quitter.`
                            : `أكملوا: ${savedLegalGaps.join("، ")}. احفظوا أدناه دون مغادرة.`}
                        </p>
                      ) : null}
                      <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
                        <label style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>
                          {uiFr ? "Degré *" : "الدرجة *"}
                          <select
                            value={legalDraft.jurisdiction_degree}
                            onChange={(e) => {
                              const d = e.target.value;
                              setLegalDraft((prev) => ({
                                ...prev,
                                jurisdiction_degree: d,
                                tribunal: suggestTribunal(selectedCase.case_type, d),
                              }));
                            }}
                            style={{ display: "block", width: "100%", marginTop: 4, border: "1px solid var(--line)", borderRadius: 10, padding: "9px 10px", background: "#fff" }}
                          >
                            {JURISDICTION_DEGREES.map((d) => (
                              <option key={d.value} value={d.value}>
                                {uiFr ? d.fr : d.ar}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>
                          {uiFr ? "Tribunal" : "المحكمة"}
                          <select
                            value={legalDraft.tribunal}
                            onChange={(e) => setLegalDraft((prev) => ({ ...prev, tribunal: e.target.value }))}
                            style={{ display: "block", width: "100%", marginTop: 4, border: "1px solid var(--line)", borderRadius: 10, padding: "9px 10px", background: "#fff" }}
                          >
                            {TRIBUNAL_OPTIONS.map((tOpt) => (
                              <option key={tOpt.value} value={tOpt.value}>
                                {uiFr ? tOpt.fr : tOpt.ar}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>
                          {uiFr ? "Votre client est *" : "موكلكم هو *"}
                          <select
                            value={legalDraft.client_role}
                            onChange={(e) => setLegalDraft((prev) => ({ ...prev, client_role: e.target.value }))}
                            style={{ display: "block", width: "100%", marginTop: 4, border: "1px solid var(--line)", borderRadius: 10, padding: "9px 10px", background: "#fff" }}
                          >
                            {partyRoleOptions(selectedCase.case_type).map((r) => (
                              <option key={r.value} value={r.value}>
                                {uiFr ? r.fr : r.ar}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>
                          {uiFr ? "Nature du client" : "طبيعة الموكل"}
                          <select
                            value={legalDraft.client_quality}
                            onChange={(e) => setLegalDraft((prev) => ({ ...prev, client_quality: e.target.value }))}
                            style={{ display: "block", width: "100%", marginTop: 4, border: "1px solid var(--line)", borderRadius: 10, padding: "9px 10px", background: "#fff" }}
                          >
                            {QUALITY_OPTIONS.map((q) => (
                              <option key={q.value} value={q.value}>
                                {uiFr ? q.fr : q.ar}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)", gridColumn: "1 / -1" }}>
                          {uiFr ? "Domicile / siège du client" : "موطن / مقر الموكل"}
                          <input
                            value={legalDraft.client_domicile}
                            onChange={(e) => setLegalDraft((prev) => ({ ...prev, client_domicile: e.target.value }))}
                            placeholder={uiFr ? "Adresse (art. 32 CPC)" : "العنوان"}
                            style={{ display: "block", width: "100%", marginTop: 4, border: "1px solid var(--line)", borderRadius: 10, padding: "9px 10px", background: "#fff" }}
                          />
                        </label>
                        <label style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>
                          {uiFr ? "Partie adverse (nom)" : "الطرف المقابل"}
                          <input
                            value={legalDraft.opposing_name}
                            onChange={(e) => setLegalDraft((prev) => ({ ...prev, opposing_name: e.target.value }))}
                            style={{ display: "block", width: "100%", marginTop: 4, border: "1px solid var(--line)", borderRadius: 10, padding: "9px 10px", background: "#fff" }}
                          />
                        </label>
                        <label style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>
                          {uiFr ? "Nature adverse" : "طبيعة المقابل"}
                          <select
                            value={legalDraft.opposing_quality}
                            onChange={(e) => setLegalDraft((prev) => ({ ...prev, opposing_quality: e.target.value }))}
                            style={{ display: "block", width: "100%", marginTop: 4, border: "1px solid var(--line)", borderRadius: 10, padding: "9px 10px", background: "#fff" }}
                          >
                            {QUALITY_OPTIONS.map((q) => (
                              <option key={q.value} value={q.value}>
                                {uiFr ? q.fr : q.ar}
                              </option>
                            ))}
                          </select>
                        </label>
                      </div>
                      <p style={{ margin: "10px 0 0", fontSize: 11, color: "var(--ink-soft)", lineHeight: 1.45 }}>
                        {indicativeDeadlineHint(legalDraft.jurisdiction_degree, uiFr)}
                      </p>
                      <button
                        type="button"
                        className="chip-btn primary"
                        style={{ marginTop: 12 }}
                        disabled={legalSaving}
                        onClick={() => void saveLegalInline()}
                      >
                        {legalSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                        {uiFr ? "Enregistrer l’identité sur le dossier" : "حفظ الهوية على الملف"}
                      </button>

                      <div style={{ marginTop: 16, paddingTop: 14, borderTop: "1px solid var(--line)" }}>
                        <label style={{ display: "block", fontSize: 12, fontWeight: 700, color: "var(--ink-soft)", marginBottom: 6 }}>
                          {uiFr ? "Type d’acte (cette génération)" : "نوع الوثيقة لهذه المرة"}
                        </label>
                        <select
                          value={actType}
                          onChange={(e) => setActType(e.target.value)}
                          style={{
                            width: "100%",
                            border: "1px solid var(--line)",
                            borderRadius: 12,
                            padding: "11px 12px",
                            background: "var(--parchment)",
                            marginBottom: 12,
                          }}
                        >
                          {ACT_TYPES.map((a) => (
                            <option key={a.value} value={a.value}>
                              {uiFr ? a.fr : a.ar}
                            </option>
                          ))}
                        </select>
                        <label style={{ display: "block", fontSize: 12, fontWeight: 700, color: "var(--ink-soft)", marginBottom: 6 }}>
                          {uiFr ? "Modèle de marafua (par domaine)" : "نموذج المرافعة (حسب المجال)"}
                        </label>
                        <select
                          value={pleaType}
                          onChange={(e) => setPleaType(e.target.value)}
                          style={{
                            width: "100%",
                            border: "1px solid var(--line)",
                            borderRadius: 12,
                            padding: "11px 12px",
                            background: "var(--parchment)",
                          }}
                        >
                          {PLAIDOIRIE_DOMAIN_GROUPS.map((g) => (
                            <optgroup key={g.key} label={uiFr ? g.labelFr : g.labelAr}>
                              {g.ids.map((id) => {
                                const tpl = getPlaidoirieTemplate(id);
                                if (!tpl) return null;
                                return (
                                  <option key={id} value={id}>
                                    {uiFr ? tpl.labelFr : tpl.labelAr}
                                  </option>
                                );
                              })}
                            </optgroup>
                          ))}
                        </select>
                        <p style={{ margin: "8px 0 0", fontSize: 11, color: "var(--ink-soft)", lineHeight: 1.45 }}>
                          {uiFr
                            ? "Le domaine adapte la structure ChatGPT (ملتمسات, posture). Le type d’acte précise la forme (requête, réplique…)."
                            : "المجال يكيّف هيكل ChatGPT. نوع الوثيقة يحدد الشكل (مقال، جواب…)."}
                        </p>
                      </div>
                    </div>
                  ) : null}
                </div>

                {/* —— Accordion 2 : Pièces —— */}
                <div style={{ border: "1px solid var(--line)", borderRadius: 14, overflow: "hidden", background: "#fff" }}>
                  <button
                    type="button"
                    onClick={() => setStep1Open(step1Open === "pieces" ? "suite" : "pieces")}
                    style={{
                      width: "100%",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: 10,
                      padding: "12px 14px",
                      border: "none",
                      background: step1Open === "pieces" ? "rgba(27,63,156,0.06)" : "transparent",
                      cursor: "pointer",
                      textAlign: "start",
                    }}
                  >
                    <span style={{ fontSize: 13, fontWeight: 700, color: "#1B3F9C" }}>
                      {uiFr
                        ? `2 · Pièces du dossier (${caseDocCount ?? 0})`
                        : `٢ · مرفقات الملف (${caseDocCount ?? 0})`}
                    </span>
                    <ChevronDown
                      size={18}
                      style={{
                        flexShrink: 0,
                        color: "var(--ink-soft)",
                        transform: step1Open === "pieces" ? "rotate(180deg)" : "none",
                        transition: "transform .2s ease",
                      }}
                    />
                  </button>
                  {step1Open === "pieces" ? (
                    <div style={{ padding: "12px 14px 14px", borderTop: "1px solid var(--line)" }}>
                      <p style={{ margin: "0 0 10px", fontSize: 12, color: "var(--ink-soft)", lineHeight: 1.45 }}>
                        {uiFr
                          ? "Vérifiez le contenu OCR avant de dicter. Vous pouvez ajouter d’autres pièces ici."
                          : "تحققوا من نص OCR قبل الإملاء. يمكنكم إضافة مرفقات أخرى هنا."}
                      </p>
                      {caseDocs.length === 0 ? (
                        <p style={{ fontSize: 12, color: "var(--ink-soft)", marginBottom: 10 }}>
                          {uiFr ? "Aucune pièce pour l’instant." : "لا مرفقات بعد."}
                        </p>
                      ) : (
                        <ul style={{ listStyle: "none", margin: "0 0 12px", padding: 0, display: "flex", flexDirection: "column", gap: 8 }}>
                          {caseDocs.map((d) => (
                            <li
                              key={d.id}
                              style={{
                                display: "flex",
                                flexWrap: "wrap",
                                alignItems: "center",
                                justifyContent: "space-between",
                                gap: 8,
                                padding: "10px 12px",
                                borderRadius: 12,
                                border: "1px solid var(--line)",
                                background: "var(--parchment)",
                              }}
                            >
                              <div style={{ minWidth: 0, flex: 1 }}>
                                <p style={{ margin: 0, fontSize: 13, fontWeight: 650, color: "var(--ink)" }}>
                                  {d.original_name}
                                </p>
                                <p
                                  style={{
                                    margin: "2px 0 0",
                                    fontSize: 11,
                                    color:
                                      d.status === "failed"
                                        ? "#b91c1c"
                                        : d.status === "indexed"
                                          ? "#15803d"
                                          : "var(--ink-soft)",
                                  }}
                                >
                                  {d.status === "indexed"
                                    ? uiFr
                                      ? "Indexé — texte prêt"
                                      : "مفهرس — النص جاهز"
                                    : d.status === "failed"
                                      ? uiFr
                                        ? `Échec — ${d.error_message || "texte non extractible"}`
                                        : `فشل — ${d.error_message || "تعذر استخراج النص"}`
                                      : d.status === "processing" || d.status === "pending"
                                        ? uiFr
                                          ? "Traitement…"
                                          : "جارٍ المعالجة…"
                                        : d.status}
                                  {d.ocr_score != null ? ` · OCR ${Math.round(d.ocr_score)}%` : ""}
                                  {d.ocr_alert ? (uiFr ? " · à vérifier" : " · للتحقق") : ""}
                                </p>
                              </div>
                              <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
                                {d.status === "failed" ? (
                                  <button
                                    type="button"
                                    className="chip-btn"
                                    style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 12 }}
                                    onClick={() => {
                                      void (async () => {
                                        try {
                                          await api.reextractDocument(d.id);
                                          setMessage(
                                            uiFr
                                              ? "Réextraction lancée…"
                                              : "أُعيد الاستخراج…",
                                          );
                                          window.setTimeout(() => refreshCaseDocs(), 2500);
                                        } catch (e) {
                                          setError(
                                            e instanceof ApiError
                                              ? e.message
                                              : uiFr
                                                ? "Réextraction impossible."
                                                : "تعذر إعادة الاستخراج.",
                                          );
                                        }
                                      })();
                                    }}
                                  >
                                    <RefreshCw size={14} />
                                    {uiFr ? "Réextraire" : "إعادة"}
                                  </button>
                                ) : null}
                                <button
                                  type="button"
                                  className="chip-btn"
                                  style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 12 }}
                                  onClick={() =>
                                    setPreviewDoc({
                                      id: d.id,
                                      name: d.original_name,
                                      mimeType: d.mime_type,
                                    })
                                  }
                                >
                                  <Eye size={14} />
                                  {uiFr ? "Aperçu" : "معاينة"}
                                </button>
                                <button
                                  type="button"
                                  className="chip-btn"
                                  style={{
                                    display: "inline-flex",
                                    alignItems: "center",
                                    gap: 6,
                                    fontSize: 12,
                                    color: "#b91c1c",
                                  }}
                                  title={uiFr ? "Supprimer cette pièce" : "حذف هذه القطعة"}
                                  onClick={() => {
                                    void (async () => {
                                      const ok = await confirm({
                                        title: uiFr ? "Supprimer cette pièce ?" : "حذف هذه القطعة؟",
                                        description: d.original_name,
                                        confirmLabel: uiFr ? "Supprimer" : "حذف",
                                        tone: "danger",
                                        deleteVisual: "document",
                                      });
                                      if (!ok) return;
                                      try {
                                        await api.deleteDocument(d.id);
                                        setCaseDocs((prev) => prev.filter((x) => x.id !== d.id));
                                        setMessage(
                                          uiFr ? "Pièce supprimée." : "تم حذف القطعة.",
                                        );
                                        pushToast(
                                          uiFr ? "Pièce supprimée" : "تم حذف القطعة",
                                          "success",
                                        );
                                      } catch (e) {
                                        setError(
                                          e instanceof ApiError
                                            ? e.message
                                            : uiFr
                                              ? "Suppression impossible."
                                              : "تعذر الحذف.",
                                        );
                                      }
                                    })();
                                  }}
                                >
                                  <Trash2 size={14} />
                                  {uiFr ? "Suppr." : "حذف"}
                                </button>
                              </div>
                            </li>
                          ))}
                        </ul>
                      )}
                      <p style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)", marginBottom: 8 }}>
                        {uiFr ? "Ajouter des pièces" : "إضافة مرفقات"}
                      </p>
                      <DocumentUpload
                        caseId={caseId}
                        onUploaded={() => refreshCaseDocs()}
                        onUpload={(cid, file) => api.uploadDocument(cid, file)}
                      />
                      <a
                        href={`/cases/${caseId}`}
                        style={{ display: "inline-block", marginTop: 10, fontSize: 12, color: "#1B3F9C", fontWeight: 600 }}
                      >
                        {uiFr ? "Ouvrir la fiche dossier →" : "فتح بطاقة الملف ←"}
                      </a>
                    </div>
                  ) : null}
                </div>

                {/* —— Accordion 3 : Suite —— */}
                <div style={{ border: "1px solid var(--line)", borderRadius: 14, overflow: "hidden", background: "#fff" }}>
                  <button
                    type="button"
                    onClick={() => setStep1Open(step1Open === "suite" ? "identite" : "suite")}
                    style={{
                      width: "100%",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: 10,
                      padding: "12px 14px",
                      border: "none",
                      background: step1Open === "suite" ? "rgba(27,63,156,0.06)" : "transparent",
                      cursor: "pointer",
                      textAlign: "start",
                    }}
                  >
                    <span style={{ fontSize: 13, fontWeight: 700, color: "#1B3F9C" }}>
                      {uiFr ? "3 · Prêt pour la dictée" : "٣ · جاهز للإملاء"}
                    </span>
                    <ChevronDown
                      size={18}
                      style={{
                        flexShrink: 0,
                        color: "var(--ink-soft)",
                        transform: step1Open === "suite" ? "rotate(180deg)" : "none",
                        transition: "transform .2s ease",
                      }}
                    />
                  </button>
                  {step1Open === "suite" ? (
                    <div style={{ padding: "12px 14px 14px", borderTop: "1px solid var(--line)" }}>
                      <p style={{ margin: 0, fontSize: 13, color: "var(--ink-soft)", lineHeight: 1.5 }}>
                        {uiFr
                          ? "Vérifiez identité + pièces, puis passez à la dictée. L’IA (ChatGPT) rédigera en arabe fusḥā selon le modèle choisi."
                          : "تحققوا من الهوية والمرفقات ثم انتقلوا للإملاء. يصوغ ChatGPT بالعربية الفصحى حسب النموذج."}
                      </p>
                      {!cabinetLogoUrl ? (
                        <p style={{ margin: "10px 0 0", fontSize: 12, color: "var(--ink-soft)" }}>
                          {uiFr
                            ? "Astuce : logo cabinet dans Paramètres → Cabinet pour l’en-tête Word."
                            : "نصيحة: شعار المكتب من الإعدادات ← المكتب لترويسة Word."}
                        </p>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              </div>
            ) : null}

            {draftsHint && <p style={{ fontSize: 12, color: "var(--emerald)", marginBottom: 10 }}>{draftsHint}</p>}
          </div>
          <div className="plea-step-actions">
            <span />
            <button
              type="button"
              className="chip-btn primary"
              disabled={!caseId || !actType || legalSaving}
              onClick={() => {
                void (async () => {
                  if (selectedCase && missingLegalFields(selectedCase).length) {
                    const ok = await saveLegalInline();
                    if (!ok) return;
                  }
                  goStep(1);
                })();
              }}
            >
              {uiFr ? "Dictée →" : "الإملاء ←"}
            </button>
          </div>
        </div>

        {/* 1 — Dictée : reste monté (display) pour ne pas couper le micro */}
        <div
          className="plea-step-panel card"
          style={{ padding: 22, display: step === 1 ? "block" : "none" }}
        >
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 10,
              marginBottom: 8,
            }}
          >
            <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>
              {uiFr ? "Dictée" : "الإملاء"}
            </h3>
            <span className="type-pill sel" aria-label={uiFr ? "Langue de la dictée : arabe" : "لغة الإملاء: العربية"}>
              العربية
            </span>
          </div>
          <p style={{ margin: "0 0 14px", fontSize: 13, color: "var(--ink-soft)", fontWeight: 500, lineHeight: 1.55 }}>
            {uiFr
              ? "Dictez au micro, ou importez un enregistrement (wav, mp3, ogg, m4a, webm). Le même moteur vocal cloud transcrit le fichier."
              : "أملوا في الميكروفون، أو ارفعوا تسجيلاً صوتياً (wav, mp3, ogg, m4a, webm). نفس محرك التفريغ السحابي يعالج الملف."}
          </p>
          <div className="voice-orb-wrap" style={{ padding: "18px 8px 10px" }}>
            <VoiceOrb listening={isLive} />
            {!isLive ? (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 10, justifyContent: "center" }}>
                <button
                  type="button"
                  className="dict-btn dict-btn--start"
                  onClick={() => void startDictation()}
                  disabled={busy !== null || (!livePreviewOk && !recorderOk)}
                >
                  <Mic className="h-4 w-4" />
                  {uiFr ? "Commencer" : "ابدأ"}
                </button>
                <button
                  type="button"
                  className="dict-btn dict-btn--ignore"
                  onClick={() => audioFileInputRef.current?.click()}
                  disabled={busy !== null || transcribing}
                  title={uiFr ? "Importer un fichier audio" : "رفع ملف صوتي"}
                >
                  {busy === "audioFile" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                  {uiFr ? "Fichier audio" : "ملف صوتي"}
                </button>
                <input
                  ref={audioFileInputRef}
                  type="file"
                  accept="audio/*,.webm,.wav,.mp3,.ogg,.m4a,.mp4"
                  hidden
                  onChange={(e) => void handleAudioFile(e.target.files?.[0])}
                />
              </div>
            ) : (
              <div className="dict-ctrls" role="group">
                {dictationPaused ? (
                  <button type="button" className="dict-btn dict-btn--start" onClick={resumeDictation} disabled={transcribing}>
                    <Play className="h-4 w-4" />
                    {uiFr ? "Reprendre" : "استئناف"}
                  </button>
                ) : (
                  <button type="button" className="dict-btn dict-btn--ignore" onClick={pauseDictation} disabled={transcribing}>
                    <Pause className="h-4 w-4" />
                    {uiFr ? "Pause" : "إيقاف مؤقت"}
                  </button>
                )}
                <button type="button" className="dict-btn dict-btn--ignore" onClick={ignoreDictation} disabled={transcribing}>
                  <X className="h-4 w-4" />
                  {uiFr ? "Annuler" : "إلغاء"}
                </button>
                <button
                  type="button"
                  className="dict-btn dict-btn--ok"
                  onClick={() => void validateDictation()}
                  disabled={transcribing || (busy !== null && busy !== "polish")}
                  title={uiFr ? "Extraire le texte dicté" : "استخراج النص المُملى"}
                >
                  {busy === "polish" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                  تم
                </button>
              </div>
            )}
            <VoiceWave active={isLive} />
          </div>

          <VoiceMeter analyser={analyser} active={recording} />

          {(recording || transcribing || dictationActive) && (
            <div
              className={`live-caption ${arabicField.className}`}
              dir={textDir}
              lang={arabicField.lang}
              style={{
                marginTop: 10,
                minHeight: 52,
                borderRadius: 16,
                border: "1px solid rgba(255,106,0,0.35)",
                background: "rgba(255,252,246,0.95)",
                padding: "12px 14px",
                fontSize: 15,
                lineHeight: 1.55,
                fontWeight: 600,
                color: "var(--ink)",
                textAlign: dictFr ? "left" : "right",
              }}
            >
              {transcribing ? (
                <span style={{ color: "var(--ink-soft)", fontWeight: 500 }}>
                  {uiFr
                    ? "⏳ Finalisation…"
                    : "⏳ جاري الإنهاء…"}
                </span>
              ) : liveCaption ? (
                <span>{liveCaption}</span>
              ) : (
                <span style={{ color: "var(--ink-soft)", fontWeight: 500 }}>
                  {uiFr
                    ? `🎙️ ${Math.floor(recElapsedSec / 60)}:${String(recElapsedSec % 60).padStart(2, "0")} — parlez, le texte doit apparaître ici…`
                    : `🎙️ ${Math.floor(recElapsedSec / 60)}:${String(recElapsedSec % 60).padStart(2, "0")} — تكلّموا، يجب أن يظهر النص هنا…`}
                </span>
              )}
            </div>
          )}

          {(whisperError || (livePreviewError && /محظور|bloqué|not-allowed|غير مدعوم|non support/i.test(livePreviewError))) && (
            <p style={{ background: "rgba(255,106,0,0.12)", color: "#E85A00", borderRadius: 12, padding: "8px 12px", fontSize: 12, marginTop: 10 }}>
              {whisperError || livePreviewError}
            </p>
          )}

          <div className="plea-step-actions">
            <span />
            <button type="button" className="chip-btn primary" onClick={() => goStep(2)}>
              {uiFr ? "Transcription →" : "التفريغ ←"}
            </button>
          </div>
        </div>

        {/* 2 — Transcription */}
        <div className="plea-step-panel card" style={{ padding: 22, display: step === 2 ? "block" : "none" }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 10 }}>
            {uiFr ? "Transcription" : "التفريغ"}
          </h3>
          <div className="form-field full">
            <label style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>
              {uiFr ? "Texte brut (après arrêt — éditable)" : "النص الخام (بعد الإيقاف — قابل للتعديل)"}
            </label>
            <textarea
              dir={textDir}
              lang={arabicField.lang}
              className={arabicField.className}
              value={raw}
              onChange={(e) => {
                setRaw(e.target.value);
                setSenseAlert("");
                if (recording || dictationActive) setLiveCaption(e.target.value);
              }}
              placeholder={uiFr ? "Le texte apparaît ici après إيقاف. Vous pouvez le corriger à la main." : "يظهر النص هنا بعد الإيقاف. يمكنكم تصحيحه يدوياً."}
              style={{
                minHeight: 220,
                width: "100%",
                textAlign: dictFr ? "left" : "right",
                resize: "vertical",
                border: "1px solid var(--line)",
                background: "#fff",
                borderRadius: 12,
                padding: "12px 14px",
                fontSize: 15,
                lineHeight: 1.6,
                color: "var(--ink)",
                outline: "none",
              }}
            />
          </div>
          <div className="doc-actions">
            <button
              type="button"
              className="chip-btn"
              disabled={!raw.trim() || (busy !== null && busy !== "polish") || recording || transcribing || dictationActive}
              onClick={() => {
                if (busy === "polish") {
                  cancelPolish();
                  return;
                }
                void handlePolish();
              }}
            >
              {busy === "polish" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 width={14} height={14} />}
              {busy === "polish" ? (uiFr ? "Annuler" : "إلغاء") : uiFr ? "Corriger" : "تصحيح"}
            </button>
            <button
              type="button"
              className="chip-btn"
              onClick={() => {
                void (async () => {
                  if (raw.trim().length > 40) {
                    const ok = await confirm({
                      title: uiFr ? "Effacer toute la dictée ?" : "مسح الإملاء بالكامل؟",
                      description: uiFr ? "Cette action est définitive." : "لا يمكن التراجع عن ذلك.",
                      tone: "danger",
                      requireDeletePhrase: true,
                      confirmLabel: uiFr ? "Effacer" : "مسح",
                    });
                    if (!ok) return;
                  }
                  setRaw("");
                  setPolished("");
                  setMessage("");
                  setContradictions([]);
                  setContradictionCheck("idle");
                  setEditingPolished(false);
                  setComposeChecks([]);
                })();
              }}
            >
              {uiFr ? "Effacer" : "مسح"}
            </button>
          </div>
          {message && (
            <p
              style={{
                fontSize: 13,
                color: contradictionCheck === "unchecked" ? "#991b1b" : "var(--emerald)",
                marginTop: 8,
                fontWeight: contradictionCheck === "unchecked" ? 600 : 500,
              }}
            >
              {message}
            </p>
          )}
          <AnimatePresence initial={false}>
            {contradictions.length > 0 && (
              <motion.div
                key="contradiction-alerts"
                className="contradiction-alerts"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8, height: 0, marginTop: 0 }}
                transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
                style={{ marginTop: 14, display: "grid", gap: 10, overflow: "hidden" }}
                dir={uiFr ? "ltr" : "rtl"}
                role="region"
                aria-label={uiFr ? "Contradictions détectées" : "تناقضات مرصودة"}
              >
                <p style={{ margin: 0, fontSize: 12, fontWeight: 700, color: "#9a3412" }}>
                  {uiFr
                    ? `${contradictions.length} alerte(s) — tranchez avant de continuer`
                    : `${contradictions.length} تنبيه(ات) — احسموا قبل المتابعة`}
                </p>
                <AnimatePresence initial={false}>
                  {contradictions.map((c) => (
                    <motion.div
                      key={`${c.kind}-${c.values.join("|")}`}
                      layout
                      initial={{ opacity: 0, y: -8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -6, scale: 0.98 }}
                      transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
                      style={{
                        borderRadius: 14,
                        border: "2px solid rgba(194, 65, 12, 0.45)",
                        background: "rgba(255, 237, 213, 0.98)",
                        padding: "12px 14px",
                        boxShadow: "0 8px 24px rgba(154, 52, 18, 0.12)",
                        transformOrigin: "top center",
                      }}
                    >
                      <p
                        className={uiFr ? undefined : "arabic-text"}
                        dir={uiFr ? "ltr" : "rtl"}
                        style={{ margin: "0 0 10px", fontSize: 13.5, fontWeight: 700, color: "#9a3412", lineHeight: 1.5 }}
                      >
                        ⚠️ {uiFr ? c.message_fr : fixArabicBidiDisplay(c.message_ar)}
                      </p>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                        {c.values.map((v) => (
                          <motion.button
                            key={v}
                            type="button"
                            className="chip-btn primary polish-chip-btn"
                            whileHover={{ scale: 1.03 }}
                            whileTap={{ scale: 0.97 }}
                            transition={{ duration: 0.15, ease: "easeOut" }}
                            onClick={() => applyContradictionChoice(c.kind, v)}
                          >
                            {v}
                          </motion.button>
                        ))}
                        <motion.button
                          type="button"
                          className="chip-btn polish-chip-btn"
                          whileHover={{ scale: 1.03 }}
                          whileTap={{ scale: 0.97 }}
                          transition={{ duration: 0.15, ease: "easeOut" }}
                          onClick={() => applyContradictionChoice(c.kind, null)}
                        >
                          {uiFr ? "Garder les deux" : "ترك الاثنين"}
                        </motion.button>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </motion.div>
            )}
          </AnimatePresence>
          {contradictionCheck === "unchecked" && polished && (
            <motion.div
              role="alert"
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
              style={{
                marginTop: 12,
                borderRadius: 14,
                border: "2px solid rgba(185, 28, 28, 0.4)",
                background: "rgba(254, 226, 226, 0.95)",
                padding: "12px 14px",
                fontSize: 13,
                fontWeight: 600,
                color: "#991b1b",
                lineHeight: 1.55,
              }}
            >
              {uiFr
                ? "⚠️ Service de vérification indisponible. Les contradictions (numéros, dates, noms, montants) n’ont PAS été vérifiées dans ce texte. Relisez attentivement avant de valider, ou réessayez une fois le service rétabli."
                : "⚠️ خدمة التحقق غير متاحة. لم يتم فحص التناقضات (أرقام الملفات، التواريخ، الأسماء، المبالغ) في هذا النص. راجعوا بعناية قبل الاعتماد، أو أعيدوا المحاولة عند عودة الخدمة."}
            </motion.div>
          )}
          {contradictionCheck === "verified" && polished && contradictions.length === 0 && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              style={{ fontSize: 12, color: "var(--emerald)", marginTop: 8, fontWeight: 600 }}
            >
              {uiFr
                ? "✅ Vérifié : aucune contradiction détectée (n°, dates, montants, noms)."
                : "✅ تم التحقق: لم يُرصد تناقض (أرقام، تواريخ، مبالغ، أسماء)."}
            </motion.p>
          )}
          {contradictionCheck === "idle" && polished && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              style={{ fontSize: 12, color: "#92400e", marginTop: 8, fontWeight: 600 }}
            >
              {uiFr
                ? "Contrôle des contradictions non exécuté sur ce texte."
                : "لم يُنفَّذ فحص التناقضات على هذا النص."}
            </motion.p>
          )}
          {polished && (
            <PleaAssistPanel
              uiFr={uiFr}
              edits={formEdits}
              variables={pleaVariables}
              polished={polished}
              onPolishedChange={setPolished}
            />
          )}
          <AnimatePresence initial={false}>
            {polished && (
              <motion.div
                key="polished-block"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 6 }}
                transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
                style={{ marginTop: 18 }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, marginBottom: 8 }}>
                  <p style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 700, fontSize: 14, margin: 0 }}>
                    <Sparkles width={16} height={16} style={{ color: "var(--gold)" }} />
                    {uiFr ? "Texte corrigé" : "النص المصحح"}
                  </p>
                  <motion.button
                    type="button"
                    className="chip-btn polish-chip-btn"
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => setEditingPolished((v) => !v)}
                  >
                    {editingPolished
                      ? uiFr
                        ? "Aperçu"
                        : "معاينة"
                      : uiFr
                        ? "Modifier"
                        : "تعديل"}
                  </motion.button>
                </div>
                <p style={{ fontSize: 11, color: "var(--ink-soft)", margin: "0 0 8px", lineHeight: 1.4 }}>
                  {uiFr
                    ? "Seul le surlignage orange marque une substitution STT à vérifier — pas les corrections mineures."
                    : "التظليل البرتقالي فقط للكلمات المستبدلة من التفريغ والتي تستحق المراجعة — وليس للتصحيحات البسيطة."}
                </p>
                {editingPolished ? (
                  <textarea
                    dir={textDir}
                    lang={arabicField.lang}
                    className={`polish-editor ${arabicField.className}`}
                    value={polished}
                    onChange={(e) => setPolished(e.target.value)}
                    style={{
                      minHeight: 160,
                      width: "100%",
                      textAlign: dictFr ? "left" : "right",
                      resize: "vertical",
                      border: "1px solid rgba(197, 160, 40, 0.35)",
                      borderRadius: 12,
                      padding: 12,
                      background: "rgba(255, 252, 246, 0.95)",
                      fontSize: 15,
                      lineHeight: 1.75,
                    }}
                  />
                ) : (
                  <div
                    dir={textDir}
                    lang={arabicField.lang}
                    className={`polish-preview ${arabicField.className}`}
                    style={{
                      minHeight: 100,
                      width: "100%",
                      border: "1px solid rgba(197, 160, 40, 0.35)",
                      borderRadius: 12,
                      padding: 12,
                      background: "rgba(255, 252, 246, 0.95)",
                      fontSize: 15,
                      lineHeight: 1.75,
                      whiteSpace: "pre-wrap",
                    }}
                    dangerouslySetInnerHTML={{
                      __html: renderArabicPreviewHtml(polished),
                    }}
                  />
                )}
              </motion.div>
            )}
          </AnimatePresence>
          <div
            style={{
              marginTop: 18,
              padding: "14px 14px 8px",
              borderRadius: 14,
              border: "1px solid rgba(27,63,156,0.18)",
              background: "rgba(27,63,156,0.04)",
            }}
          >
            <p style={{ margin: "0 0 10px", fontSize: 13, fontWeight: 700, color: "#1B3F9C" }}>
              {uiFr ? "Contexte issu du dossier + type d’acte" : "سياق الملف + نوع الوثيقة"}
            </p>
            <p style={{ margin: "0 0 10px", fontSize: 12, color: "var(--ink-soft)", lineHeight: 1.5 }}>
              {uiFr
                ? "Avant l’envoi à l’IA : noms du client et de l’adverse → PARTIE_A / PARTIE_B. Après rédaction : les vrais noms reviennent dans le document Word. L’IA croise fiche dossier + pièces + dictée."
                : "قبل الإرسال: الأسماء → PARTIE_A/B. بعد الصياغة تُعاد الأسماء في ملف Word. يدمج الذكاء بطاقة الملف والمرفقات والإملاء."}
            </p>
            <label style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)", display: "block" }}>
              {uiFr ? "Type d’acte" : "نوع الوثيقة"}
              <select
                value={actType}
                onChange={(e) => setActType(e.target.value)}
                style={{
                  display: "block",
                  width: "100%",
                  marginTop: 4,
                  border: "1px solid var(--line)",
                  borderRadius: 10,
                  padding: "9px 10px",
                  background: "#fff",
                }}
              >
                {ACT_TYPES.map((a) => (
                  <option key={a.value} value={a.value}>
                    {uiFr ? a.fr : a.ar}
                  </option>
                ))}
              </select>
            </label>
            {selectedCase?.jurisdiction_degree ? (
              <p style={{ margin: "10px 0 0", fontSize: 11, color: "var(--ink-soft)", lineHeight: 1.45 }}>
                {indicativeDeadlineHint(selectedCase.jurisdiction_degree, uiFr)}
              </p>
            ) : null}
          </div>
          <div className="plea-step-actions">
            <button type="button" className="chip-btn" onClick={() => goStep(1)}>
              {uiFr ? "← Dictée" : "→ الإملاء"}
            </button>
            <button
              type="button"
              className="chip-btn primary"
              disabled={!(polished || raw).trim() || busy !== null || clarifyLoading || clarifyOpen}
              onClick={() => {
                void startClarifyFlow();
              }}
            >
              {busy === "compose" || clarifyLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles width={14} height={14} />}
              {busy === "compose"
                ? uiFr
                  ? "Rédaction…"
                  : "جاري الصياغة…"
                : clarifyLoading
                  ? uiFr
                    ? "Analyse…"
                    : "تحليل…"
                  : uiFr
                    ? "Rédaction IA →"
                    : "الصياغة بالذكاء ←"}
            </button>
          </div>
        </div>

        {/* 3 — Document éditable */}
        <div className="plea-step-panel" style={{ display: step === 3 ? "block" : "none" }}>
          {docBody ? (
            <>
            <div ref={docEditorRef}>
            <DocumentWorkspace
              key={`edit-${docEditorKey}`}
              title={docTitle}
              body={docBody}
              onTitleChange={setDocTitle}
              onBodyChange={setDocBody}
              cases={cases}
              caseId={caseId}
              onCaseIdChange={setCaseId}
              onExportWord={async () => {
                const ok = await handleExportWord();
                if (ok) setExportedDone(true);
              }}
              onPreviewWord={handlePreviewWord}
              onSaveToCase={handleSaveToCase}
              savingCase={busy === "save"}
              exportingWord={busy === "word"}
              previewingWord={wordPreviewOpen}
              hideClassify
              docLang={dictationLang}
              mode="edit"
            />
            </div>
            <div className="card" style={{ marginTop: 14, padding: 16 }}>
              <p style={{ margin: "0 0 6px", fontWeight: 650, color: "var(--ink)", fontSize: 14 }}>
                {uiFr ? "Assistant IA — modifications" : "مساعد الذكاء — تعديلات"}
              </p>
              <p style={{ margin: "0 0 10px", fontSize: 12, color: "var(--ink-soft)", lineHeight: 1.45 }}>
                {uiFr
                  ? "Décrivez le changement voulu. L’IA met à jour le document ci-dessus ; l’historique reste ici comme un chat."
                  : "صفوا التعديل المطلوب. يحدّث الذكاء الوثيقة أعلاه؛ ويبقى السجل هنا كمحادثة."}
              </p>
              {reviseChat.length > 0 ? (
                <div
                  style={{
                    maxHeight: 220,
                    overflowY: "auto",
                    marginBottom: 12,
                    display: "flex",
                    flexDirection: "column",
                    gap: 8,
                    padding: 10,
                    borderRadius: 12,
                    border: "1px solid var(--line)",
                    background: "rgba(27,63,156,0.04)",
                  }}
                >
                  {reviseChat.map((m) => (
                    <div
                      key={m.id}
                      style={{
                        alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                        maxWidth: "92%",
                        padding: "8px 11px",
                        borderRadius: 12,
                        background: m.role === "user" ? "#1B3F9C" : "#fff",
                        color: m.role === "user" ? "#fff" : "var(--ink)",
                        border: m.role === "assistant" ? "1px solid var(--line)" : "none",
                        fontSize: 13,
                        lineHeight: 1.45,
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 8, marginBottom: 4 }}>
                        <span style={{ fontSize: 10, opacity: 0.75, fontWeight: 600 }}>
                          {m.role === "user"
                            ? uiFr
                              ? "Vous"
                              : "أنتم"
                            : uiFr
                              ? `IA${m.provider ? ` · ${m.provider}` : ""}`
                              : `الذكاء${m.provider ? ` · ${m.provider}` : ""}`}
                        </span>
                        <button
                          type="button"
                          title={uiFr ? "Copier" : "نسخ"}
                          onClick={() => void navigator.clipboard.writeText(m.content)}
                          style={{
                            border: "none",
                            background: "transparent",
                            cursor: "pointer",
                            color: "inherit",
                            opacity: 0.7,
                            padding: 0,
                            display: "inline-flex",
                          }}
                        >
                          <Copy size={12} />
                        </button>
                      </div>
                      <div style={{ whiteSpace: "pre-wrap" }}>{m.content}</div>
                      {m.role === "user" ? (
                        <button
                          type="button"
                          onClick={() => setReviseInstruction(m.content)}
                          style={{
                            marginTop: 6,
                            border: "none",
                            background: "rgba(255,255,255,0.15)",
                            color: "#fff",
                            fontSize: 11,
                            borderRadius: 8,
                            padding: "2px 8px",
                            cursor: "pointer",
                          }}
                        >
                          {uiFr ? "Réutiliser" : "إعادة استخدام"}
                        </button>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : null}
              <textarea
                value={reviseInstruction}
                onChange={(e) => setReviseInstruction(e.target.value)}
                rows={3}
                placeholder={
                  uiFr
                    ? "Écrivez naturellement (fautes OK) — ex. « rien écrit sous خامساً », « développez ce paragraphe… »"
                    : "اكتبوا بصياغتكم العادية — مثال: « ما كتب والو تحت خامساً »، « طوّروا هذه الفقرة… »"
                }
                style={{
                  width: "100%",
                  border: "1px solid var(--line)",
                  borderRadius: 10,
                  padding: "10px 12px",
                  fontSize: 13,
                  resize: "vertical",
                  background: "#fff",
                }}
              />
              <button
                type="button"
                className="chip-btn primary"
                style={{ marginTop: 10 }}
                disabled={!reviseInstruction.trim() || busy !== null}
                onClick={() => void handleRevise()}
              >
                {busy === "revise" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 width={14} height={14} />}
                {busy === "revise"
                  ? uiFr
                    ? "Modification…"
                    : "جاري التعديل…"
                  : uiFr
                    ? "Appliquer la modification"
                    : "تطبيق التعديل"}
              </button>
            </div>
            </>
          ) : (
            <div className="card" style={{ padding: 22 }}>
              <p className="section-sub" style={{ margin: 0 }}>
                {uiFr
                  ? "Générez d’abord la plaidoirie depuis l’étape Transcription (Rédaction IA)."
                  : "ولّدوا المرافعة أولاً من خطوة التفريغ (الصياغة بالذكاء)."}
              </p>
              <button type="button" className="chip-btn primary" style={{ marginTop: 12 }} onClick={() => goStep(2)}>
                {uiFr ? "Aller à la transcription" : "إلى التفريغ"}
              </button>
            </div>
          )}
          <div className="plea-step-actions">
            <button type="button" className="chip-btn" onClick={() => goStep(2)}>
              {uiFr ? "← Transcription" : "→ التفريغ"}
            </button>
            <button type="button" className="chip-btn primary" disabled={!docBody.trim()} onClick={() => goStep(4)}>
              {uiFr ? "Export →" : "التصدير ←"}
            </button>
          </div>
        </div>

        {/* 4 — Export */}
        <div className="plea-step-panel" style={{ display: step === 4 ? "block" : "none" }}>
          {docBody ? (
            <>
              <DocumentWorkspace
              title={docTitle}
              body={docBody}
              onTitleChange={setDocTitle}
              onBodyChange={setDocBody}
              cases={cases}
              caseId={caseId}
              onCaseIdChange={setCaseId}
              onExportWord={async () => {
                const ok = await handleExportWord();
                if (ok) setExportedDone(true);
              }}
              onPreviewWord={handlePreviewWord}
              onSaveToCase={handleSaveToCase}
              savingCase={busy === "save"}
              exportingWord={busy === "word"}
              previewingWord={wordPreviewOpen}
              savingTemplate={busy === "saveTpl"}
              hideClassify
              docLang={dictationLang}
              mode="export"
            />
            </>
          ) : (
            <div className="card" style={{ padding: 22 }}>
              <p className="section-sub" style={{ margin: 0 }}>
                {uiFr ? "Aucun document à exporter." : "لا وثيقة للتصدير."}
              </p>
            </div>
          )}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 14, justifyContent: "flex-start" }}>
            <a href="/redaction/new" className="chip-btn primary">
              {uiFr ? "Nouvelle plaidoirie" : "مرافعة جديدة"}
            </a>
          </div>
          {exportedDone ? (
            <div className="plea-success" role="status">
              <p className="plea-success__eyebrow">LexHub</p>
              <h3 className="plea-success__title">
                {uiFr ? "Plaidoirie finalisée" : "مرافعة منتهية"}
              </h3>
              <p className="plea-success__sub">
                {uiFr
                  ? "Exportée en format Word (.docx) et classée « Finalisée » (plus un brouillon). Prête à être modifiée, complétée ou jointe au dossier."
                  : "مُصدَّرة بصيغة Word (.docx) ومصنّفة « منتهية » (لم تعد مسودة). جاهزة للتعديل أو الإرفاق بالملف."}
              </p>
              <div className="plea-success__actions">
                <button
                  type="button"
                  className="chip-btn primary"
                  onClick={() => {
                    void handleExportWord();
                  }}
                >
                  <Download className="me-1 inline h-3.5 w-3.5" />
                  {uiFr ? "Télécharger Word (.docx)" : "تحميل Word (.docx)"}
                </button>
                <a href="/redaction/new" className="chip-btn">
                  {uiFr ? "Nouvelle plaidoirie" : "مرافعة جديدة"}
                </a>
              </div>
            </div>
          ) : null}
          <div className="plea-step-actions">
            <button type="button" className="chip-btn" onClick={() => goStep(3)}>
              {uiFr ? "← Document" : "→ الوثيقة"}
            </button>
            <span style={{ fontSize: 12.5, color: exportedDone ? "var(--emerald)" : "var(--ink-soft)", fontWeight: 600 }}>
              {exportedDone
                ? uiFr
                  ? "Export effectué (Word)"
                  : "تم التصدير (Word)"
                : "Word (.docx)"}
            </span>
          </div>
        </div>
      </div>
    </div>

      {wordPreviewOpen ? (
        <div
          role="dialog"
          aria-modal="true"
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 80,
            background: "rgba(7,16,51,0.45)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 16,
          }}
          onClick={() => setWordPreviewOpen(false)}
        >
          <div
            className="card"
            style={{
              width: "min(920px, 96vw)",
              maxHeight: "92vh",
              overflow: "auto",
              padding: 16,
              position: "relative",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <p style={{ margin: 0, fontWeight: 650, color: "var(--ink)" }}>
                {uiFr ? "Aperçu Word (mise en page export)" : "معاينة Word (تنسيق التصدير)"}
              </p>
              <button type="button" className="chip-btn" onClick={() => setWordPreviewOpen(false)}>
                <X width={14} height={14} />
                {uiFr ? "Fermer" : "إغلاق"}
              </button>
            </div>
            <PlaidoirieDocumentPreview
              title={docTitle || "مرافعة"}
              body={structurePlaidoirieBody(docBody)}
              cabinetName={cabinetDisplayName}
              lawyerName={lawyerDisplayName}
              city={user?.cabinet_city || undefined}
            />
          </div>
        </div>
      ) : null}

      <NewCaseModal
        open={showNewCase}
        onClose={() => setShowNewCase(false)}
        existingTypes={cases.map((c) => c.case_type)}
        fromPlea
        onCreated={(_ref, id) => {
          const s = loadPleaSession();
          if (s?.caseId && s.caseId !== id) {
            setRaw("");
            setPolished("");
            setComposeChecks([]);
            setDocBody("");
          }
          setCaseId(id);
          setShowNewCase(false);
          setSettingsVisited(true);
          setStep1Open("pieces");
          savePleaSession({
            v: 1,
            templateId,
            step,
            caseId: id,
            raw: s?.caseId && s.caseId !== id ? "" : raw,
            polished: s?.caseId && s.caseId !== id ? "" : polished,
            docTitle,
            docBody: s?.caseId && s.caseId !== id ? "" : docBody,
            composeChecks: s?.caseId && s.caseId !== id ? [] : composeChecks,
            pleaType,
            actType,
            briefPosture,
            briefJurisdiction,
            settingsVisited: true,
            editingPolished,
            savedAt: Date.now(),
            pendingReturn: true,
          });
          setMessage(
            uiFr
              ? "Dossier créé. Ajoutez des pièces ici, puis « Reprendre la plaidoirie » pour revenir à l’atelier."
              : "تم إنشاء الملف. أضيفوا القطَع هنا ثم « العودة إلى المرافعة » للرجوع إلى الورشة.",
          );
          void api.getCases().then(setCases).catch(() => undefined);
        }}
      />
      <DocumentPreviewModal
        doc={previewDoc}
        open={!!previewDoc}
        onClose={() => setPreviewDoc(null)}
        ar={!uiFr}
      />
    </>
  );
}
