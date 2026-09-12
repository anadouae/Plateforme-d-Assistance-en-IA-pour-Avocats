"use client";

import { AlertTriangle, CheckCircle2, Clock, Loader2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useLocaleStore } from "@/store/locale";

const STATUS_CONFIG: Record<
  string,
  { labelFr: string; labelAr: string; icon: typeof CheckCircle2; className: string }
> = {
  pending: {
    labelFr: "En attente",
    labelAr: "قيد الانتظار",
    icon: Clock,
    className: "bg-sanad-stone text-sanad-navy/70",
  },
  processing: {
    labelFr: "Traitement",
    labelAr: "جارٍ المعالجة",
    icon: Loader2,
    className: "bg-sanad-gold/15 text-sanad-navy",
  },
  indexed: {
    labelFr: "Prêt",
    labelAr: "جاهز",
    icon: CheckCircle2,
    className: "bg-sanad-gold/25 text-sanad-navy",
  },
  ready: {
    labelFr: "Prêt",
    labelAr: "جاهز",
    icon: CheckCircle2,
    className: "bg-sanad-gold/25 text-sanad-navy",
  },
  done: {
    labelFr: "Prêt",
    labelAr: "جاهز",
    icon: CheckCircle2,
    className: "bg-sanad-gold/25 text-sanad-navy",
  },
  failed: {
    labelFr: "Illisible",
    labelAr: "غير قابل للقراءة",
    icon: XCircle,
    className: "bg-red-50 text-red-700",
  },
};

interface DocumentStatusBadgeProps {
  status: string;
  ocrScore?: number | null;
  ocrAlert?: boolean;
  /** audio | pdf | docx | image — pour libellés corrects */
  kind?: string | null;
  className?: string;
}

export function DocumentStatusBadge({
  status,
  ocrScore,
  ocrAlert,
  kind,
  className,
}: DocumentStatusBadgeProps) {
  const locale = useLocaleStore((s) => s.locale);
  const ar = locale === "ar";
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  const Icon = config.icon;
  const spinning = status === "processing" || status === "pending";
  const label = ar ? config.labelAr : config.labelFr;
  const isDocx = (kind || "").toLowerCase().includes("doc");
  const isAudio = (kind || "").toLowerCase() === "audio";
  const isReady = ["indexed", "ready", "done"].includes(status);

  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      <span
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
          config.className,
        )}
      >
        <Icon className={cn("h-3.5 w-3.5", spinning && "animate-spin")} />
        {label}
        {spinning ? "…" : null}
      </span>
      {spinning && (
        <span className="text-xs text-sanad-blue/80">
          {ar ? "تحليل جارٍ…" : "Analyse en cours…"}
        </span>
      )}
      {isReady && isDocx && ocrScore == null && (
        <span className="text-xs text-emerald-700">
          {ar ? "Word · نص أصلي" : "Word · texte natif"}
        </span>
      )}
      {isReady && isAudio && (
        <span className="text-xs text-slate-500">
          {ar ? "تفريغ صوتي" : "Transcription audio"}
        </span>
      )}
      {ocrScore != null && !isDocx && !isAudio && (
        <span className="text-xs text-slate-500">
          {ar ? `جودة القراءة ${ocrScore}%` : `Qualité lecture ${ocrScore}%`}
        </span>
      )}
      {ocrAlert && !isDocx && !isAudio && (
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-xs text-amber-700">
          <AlertTriangle className="h-3 w-3" />
          {ar ? "جودة قراءة ضعيفة — تحققوا من المستند" : "Qualité de lecture faible — vérifiez le document"}
        </span>
      )}
    </div>
  );
}
