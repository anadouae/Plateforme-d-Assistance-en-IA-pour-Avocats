"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  Calendar,
  DollarSign,
  FileText,
  Loader2,
  RefreshCw,
  Users,
} from "lucide-react";
import { MarkdownAnswer } from "@/components/ai/markdown-answer";
import { Button } from "@/components/ui/button";
import { locales, type Locale } from "@/lib/i18n/translations";
import { api, ApiError, getClientLocale, type SynthesisResult } from "@/lib/api";
import { useLocaleStore } from "@/store/locale";
import { cn } from "@/lib/utils";

interface SynthesisPanelProps {
  documentId: string;
  documentName: string;
  canAnalyze: boolean;
  hasText: boolean;
  kind?: "audio" | "file" | string;
  className?: string;
}

const LABELS: Record<
  Locale,
  {
    parties: string;
    dates: string;
    amounts: string;
    risks: string;
    executive: string;
    sources: string;
    loading: string;
    loadingHint: string;
    insufficient: string;
    insufficientHint: string;
    insufficientHintAudio: string;
    pending: string;
    pendingAudio: string;
    refresh: string;
    error: string;
  }
> = {
  fr: {
    parties: "Parties",
    dates: "Dates clés",
    amounts: "Montants",
    risks: "Clauses à risque",
    executive: "Synthèse intelligente",
    sources: "Source documentaire",
    loading: "Analyse intelligente du document…",
    loadingHint: "Le modèle lit la pièce et rédige une synthèse de cabinet.",
    insufficient: "Texte insuffisant pour une synthèse",
    insufficientHint: "Vérifiez la qualité du scan ou ré-extrayez le texte.",
    insufficientHintAudio: "Vérifiez le fichier audio ou relancez la transcription.",
    pending: "En attente du texte extrait…",
    pendingAudio: "En attente de la transcription…",
    refresh: "Actualiser",
    error: "Impossible de générer la synthèse. Réessayez.",
  },
  ar: {
    parties: "الأطراف",
    dates: "التواريخ الرئيسية",
    amounts: "المبالغ",
    risks: "بنود المخاطر",
    executive: "تلخيص ذكي",
    sources: "مصدر الوثيقة",
    loading: "جاري التحليل الذكي للوثيقة…",
    loadingHint: "يقرأ النموذج القطعة ويُعد تلخيصاً للمكتب.",
    insufficient: "النص غير كافٍ للتلخيص",
    insufficientHint: "تحقق من جودة المسح أو أعد الاستخراج.",
    insufficientHintAudio: "تحقق من الملف الصوتي أو أعد التفريغ.",
    pending: "في انتظار النص المستخرج…",
    pendingAudio: "في انتظار التفريغ الصوتي…",
    refresh: "تحديث",
    error: "تعذر إنشاء التلخيص. حاول مجدداً.",
  },
};

function SynthesisSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-20 rounded-lg bg-slate-100" />
        ))}
      </div>
      <div className="h-40 rounded-lg bg-slate-100" />
    </div>
  );
}

