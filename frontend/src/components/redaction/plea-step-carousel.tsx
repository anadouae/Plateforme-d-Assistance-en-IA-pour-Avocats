"use client";

import { motion } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Download,
  FileText,
  Mic,
  Settings2,
  Type,
} from "lucide-react";
import { useRef } from "react";
import { cn } from "@/lib/utils";

export type PleaStepId = "dictate" | "transcript" | "settings" | "document" | "export";

export type PleaStepStatus = "todo" | "current" | "done";

export type PleaStepDef = {
  id: PleaStepId;
  labelFr: string;
  labelAr: string;
  hintFr: string;
  hintAr: string;
  Icon: typeof Mic;
  accent: string;
};

export const PLEA_STEPS: PleaStepDef[] = [
  {
    id: "settings",
    labelFr: "Dossier & pièces",
    labelAr: "الملف والمرفقات",
    hintFr: "Lier le dossier · pièces jointes",
    hintAr: "ربط الملف · المرفقات",
    Icon: Settings2,
    accent: "#C9A84A",
  },
  {
    id: "dictate",
    labelFr: "Dictée",
    labelAr: "إملاء",
    hintFr: "Micro · voix de l'avocat",
    hintAr: "ميكروفون · صوت المحامي",
    Icon: Mic,
    accent: "#4C7CFF",
  },
  {
    id: "transcript",
    labelFr: "Transcription",
    labelAr: "تفريغ",
    hintFr: "Corriger · vérifier",
    hintAr: "تصحيح · مراجعة",
    Icon: Type,
    accent: "#FF6A00",
  },
  {
    id: "document",
    labelFr: "Rédaction IA",
    labelAr: "الصياغة بالذكاء",
    hintFr: "Plaidoirie professionnelle",
    hintAr: "مرافعة مهنية",
    Icon: FileText,
    accent: "#1B3F9C",
  },
  {
    id: "export",
    labelFr: "Export",
    labelAr: "تصدير",
    hintFr: "Word · PDF · modèle",
    hintAr: "Word · PDF · نموذج",
    Icon: Download,
    accent: "#57A88C",
  },
];

type Props = {
  step: number;
  onStepChange: (i: number) => void;
  statuses: PleaStepStatus[];
  uiFr: boolean;
};

