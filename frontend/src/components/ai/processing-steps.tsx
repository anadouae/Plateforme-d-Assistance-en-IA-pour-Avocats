import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

type DocKind = "file" | "audio";

const STEPS_FILE = [
  { id: "upload", label: "Upload sécurisé" },
  { id: "extract", label: "Extraction texte / OCR" },
  { id: "index", label: "Indexation vectorielle" },
] as const;

const STEPS_AUDIO = [
  { id: "upload", label: "Upload sécurisé" },
  { id: "extract", label: "جارٍ تفريغ الصوت… / Transcription Whisper" },
  { id: "index", label: "Indexation vectorielle" },
] as const;

type StepId = (typeof STEPS_FILE)[number]["id"];

interface ProcessingStepsProps {
  status: string;
  kind?: DocKind;
  className?: string;
}

function activeStep(status: string): StepId {
  if (status === "pending") return "upload";
  if (status === "processing") return "extract";
  return "index";
}

export function ProcessingSteps({ status, kind = "file", className }: ProcessingStepsProps) {
  if (status === "indexed" || status === "failed") return null;

  const steps = kind === "audio" ? STEPS_AUDIO : STEPS_FILE;
  const current = activeStep(status);
  const currentIdx = steps.findIndex((s) => s.id === current);

  return (
    <div className={cn("rounded-xl border border-sanad-border bg-white p-4", className)}>
      <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
        {kind === "audio" ? "Pipeline audio (Whisper)" : "Pipeline documentaire"}
      </p>
      <div className="space-y-2">
        {steps.map((step, idx) => {
          const done = idx < currentIdx || status === "indexed";
          const active = idx === currentIdx;
          return (
            <div key={step.id} className="flex items-center gap-3 text-sm">
              {done ? (
                <CheckCircle2 className="h-4 w-4 text-sanad-gold" />
              ) : active ? (
                <Loader2 className="h-4 w-4 animate-spin text-sanad-blue" />
              ) : (
                <Circle className="h-4 w-4 text-slate-300" />
              )}
              <span
                className={cn(
                  done && "text-slate-600",
                  active && "font-medium text-sanad-blue",
                  !done && !active && "text-slate-400",
                )}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