function InfoBlock({
  icon: Icon,
  title,
  items,
  variant = "default",
}: {
  icon: typeof Users;
  title: string;
  items: string[];
  variant?: "default" | "risk";
}) {
  return (
    <div
      className={cn(
        "rounded-xl border p-4",
        variant === "risk"
          ? "border-amber-200 bg-amber-50/50"
          : "border-sanad-border bg-sanad-light/50",
      )}
    >
      <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
        <Icon className="h-3.5 w-3.5" />
        {title}
      </div>
      <ul className="space-y-1 text-sm text-sanad-slate">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function SynthesisLangSwitch({
  value,
  onChange,
  disabled,
}: {
  value: Locale;
  onChange: (locale: Locale) => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex items-center rounded-lg border border-sanad-gold/20 bg-sanad-cream p-0.5 text-xs font-semibold">
      {locales.map((l) => (
        <button
          key={l.code}
          type="button"
          disabled={disabled}
          onClick={() => onChange(l.code as Locale)}
          className={cn(
            "rounded-md px-2.5 py-1 transition-all duration-200 disabled:opacity-50",
            value === l.code
              ? "bg-sanad-navy text-sanad-ivory shadow-sm"
              : "text-sanad-muted hover:text-sanad-navy",
          )}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}

export function SynthesisPanel({
  documentId,
  documentName,
  canAnalyze,
  hasText,
  kind = "file",
  className,
}: SynthesisPanelProps) {
  const appLocale = useLocaleStore((s) => s.locale);
  const [lang, setLang] = useState<Locale>(() => getClientLocale() as Locale);
  const [cache, setCache] = useState<Partial<Record<Locale, SynthesisResult>>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const requestId = useRef(0);
  const cacheRef = useRef(cache);
  cacheRef.current = cache;
  const isAudio = kind === "audio";

  useEffect(() => {
    setLang(appLocale);
  }, [appLocale]);

  useEffect(() => {
    setCache({});
    setError("");
  }, [documentId]);

  const labels = LABELS[lang];
  const synthesis = cache[lang] ?? null;

  const load = useCallback(
    async (targetLang: Locale, force = false) => {
      if (!canAnalyze || !hasText) return;
      if (!force && cacheRef.current[targetLang]) return;

      const id = ++requestId.current;
      setLoading(true);
      setError("");
      try {
        const result = await api.getSynthesis(documentId, targetLang);
        if (id !== requestId.current) return;
        setCache((prev) => ({ ...prev, [targetLang]: result }));
      } catch (e) {
        if (id !== requestId.current) return;
        setError(
          e instanceof ApiError ? e.message : LABELS[targetLang].error,
        );
      } finally {
        if (id === requestId.current) setLoading(false);
      }
    },
    [canAnalyze, hasText, documentId],
  );

  useEffect(() => {
    if (!canAnalyze || !hasText) return;
    void load(lang);
  }, [canAnalyze, hasText, lang, documentId, load]);

  if (!canAnalyze) {
    return (
      <p className="text-sm text-slate-500">
        {isAudio ? labels.pendingAudio : labels.pending}
      </p>
    );
  }

  if (!hasText) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <div className="flex items-start gap-2">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <div>
            <p className="font-medium">{labels.insufficient}</p>
            <p className="mt-1 text-amber-800/80">
              {isAudio ? labels.insufficientHintAudio : labels.insufficientHint}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          {documentName}
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <SynthesisLangSwitch
            value={lang}
            disabled={loading}
            onChange={(next) => {
              setLang(next);
            }}
          />
          {synthesis && (
            <Button
              variant="ghost"
              size="sm"
              disabled={loading}
              onClick={() => void load(lang, true)}
            >
              <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin")} />
              {labels.refresh}
            </Button>
          )}
        </div>
      </div>

      {loading && !synthesis && (
        <div className="space-y-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-sanad-blue">
              <Loader2 className="h-4 w-4 animate-spin" />
              {labels.loading}
            </div>
            {labels.loadingHint ? (
              <p className="text-xs text-slate-500">{labels.loadingHint}</p>
            ) : null}
          </div>
          <SynthesisSkeleton />
        </div>
      )}

      {error && !synthesis && (
        <div className="space-y-3">
          <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
          <Button variant="outline" size="sm" onClick={() => void load(lang, true)}>
            {labels.refresh}
          </Button>
        </div>
      )}

      {synthesis && (
        <div
          className={cn("space-y-4", loading && "opacity-60")}
          dir={lang === "ar" ? "rtl" : "ltr"}
          lang={lang}
        >
          {synthesis.attention_points.length > 0 && (
            <div className="space-y-2">
              {synthesis.attention_points.map((point, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900"
                >
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                  {point}
                </div>
              ))}
            </div>
          )}

          <div className="grid gap-3 sm:grid-cols-2">
            {synthesis.parties.length > 0 && (
              <InfoBlock icon={Users} title={labels.parties} items={synthesis.parties} />
            )}
            {synthesis.key_dates.length > 0 && (
              <InfoBlock icon={Calendar} title={labels.dates} items={synthesis.key_dates} />
            )}
            {synthesis.amounts.length > 0 && (
              <InfoBlock icon={DollarSign} title={labels.amounts} items={synthesis.amounts} />
            )}
            {synthesis.risk_clauses.length > 0 && (
              <InfoBlock
                icon={FileText}
                title={labels.risks}
                items={synthesis.risk_clauses}
                variant="risk"
              />
            )}
          </div>

          <div className="rounded-xl border border-sanad-green/20 bg-sanad-green/5 p-4">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-sanad-green">
              {labels.executive}
            </p>
            <MarkdownAnswer text={synthesis.summary} sources={synthesis.sources} />
          </div>

          {synthesis.sources.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {labels.sources}
              </p>
              {synthesis.sources.map((src, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-sanad-border bg-white p-3 text-sm"
                >
                  <p className="font-medium text-sanad-blue">{src.label}</p>
                  <p className="mt-1 text-slate-600">{src.excerpt}</p>
                </div>
              ))}
            </div>
          )}
          <p className="text-xs italic text-slate-400">{synthesis.disclaimer}</p>
        </div>
      )}
    </div>
  );
}
