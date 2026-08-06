import { AlertTriangle, CheckCircle2, Clock, Loader2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

const STATUS_CONFIG: Record<
  string,
  { label: string; icon: typeof CheckCircle2; className: string }
> = {
  pending: {
    label: "En attente",
    icon: Clock,
    className: "bg-sanad-stone text-sanad-navy/70",
  },
  processing: {
    label: "Traitement",
    icon: Loader2,
    className: "bg-sanad-gold/15 text-sanad-navy",
  },
  indexed: {
    label: "Indexé",
    icon: CheckCircle2,
    className: "bg-sanad-gold/25 text-sanad-navy",
  },
  failed: {
    label: "Échec",
    icon: XCircle,
    className: "bg-red-50 text-red-700",
  },
};

interface DocumentStatusBadgeProps {
  status: string;
  ocrScore?: number | null;
  ocrAlert?: boolean;
  className?: string;
}

export function DocumentStatusBadge({
  status,
  ocrScore,
  ocrAlert,
  className,
}: DocumentStatusBadgeProps) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  const Icon = config.icon;
  const spinning = status === "processing";

  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      <span
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
          config.className,
        )}
      >
        <Icon className={cn("h-3.5 w-3.5", spinning && "animate-spin")} />
        {config.label}
      </span>
      {ocrScore != null && (
        <span className="text-xs text-slate-500">OCR {ocrScore}%</span>
      )}
      {ocrAlert && (
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-800">
          <AlertTriangle className="h-3 w-3" />
          Qualité OCR faible
        </span>
      )}
    </div>
  );
}
