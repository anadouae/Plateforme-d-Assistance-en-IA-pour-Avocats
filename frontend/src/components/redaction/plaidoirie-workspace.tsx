"use client";

import Image from "next/image";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  FileText,
  Loader2,
  Mic,
  MicOff,
  Sparkles,
  Upload,
  Wand2,
} from "lucide-react";
import { VoiceMeter } from "@/components/ai/voice-meter";
import { VoiceOrb, VoiceWave } from "@/components/ai/voice-orb";
import { DocumentWorkspace } from "@/components/redaction/document-workspace";
import {
  api,
  ApiError,
  type CabinetPlaidoirieTemplate,
  type CaseListItem,
} from "@/lib/api";
import {
  downloadOfficialArabicDoc,
  exportOfficialArabicDocument,
  plaidoirieFileFromContent,
} from "@/lib/export-official-doc";
import { getPlaidoirieTemplate } from "@/lib/plaidoirie-templates";
import { useSpeechInput, cleanDictationNoise } from "@/hooks/use-speech-input";
import { useWhisperDictation } from "@/hooks/use-whisper-dictation";
import { useAuthStore } from "@/store/auth";
import { cn } from "@/lib/utils";

function stripStars(text: string): string {
  return text
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*\n]+)\*/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^\s*[-*•]\s+/gm, "— ")
    .replace(/\*{1,3}/g, "")
    .trim();
}

type Props = {
  templateId: string;
};

/**
 * Espace dictée / document — AR + FR (Whisper local + polish/compose).
 */
