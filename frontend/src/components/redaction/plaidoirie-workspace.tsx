"use client";

import Image from "next/image";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
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
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { VoiceMeter } from "@/components/ai/voice-meter";
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
import { Magnetic } from "@/components/motion/magnetic";

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
 * Espace dictée / document — arabe uniquement (avocats marocains).
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
  } = useWhisperDictation("ar");

  const { listening, supported, error: speechError, startListening, stopListening } =
    useSpeechInput("ar");
  const sessionBaseRef = useRef("");
  const whisperProgressRef = useRef("");

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
    if (!recording || !livePartial) return;
    const base = sessionBaseRef.current;
    setRaw(cleanDictationNoise([base, livePartial].filter(Boolean).join(" ")));
  }, [livePartial, recording]);

  const onSpeechResult = useCallback((finals: string, liveInterim: string) => {
    const base = sessionBaseRef.current;
    const parts = [base, finals, liveInterim].filter((p) => p && p.trim());
    setRaw(cleanDictationNoise(parts.join(" ")));
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
      const res = await api.polishDictation(cleaned);
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
      const result = await stopRecordingAndTranscribe();
      whisperProgressRef.current = "";
      if (result?.text) {
        sessionBaseRef.current = "";
        await applyTextAndPolish(result.text, result.provider);
      }
      return;
    }
    if (listening) stopListening();
    sessionBaseRef.current = cleanDictationNoise(raw);
    whisperProgressRef.current = "";
    await startRecording((segmentText) => {
      whisperProgressRef.current = [whisperProgressRef.current, segmentText]
        .filter(Boolean)
        .join("\n\n");
      setRaw(
        cleanDictationNoise(
          [sessionBaseRef.current, whisperProgressRef.current]
            .filter(Boolean)
            .join("\n\n"),
        ),
      );
    });
  }

  function toggleChromeMic() {
    if (listening) {
      stopListening();
      setRaw((prev) => cleanDictationNoise(prev));
      return;
    }
    if (recording || transcribing) return;
    sessionBaseRef.current = cleanDictationNoise(raw);
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
      const res = await api.polishDictation(cleaned);
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
      <div className="flex items-center justify-center py-20 text-sm text-slate-500">
        <Loader2 className="me-2 h-4 w-4 animate-spin" />
        …
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-wrap items-end justify-between gap-3"
      >
        <div>
          <Link
            href="/redaction"
            className="mb-2 inline-flex items-center gap-1 text-xs text-sanad-muted hover:text-sanad-navy"
          >
            <ArrowRight className="h-3.5 w-3.5 rotate-180" />
            النماذج
          </Link>
          <h1 className="font-display text-2xl font-semibold text-sanad-navy" dir="rtl">
            {templateLabel}
          </h1>
        </div>
        {sttOk !== null && (
          <span
            className={cn(
              "rounded-full px-3 py-1 text-xs font-medium",
              sttOk ? "bg-green-50 text-green-700" : "bg-amber-50 text-amber-800",
            )}
          >
            Whisper {sttOk ? "prêt" : "indisponible"}
          </span>
        )}
      </motion.div>

      {composeChecks.length > 0 && (
        <div
          dir="rtl"
          className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950"
        >
          <p className="font-semibold">للمراجعة</p>
          <ul className="mt-2 list-disc space-y-1 pe-5">
            {composeChecks.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-4">
          <Card className="overflow-hidden border-sanad-navy/10 shadow-luxe">
            <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 space-y-0">
              <CardTitle className="text-base">الإملاء · الصوت</CardTitle>
              <div className="flex flex-wrap items-center gap-2">
                <Magnetic strength={20}>
                  <Button
                    type="button"
                    size="sm"
                    variant={recording || transcribing ? "default" : "gold"}
                    className={cn((recording || transcribing) && "bg-red-600 hover:bg-red-700")}
                    onClick={() => void toggleWhisperMic()}
                    disabled={!whisperSupported || busy !== null || sttOk === false}
                  >
                    {transcribing ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        …
                      </>
                    ) : recording ? (
                      <>
                        <MicOff className="h-4 w-4" />
                        إيقاف
                      </>
                    ) : (
                      <>
                        <Mic className="h-4 w-4" />
                        ميكروفون
                      </>
                    )}
                  </Button>
                </Magnetic>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  disabled={recording || transcribing || busy !== null}
                  onClick={() => fileRef.current?.click()}
                >
                  <Upload className="h-4 w-4" />
                  ملف صوتي
                </Button>
                <input
                  ref={fileRef}
                  type="file"
                  accept="audio/*,.webm,.wav,.mp3,.m4a,.ogg"
                  className="hidden"
                  onChange={(e) => void onAudioFile(e.target.files?.[0] || null)}
                />
                <Button
                  type="button"
                  size="sm"
                  variant={listening ? "default" : "ghost"}
                  className={cn(listening && "bg-amber-600 hover:bg-amber-700 text-white")}
                  onClick={toggleChromeMic}
                  disabled={!supported || recording || transcribing || busy !== null}
                  title="Chrome"
                >
                  Chrome
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <VoiceMeter analyser={analyser} active={recording} />

              {recording && (
                <p className="animate-pulse text-xs font-medium text-red-600">● تسجيل</p>
              )}
              {transcribing && (
                <p className="flex items-center gap-2 text-xs font-medium text-sanad-navy">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  تفريغ…
                </p>
              )}
              {(speechError || whisperError) && (
                <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
                  {whisperError || speechError}
                </p>
              )}

              <textarea
                dir="rtl"
                lang="ar"
                className="min-h-[200px] w-full rounded-xl border border-sanad-border bg-sanad-cream/40 px-3 py-3 text-right text-base leading-relaxed outline-none focus:ring-2 focus:ring-sanad-gold/40"
                placeholder="النص…"
                value={raw}
                onChange={(e) => setRaw(e.target.value)}
              />
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="outline"
                  disabled={!raw.trim() || busy !== null || recording || transcribing}
                  onClick={() => void handlePolish()}
                >
                  {busy === "polish" ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Wand2 className="h-4 w-4" />
                  )}
                  تصحيح
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setRaw("");
                    setPolished("");
                    setMessage("");
                  }}
                >
                  مسح
                </Button>
              </div>
              {message && <p className="text-sm text-green-700">{message}</p>}
            </CardContent>
          </Card>

          {polished && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Sparkles className="h-4 w-4 text-sanad-gold" />
                  النص المصحح
                </CardTitle>
              </CardHeader>
              <CardContent>
                <textarea
                  dir="rtl"
                  lang="ar"
                  className="min-h-[140px] w-full rounded-xl border border-sanad-border px-3 py-3 text-right text-sm leading-relaxed outline-none focus:ring-2 focus:ring-sanad-gold/40"
                  value={polished}
                  onChange={(e) => setPolished(e.target.value)}
                />
                {provider && (
                  <p className="mt-2 text-[10px] text-slate-400">via {provider}</p>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-4">
          <Card className="border-sanad-gold/30 shadow-luxe">
            <CardHeader>
              <CardTitle className="text-base">الوثيقة الرسمية</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-3 rounded-xl border border-sanad-border/80 bg-sanad-cream/50 px-3 py-2.5">
                <Image
                  src="/armoiries-maroc.png"
                  alt=""
                  width={48}
                  height={60}
                  className="h-14 w-auto object-contain"
                  priority
                />
                <div className="text-right" dir="rtl">
                  <p className="text-sm font-bold text-[#1a3a2a]">المملكة المغربية</p>
                  <p className="text-xs font-semibold text-sanad-gold">مرافعة</p>
                </div>
              </div>
              <div className="flex items-center justify-between gap-3 rounded-xl border border-sanad-border px-3 py-2">
                <span className="text-sm text-sanad-muted">الأولوية</span>
                <div className="flex gap-1 rounded-lg bg-sanad-cream/60 p-0.5">
                  <button
                    type="button"
                    onClick={() => setPriority("normal")}
                    className={cn(
                      "rounded-md px-3 py-1.5 text-xs font-medium transition",
                      priority === "normal"
                        ? "bg-white text-sanad-navy shadow-sm"
                        : "text-sanad-muted hover:text-sanad-navy",
                    )}
                  >
                    عادي
                  </button>
                  <button
                    type="button"
                    onClick={() => setPriority("urgent")}
                    className={cn(
                      "rounded-md px-3 py-1.5 text-xs font-medium transition",
                      priority === "urgent"
                        ? "bg-amber-500 text-white shadow-sm"
                        : "text-sanad-muted hover:text-amber-700",
                    )}
                  >
                    عاجل
                  </button>
                </div>
              </div>
              <Button
                className="w-full gap-2"
                disabled={!(polished || raw || docBody).trim() || busy !== null}
                onClick={() => void handleCompose()}
              >
                {busy === "compose" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileText className="h-4 w-4" />
                )}
                توليد الوثيقة
              </Button>
              {error && <p className="text-sm text-red-600">{error}</p>}
            </CardContent>
          </Card>

          {docBody && (
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
              onOpenGoogleDocs={() =>
                window.open(
                  "https://docs.google.com/document/create",
                  "_blank",
                  "noopener,noreferrer",
                )
              }
              onSaveTemplate={handleSaveAsCabinetTemplate}
              onSaveToCase={handleSaveToCase}
              savingCase={busy === "save"}
              exportingWord={busy === "word"}
              savingTemplate={busy === "saveTpl"}
            />
          )}
        </div>
      </div>
    </div>
  );
}