export function PleaStepCarousel({ step, onStepChange, statuses, uiFr }: Props) {
  const n = PLEA_STEPS.length;
  const touchX = useRef<number | null>(null);
  const current = PLEA_STEPS[step]!;
  const next = step < n - 1 ? PLEA_STEPS[step + 1] : null;
  const fillPct = n <= 1 ? 0 : (step / (n - 1)) * 100;

  function go(delta: number) {
    onStepChange(Math.max(0, Math.min(n - 1, step + delta)));
  }

  return (
    <div className="plea-carousel">
      <div className="plea-pipe">
        <div className="plea-pipe__meta">
          <span className="plea-pipe__kicker">
            {uiFr ? `Étape ${step + 1} / ${n}` : `الخطوة ${step + 1} / ${n}`}
          </span>
          <p className="plea-pipe__title">{uiFr ? current.labelFr : current.labelAr}</p>
          <p className="plea-pipe__hint">{uiFr ? current.hintFr : current.hintAr}</p>
        </div>
        <div className="plea-pipe__rail" role="list">
          <span className="plea-pipe__track" aria-hidden>
            <span className="plea-pipe__fill" style={{ width: `${fillPct}%` }} />
          </span>
          {PLEA_STEPS.map((s, i) => {
            const st = statuses[i] || "todo";
            const active = i === step;
            const Icon = s.Icon;
            return (
              <button
                key={s.id}
                type="button"
                role="listitem"
                className={cn("plea-pipe__node", active && "is-active", `is-${st}`)}
                onClick={() => onStepChange(i)}
                aria-current={active ? "step" : undefined}
                aria-label={uiFr ? s.labelFr : s.labelAr}
                style={{ color: active || st === "done" ? s.accent : undefined }}
              >
                <span className="plea-pipe__dot" style={{ borderColor: s.accent, background: active || st === "done" ? s.accent : "#fff" }}>
                  {st === "done" ? "✓" : <Icon size={12} strokeWidth={2.2} color={active || st === "done" ? "#fff" : s.accent} />}
                </span>
                <span className="plea-pipe__name">{uiFr ? s.labelFr : s.labelAr}</span>
              </button>
            );
          })}
        </div>
        {next ? (
          <button type="button" className="plea-pipe__next" onClick={() => go(1)}>
            {uiFr ? `Continuer → ${next.labelFr}` : `التالي ← ${next.labelAr}`}
          </button>
        ) : (
          <p className="plea-pipe__done">
            {uiFr ? "Dernière étape — exportez Word ou PDF." : "آخر خطوة — صدّروا Word أو PDF."}
          </p>
        )}
      </div>

      <div
        className="plea-carousel__stage"
        style={{ perspective: 1000, touchAction: "pan-y" }}
        onTouchStart={(e) => {
          touchX.current = e.changedTouches[0]?.clientX ?? null;
        }}
        onTouchEnd={(e) => {
          const start = touchX.current;
          touchX.current = null;
          if (start == null) return;
          const dx = (e.changedTouches[0]?.clientX ?? start) - start;
          if (Math.abs(dx) < 48) return;
          go((uiFr ? dx < 0 : dx > 0) ? 1 : -1);
        }}
      >
        <button
          type="button"
          className="plea-carousel__nav plea-carousel__nav--prev"
          onClick={() => go(-1)}
          disabled={step <= 0}
          aria-label={uiFr ? "Étape précédente" : "الخطوة précédente"}
        >
          {uiFr ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
        </button>

        <div className="plea-carousel__track" style={{ transformStyle: "preserve-3d" }}>
          {PLEA_STEPS.map((s, i) => {
            const Icon = s.Icon;
            let offset = i - step;
            if (offset > Math.floor(n / 2)) offset -= n;
            if (offset < -Math.floor(n / 2)) offset += n;
            const visual = uiFr ? offset : -offset;
            const abs = Math.abs(offset);
            const active = offset === 0;
            const st = statuses[i] || "todo";
            return (
              <motion.button
                key={s.id}
                type="button"
                className={cn("plea-carousel__card", active && "is-active", `is-${st}`)}
                onClick={() => onStepChange(i)}
                style={{
                  marginLeft: -58,
                  marginTop: -48,
                  borderColor: active ? s.accent : "rgba(14,21,38,0.1)",
                  boxShadow: active
                    ? `0 18px 40px rgba(7,16,51,0.2), 0 0 28px ${s.accent}44`
                    : "0 8px 20px rgba(7,16,51,0.08)",
                }}
                animate={{
                  x: visual * 78,
                  z: active ? 60 : -abs * 70,
                  rotateY: visual * -22,
                  scale: active ? 1.08 : Math.max(0.72, 1 - abs * 0.12),
                  opacity: abs > 2 ? 0 : active ? 1 : 0.55,
                }}
                transition={{ type: "spring", stiffness: 260, damping: 26 }}
                aria-current={active ? "step" : undefined}
                aria-label={uiFr ? s.labelFr : s.labelAr}
              >
                <span
                  className={cn("plea-carousel__badge", `badge-${st}`)}
                  aria-hidden
                >
                  {st === "done" ? "✓" : st === "current" ? "●" : String(i + 1)}
                </span>
                <span
                  className="plea-carousel__icon"
                  style={{
                    background: `${s.accent}18`,
                    color: s.accent,
                    borderColor: `${s.accent}55`,
                  }}
                >
                  <Icon size={18} strokeWidth={1.75} />
                </span>
                <span className="plea-carousel__label">
                  {uiFr ? s.labelFr : s.labelAr}
                </span>
                {active ? (
                  <span className="plea-carousel__hint">
                    {uiFr ? s.hintFr : s.hintAr}
                  </span>
                ) : null}
              </motion.button>
            );
          })}
        </div>

        <button
          type="button"
          className="plea-carousel__nav plea-carousel__nav--next"
          onClick={() => go(1)}
          disabled={step >= n - 1}
          aria-label={uiFr ? "Étape suivante" : "الخطوة التالية"}
        >
          {uiFr ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      <div className="plea-stepbar" role="tablist" aria-label={uiFr ? "Parcours" : "المسار"}>
        {PLEA_STEPS.map((s, i) => {
          const st = statuses[i] || "todo";
          const active = i === step;
          return (
            <button
              key={s.id}
              type="button"
              role="tab"
              aria-selected={active}
              className={cn("plea-stepbar__item", active && "is-active", `is-${st}`)}
              onClick={() => onStepChange(i)}
            >
              <span className="plea-stepbar__dot" style={{ background: active || st === "done" ? s.accent : undefined }} />
              <span className="plea-stepbar__text">{uiFr ? s.labelFr : s.labelAr}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