export function PlaidoirieWorkspace({ templateId }: Props) {
  const user = useAuthStore((s) => s.user);
  const fileRef = useRef<HTMLInputElement>(null);
  const [raw, setRaw] = useState("");
  const [polished, setPolished] = useState("");
  const [docTitle, setDocTitle] = useState("");
  const [docBody, setDocBody] = useState("");
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [caseId, setCaseId] = useState("");
  const [busy, setBusy] = useState<
    "polish" | "compose" | "save" | "saveTpl" | "word" | null
  >(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [provider, setProvider] = useState("");
  const [sttOk, setSttOk] = useState<boolean | null>(null);
  const [dictationLang, setDictationLang] = useState<"ar" | "fr">("ar");
  const [customTemplates, setCustomTemplates] = useState<CabinetPlaidoirieTemplate[]>(
    [],
  );
  const [composeChecks, setComposeChecks] = useState<string[]>([]);
  const [priority, setPriority] = useState<"normal" | "urgent">("normal");
  const [ready, setReady] = useState(false);

  const selectedTemplate = getPlaidoirieTemplate(templateId);
  const selectedCustom = customTemplates.find((t) => t.id === templateId);
  const templateLabel =
    selectedCustom?.name || selectedTemplate?.labelAr || "مرافعة";
  const isFr = dictationLang === "fr";
  const textDir = isFr ? "ltr" : "rtl";

  const {
    recording,
    transcribing,
    error: whisperError,
    startRecording,
    stopRecordingAndTranscribe,
    transcribeFile,
    supported: whisperSupported,
    analyser,
    livePartial,
    setLanguage: setWhisperLanguage,
  } = useWhisperDictation("ar");

  const { listening, supported, error: speechError, startListening, stopListening } =
    useSpeechInput(dictationLang);
  const sessionBaseRef = useRef("");
  const whisperProgressRef = useRef("");
  /** Texte Chrome live (instantané) pendant que Whisper tourne en arrière-plan. */
  const chromeLiveRef = useRef("");
  const [liveCaption, setLiveCaption] = useState("");

  function switchDictationLang(lang: "ar" | "fr") {
    if (lang === dictationLang) return;
    if (recording || transcribing || listening) return;
    setDictationLang(lang);
    setWhisperLanguage(lang);
  }

  useEffect(() => {
    api.getCases().then(setCases).catch(() => setCases([]));
    api
      .getDictationSttStatus()
      .then((s) => setSttOk(!!s.enabled))
      .catch(() => setSttOk(false));
    api
      .listCabinetPlaidoirieTemplates()
      .then((list) => {
        setCustomTemplates(list);
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
        const sys = getPlaidoirieTemplate(templateId) || getPlaidoirieTemplate("libre");
        setDocTitle(sys?.labelAr || "مرافعة");
        setDocBody(sys?.body || "");
        setReady(true);
      });
  }, [templateId]);

  useEffect(() => {
    // Whisper : met à jour si Chrome n’est pas déjà en train d’écrire en live
    if (!recording || !livePartial) return;
    if (chromeLiveRef.current.trim()) return;
    const base = sessionBaseRef.current;
    const next = cleanDictationNoise([base, livePartial].filter(Boolean).join(" "));
    setRaw(next);
    setLiveCaption(livePartial);
  }, [livePartial, recording]);

  const onSpeechResult = useCallback((finals: string, liveInterim: string) => {
    const base = sessionBaseRef.current;
    const parts = [base, finals, liveInterim].filter((p) => p && p.trim());
    const next = cleanDictationNoise(parts.join(" "));
    chromeLiveRef.current = [finals, liveInterim].filter(Boolean).join(" ").trim();
    setRaw(next);
    setLiveCaption(chromeLiveRef.current);
  }, []);

  async function applyTextAndPolish(text: string, fromProvider?: string) {
    const cleaned = cleanDictationNoise(text);
    if (!cleaned) return;
    setRaw(cleaned);
    if (fromProvider) setProvider(fromProvider);
    setMessage("");
    setBusy("polish");
    setError("");
    try {
      const res = await api.polishDictation(cleaned, dictationLang);
      setPolished(stripStars(cleanDictationNoise(res.polished)));
      setProvider(res.provider || fromProvider || "");
    } catch (e) {
      setPolished(cleaned);
      setError(e instanceof ApiError ? e.message : "Correction indisponible.");
    } finally {
      setBusy(null);
    }
  }

  async function toggleWhisperMic() {
    if (recording || transcribing) {
      if (listening) stopListening();
      const chromeSnapshot = chromeLiveRef.current.trim();
      chromeLiveRef.current = "";
      setLiveCaption("");
      const result = await stopRecordingAndTranscribe();
      whisperProgressRef.current = "";
      // Whisper prioritaire ; sinon on garde le texte Chrome déjà affiché
      const finalText = result?.text?.trim() || chromeSnapshot;
      if (finalText) {
        sessionBaseRef.current = "";
        await applyTextAndPolish(finalText, result?.provider || "chrome");
      }
      return;
    }
    if (listening) stopListening();
    sessionBaseRef.current = cleanDictationNoise(raw);
    whisperProgressRef.current = "";
    chromeLiveRef.current = "";
    setLiveCaption("");

    // Live instantané (Chrome) + Whisper en parallèle pour la précision à l’arrêt
    if (supported) {
      startListening(onSpeechResult);
    }

    await startRecording((segmentText) => {
      whisperProgressRef.current = [whisperProgressRef.current, segmentText]
        .filter(Boolean)
        .join(" ");
      // Si Chrome écrit déjà, on ne remplace pas (évite les sauts)
      if (chromeLiveRef.current.trim()) return;
      const next = cleanDictationNoise(
        [sessionBaseRef.current, whisperProgressRef.current]
          .filter(Boolean)
          .join(" "),
      );
      setRaw(next);
      setLiveCaption(segmentText);
    });
  }

  async function openInGoogleDocs() {
    const text = [docTitle.trim(), "", docBody.trim()].filter(Boolean).join("\n\n");
    try {
      await navigator.clipboard.writeText(text);
      setMessage(
        "تم نسخ المرافعة — افتح Google Docs والصق (Ctrl+V / Cmd+V) للتعديل.",
      );
    } catch {
      setMessage(
        "تعذر النسخ التلقائي — انسخ النص يدوياً ثم الصقه في Google Docs.",
      );
    }
    window.open(
      "https://docs.google.com/document/create",
      "_blank",
      "noopener,noreferrer",
    );
  }

  function toggleChromeMic() {
    if (listening) {
      stopListening();
      chromeLiveRef.current = "";
      setLiveCaption("");
      setRaw((prev) => cleanDictationNoise(prev));
      return;
    }
    if (recording || transcribing) return;
    sessionBaseRef.current = cleanDictationNoise(raw);
    chromeLiveRef.current = "";
    setLiveCaption("");
    setRaw(sessionBaseRef.current);
    startListening(onSpeechResult);
  }

  async function onAudioFile(file: File | null) {
    if (!file) return;
    setMessage("");
    const result = await transcribeFile(file);
    if (result?.text) {
      sessionBaseRef.current = "";
      await applyTextAndPolish(result.text, result.provider);
    }
  }

  async function handleSaveAsCabinetTemplate() {
    const body = docBody.trim();
    if (!body) {
      setError("Générez le document avant de le sauver.");
      return;
    }
    const suggested = docTitle.trim() || selectedTemplate?.labelAr || "نموذج المكتب";
    const name = window.prompt("اسم النموذج", suggested);
    if (!name?.trim()) return;
    setBusy("saveTpl");
    setError("");
    try {
      await api.createCabinetPlaidoirieTemplate({
        name: name.trim(),
        body,
        base_type: selectedTemplate?.id || selectedCustom?.base_type || "libre",
      });
      setMessage("Modèle enregistré.");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Impossible d’enregistrer.");
    } finally {
      setBusy(null);
    }
  }

  async function handleExportWord() {
    if (!docBody.trim()) return;
    setBusy("word");
    setError("");
    try {
      const filename = await api.downloadPlaidoirieDocx({
        title: docTitle || "مرافعة",
        body: docBody,
        cabinet_name: user?.cabinet_name,
        lawyer_name: user?.full_name,
      });
      setMessage(filename ? `Word : ${filename}` : "Word téléchargé.");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Export Word échoué.");
    } finally {
      setBusy(null);
    }
  }

  async function handlePolish() {
    const cleaned = cleanDictationNoise(raw);
    if (!cleaned) return;
    setRaw(cleaned);
    setBusy("polish");
    setError("");
    try {
      const res = await api.polishDictation(cleaned, dictationLang);
      setPolished(res.polished);
      setProvider(res.provider);
    } catch (e) {
      setPolished(cleaned);
      setProvider("none");
      setError(e instanceof ApiError ? e.message : "Correction indisponible.");
    } finally {
      setBusy(null);
    }
  }

  async function handleCompose() {
    const source = cleanDictationNoise(polished || raw);
    if (!source) return;
    setBusy("compose");
    setError("");
    try {
      const composeType = selectedCustom
        ? selectedCustom.base_type || "custom"
        : templateId || "civil-general";
      const res = await api.composeDictation({
        text: source,
        doc_type: "plaidoirie",
        polish_first: !polished,
        plaidoirie_type: composeType,
        title: docTitle || selectedCustom?.name || selectedTemplate?.labelAr,
        language: dictationLang,
      });
      if (res.polished) setPolished(res.polished);
      setDocTitle(
        stripStars(
          res.title || selectedCustom?.name || selectedTemplate?.labelAr || "مرافعة",
        ),
      );
      setDocBody(stripStars(res.body));
      setComposeChecks(res.checks || []);
      setProvider(res.provider);
      setMessage("");
    } catch (e) {
      setDocTitle(selectedCustom?.name || selectedTemplate?.labelAr || "مرافعة");
      setDocBody(source);
      setComposeChecks([]);
      setProvider("none");
      setError(e instanceof ApiError ? e.message : "Génération indisponible.");
    } finally {
      setBusy(null);
    }
  }

  const titledDoc =
    priority === "urgent" ? `[عاجل] ${docTitle || "مرافعة"}` : docTitle || "مرافعة";
  const exportOpts = {
    title: titledDoc,
    body: docBody,
    cabinetName: user?.cabinet_name || undefined,
    lawyerName: user?.full_name || undefined,
  };

  async function handleSaveToCase() {
    if (!docBody.trim()) return;
    if (!caseId) {
      setError("Choisissez un dossier.");
      return;
    }
    setBusy("save");
    setError("");
    setMessage("");
    try {
      const file = plaidoirieFileFromContent(exportOpts);
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

  return (
    <div>
      <Link
        href="/redaction"
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 4,
          fontSize: 12.5,
          fontWeight: 600,
          color: "var(--ink-soft)",
          marginBottom: 8,
          textDecoration: "none",
        }}
      >
        <ArrowRight className="h-3.5 w-3.5 rotate-180" />
        {isFr ? "Modèles" : "النماذج"}
      </Link>
      <div className="dossiers-top" style={{ marginBottom: 20 }}>
        <div>
          <div className="section-title" style={{ marginBottom: 4 }} dir="rtl">
            {templateLabel}
          </div>
          <div className="section-sub" style={{ marginBottom: 0 }}>
            {isFr
              ? "Dictée → correction → document officiel"
              : "إملاء → تصحيح → وثيقة رسمية"}
          </div>
        </div>
        {sttOk !== null && (
          <span className={cn("status-pill", sttOk && "status-pill--closed")}>
            Whisper {sttOk ? (isFr ? "prêt" : "جاهز") : isFr ? "indisponible" : "غير متاح"}
          </span>
        )}
      </div>

      {composeChecks.length > 0 && (
        <div
          dir="rtl"
          className="card"
          style={{
            marginBottom: 18,
            background: "rgba(199,151,63,0.1)",
            borderColor: "rgba(199,151,63,0.35)",
          }}
        >
          <p style={{ fontWeight: 700, marginBottom: 8 }}>{isFr ? "À revoir" : "للمراجعة"}</p>
          <ul style={{ paddingInlineStart: 20, margin: 0 }}>
            {composeChecks.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="plaid-grid">
        <div className="card" style={{ padding: 22 }}>
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
              {isFr ? "Dictée · audio" : "الإملاء · الصوت"}
            </h3>
            <div className="type-pick" role="group" aria-label={isFr ? "Langue" : "اللغة"}>
              <button
                type="button"
                className={`type-pill${dictationLang === "ar" ? " sel" : ""}`}
                disabled={recording || transcribing || listening}
                onClick={() => switchDictationLang("ar")}
              >
                ع
              </button>
              <button
                type="button"
                className={`type-pill${dictationLang === "fr" ? " sel" : ""}`}
                disabled={recording || transcribing || listening}
                onClick={() => switchDictationLang("fr")}
              >
                FR
              </button>
            </div>
          </div>

          <div className="voice-orb-wrap" style={{ padding: "18px 8px 10px" }}>
            <VoiceOrb listening={recording || listening} />
            <button
              type="button"
              className="mic-btn"
              aria-pressed={recording || listening}
              onClick={() => void toggleWhisperMic()}
              disabled={
                busy !== null ||
                transcribing ||
                (!whisperSupported && !supported) ||
                (sttOk === false && !supported)
              }
            >
              {transcribing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : recording ? (
                <MicOff className="h-4 w-4" />
              ) : (
                <Mic className="h-4 w-4" />
              )}
              {transcribing
                ? "…"
                : recording
                  ? isFr
                    ? "Arrêter"
                    : "إيقاف"
                  : isFr
                    ? "Commencer à dicter"
                    : "ابدأ الإملاء"}
            </button>
            <VoiceWave active={recording || listening} />
          </div>

          <VoiceMeter analyser={analyser} active={recording} />
          <div aria-live="polite" className="sr-only">
            {recording || listening
              ? isFr
                ? "Écoute active — les mots s’affichent en direct"
                : "جاري الاستماع — الكلمات تظهر فوراً"
              : isFr
                ? "Micro inactif"
                : "الميكروفون متوقف"}
          </div>

          {(recording || listening) && (
            <div
              className="live-caption"
              dir={textDir}
              aria-live="polite"
              style={{
                marginTop: 10,
                minHeight: 52,
                borderRadius: 16,
                border: "1px solid rgba(199,151,63,0.35)",
                background: "rgba(255,252,246,0.95)",
                padding: "12px 14px",
                fontSize: 15,
                lineHeight: 1.55,
                fontWeight: 600,
                color: "var(--ink)",
                textAlign: isFr ? "left" : "right",
              }}
            >
              {liveCaption.trim() || raw.trim() ? (
                liveCaption.trim() || raw
              ) : (
                <span style={{ color: "var(--ink-soft)", fontWeight: 500 }}>
                  {isFr
                    ? "Parlez — les mots apparaissent ici instantanément…"
                    : "تحدث — تظهر الكلمات هنا فوراً…"}
                </span>
              )}
            </div>
          )}

          <div className="doc-actions" style={{ marginTop: 12, marginBottom: 12 }}>
            <button
              type="button"
              className="chip-btn"
              disabled={recording || transcribing || busy !== null}
              onClick={() => fileRef.current?.click()}
            >
              <Upload width={14} height={14} />
              {isFr ? "Fichier audio" : "ملف صوتي"}
            </button>
            <input
              ref={fileRef}
              type="file"
              accept="audio/*,.webm,.wav,.mp3,.m4a,.ogg,.mp4,.aac"
              style={{ display: "none" }}
              onChange={(e) => void onAudioFile(e.target.files?.[0] || null)}
            />
            <button
              type="button"
              className={`chip-btn${listening && !recording ? " primary" : ""}`}
              onClick={toggleChromeMic}
              disabled={!supported || recording || transcribing || busy !== null}
              title="Chrome"
            >
              Chrome
            </button>
          </div>

          {recording && (
            <p style={{ fontSize: 12, fontWeight: 600, color: "#b91c1c" }} dir={textDir}>
              {isFr
                ? supported
                  ? "● Enregistrement — texte en direct"
                  : "● Enregistrement — texte progressif (~3 s)"
                : supported
                  ? "● جارٍ التسجيل — النص يظهر فوراً"
                  : "● جارٍ التسجيل — نص تدريجي (~3 ث)"}
            </p>
          )}
          {listening && !recording && (
            <p style={{ fontSize: 12, fontWeight: 600, color: "var(--emerald)" }} dir={textDir}>
              {isFr ? "● Chrome — transcription instantanée" : "● Chrome — تفريغ فوري"}
            </p>
          )}
          {transcribing && (
            <p
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                fontSize: 12,
                fontWeight: 600,
                color: "var(--ink)",
              }}
              dir={textDir}
            >
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              {isFr ? "Transcription finale…" : "التفريغ النهائي…"}
            </p>
          )}
          {(speechError || whisperError) && (
            <p
              style={{
                background: "rgba(199,151,63,0.12)",
                color: "#8a6321",
                borderRadius: 12,
                padding: "8px 12px",
                fontSize: 12,
              }}
            >
              {whisperError || speechError}
            </p>
          )}

          <div className="form-field full" style={{ marginTop: 10 }}>
            <label style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>
              {isFr ? "Texte dicté (en direct)" : "النص المُملى (مباشر)"}
            </label>
            <textarea
              dir={textDir}
              lang={dictationLang}
              value={raw}
              onChange={(e) => {
                setRaw(e.target.value);
                if (recording || listening) setLiveCaption(e.target.value);
              }}
              placeholder={
                isFr
                  ? "Les mots s’écrivent ici pendant que vous parlez…"
                  : "تُكتب الكلمات هنا أثناء الحديث…"
              }
              style={{
                minHeight: 180,
                width: "100%",
                textAlign: isFr ? "left" : "right",
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
              disabled={!raw.trim() || busy !== null || recording || transcribing}
              onClick={() => void handlePolish()}
            >
              {busy === "polish" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Wand2 width={14} height={14} />
              )}
              {isFr ? "Corriger" : "تصحيح"}
            </button>
            <button
              type="button"
              className="chip-btn"
              onClick={() => {
                setRaw("");
                setPolished("");
                setMessage("");
              }}
            >
              {isFr ? "Effacer" : "مسح"}
            </button>
          </div>
          {message && (
            <p style={{ fontSize: 13, color: "var(--emerald)", marginTop: 8 }}>{message}</p>
          )}

          {polished && (
            <div style={{ marginTop: 18 }}>
              <p
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  fontWeight: 700,
                  fontSize: 14,
                  marginBottom: 8,
                }}
              >
                <Sparkles width={16} height={16} style={{ color: "var(--gold)" }} />
                {isFr ? "Texte corrigé" : "النص المصحح"}
              </p>
              <div className="form-field">
                <textarea
                  dir={textDir}
                  lang={dictationLang}
                  value={polished}
                  onChange={(e) => setPolished(e.target.value)}
                  style={{
                    minHeight: 120,
                    textAlign: isFr ? "left" : "right",
                    resize: "vertical",
                  }}
                />
              </div>
              {provider && (
                <p style={{ fontSize: 10, color: "var(--ink-soft)", marginTop: 6 }}>
                  via {provider}
                </p>
              )}
            </div>
          )}
        </div>

        <div>
          <div className="card doc-preview">
            <span className="badge">{isFr ? "Document officiel" : "الوثيقة الرسمية"}</span>
            <div className="flex items-center gap-3" style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <Image
                src="/armoiries-maroc.png"
                alt=""
                width={48}
                height={60}
                style={{ height: 56, width: "auto", objectFit: "contain" }}
                priority
              />
              <div dir="rtl" style={{ textAlign: "right" }}>
                <p style={{ fontSize: 14, fontWeight: 700, color: "#1a3a2a", margin: 0 }}>
                  المملكة المغربية
                </p>
                <p style={{ fontSize: 12, fontWeight: 600, color: "var(--gold)", margin: 0 }}>
                  مرافعة
                </p>
              </div>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 12,
                border: "1px solid var(--line)",
                borderRadius: 12,
                padding: "10px 12px",
              }}
            >
              <span style={{ fontSize: 13, color: "var(--ink-soft)" }}>
                {isFr ? "Priorité" : "الأولوية"}
              </span>
              <div className="type-pick">
                <button
                  type="button"
                  className={`type-pill${priority === "normal" ? " sel" : ""}`}
                  onClick={() => setPriority("normal")}
                >
                  {isFr ? "Normal" : "عادي"}
                </button>
                <button
                  type="button"
                  className={`type-pill${priority === "urgent" ? " sel" : ""}`}
                  onClick={() => setPriority("urgent")}
                >
                  {isFr ? "Urgent" : "عاجل"}
                </button>
              </div>
            </div>

            <button
              type="button"
              className="mic-btn"
              style={{ width: "100%", justifyContent: "center" }}
              disabled={!(polished || raw || docBody).trim() || busy !== null}
              onClick={() => void handleCompose()}
            >
              {busy === "compose" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <FileText className="h-4 w-4" />
              )}
              {isFr ? "Générer le document" : "توليد الوثيقة"}
            </button>
            {error && <p style={{ fontSize: 13, color: "#b91c1c" }}>{error}</p>}
          </div>

          {docBody && (
            <div style={{ marginTop: 18 }}>
              <DocumentWorkspace
                title={docTitle}
                body={docBody}
                onTitleChange={setDocTitle}
                onBodyChange={setDocBody}
                cases={cases}
                caseId={caseId}
                onCaseIdChange={setCaseId}
                onExportPdf={() => exportOfficialArabicDocument(exportOpts)}
                onExportDocLegacy={() => downloadOfficialArabicDoc(exportOpts)}
                onExportWord={handleExportWord}
                onOpenGoogleDocs={() => void openInGoogleDocs()}
                onSaveTemplate={handleSaveAsCabinetTemplate}
                onSaveToCase={handleSaveToCase}
                savingCase={busy === "save"}
                exportingWord={busy === "word"}
                savingTemplate={busy === "saveTpl"}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
