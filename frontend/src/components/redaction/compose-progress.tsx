"use client";

import { useEffect, useState } from "react";
import { Check, Loader2 } from "lucide-react";

export type ComposeProgressStep = {
  id: string;
  labelFr: string;
  labelAr: string;
};

export function buildComposeProgressSteps(hasPieces: boolean): ComposeProgressStep[] {
  const pieces: ComposeProgressStep = hasPieces
    ? {
        id: "pieces",
        labelFr: "Analyse des pièces jointes — extraire l’utile (dates, montants, faits)",
        labelAr: "تحليل المرفقات — استخراج المفيد (تواريخ، مبالغ، وقائع)",
      }
    : {
        id: "pieces",
        labelFr: "Aucune pièce — l’IA s’appuie sur la dictée et la fiche du dossier",
        labelAr: "لا مرفقات — الاعتماد على الإملاء وبطاقة الملف",
      };
  return [
    {
      id: "dossier",
      labelFr: "Lecture du dossier : référence, type d’affaire, parties",
      labelAr: "قراءة الملف: المرجع، نوع القضية، الأطراف",
    },
    pieces,
    {
      id: "pii",
      labelFr: "Masquage intelligent des noms (PARTIE_A, B, C…) — confidentialité cabinet",
      labelAr: "إخفاء ذكي للأسماء (PARTIE_A…) — سرية المكتب",
    },
    {
      id: "clarify",
      labelFr: "Clarification avocat — questions ciblées (si besoin)",
      labelAr: "توضيح المحامي — أسئلة مركّزة عند الحاجة",
    },
    {
      id: "write",
      labelFr: "Rédaction fusḥā exhaustive (faits · arguments · ملتمسات)",
      labelAr: "صياغة فصحى شاملة (وقائع · حجج · ملتمسات)",
    },
    {
      id: "restore",
      labelFr: "Restauration des vrais noms dans le document",
      labelAr: "إعادة الأسماء الحقيقية إلى الوثيقة",
    },
    {
      id: "layout",
      labelFr: "Mise en forme de plaidoirie marocaine (افتتاح → وقائع → مناقشة → ملتمسات)",
      labelAr: "تنسيق مرافعة مغربية (افتتاح → وقائع → مناقشة → ملتمسات)",
    },
  ];
}

type Props = {
  open: boolean;
  uiFr: boolean;
  hasPieces: boolean;
};

export function ComposeProgressOverlay({ open, uiFr, hasPieces }: Props) {
  const steps = buildComposeProgressSteps(hasPieces);
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    if (!open) {
      setIdx(0);
      return;
    }
    setIdx(0);
    const id = window.setInterval(() => {
      setIdx((i) => (i < steps.length - 1 ? i + 1 : i));
    }, 1600);
    return () => window.clearInterval(id);
  }, [open, steps.length]);

  if (!open) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 80,
        background: "rgba(7,16,51,0.55)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 20,
      }}
    >
      <div
        dir={uiFr ? "ltr" : "rtl"}
        style={{
          width: "min(520px, 100%)",
          borderRadius: 20,
          background: "#fff",
          padding: "22px 22px 18px",
          boxShadow: "0 28px 80px rgba(7,16,51,0.35)",
        }}
      >
        <p style={{ margin: 0, fontSize: 12, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "#1B3F9C" }}>
          {uiFr ? "Analyse en cours" : "جاري التحليل"}
        </p>
        <p style={{ margin: "8px 0 16px", fontSize: 15, fontWeight: 700, color: "#0A1228" }}>
          {uiFr
            ? "LexHub prépare la plaidoirie — sans inventer de faits."
            : "LexHub يعدّ المرافعة — دون اختلاق وقائع."}
        </p>
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 10 }}>
          {steps.map((s, i) => {
            const done = i < idx;
            const current = i === idx;
            return (
              <li
                key={s.id}
                style={{
                  display: "flex",
                  gap: 10,
                  alignItems: "flex-start",
                  fontSize: 13,
                  lineHeight: 1.45,
                  color: current ? "#0A1228" : done ? "#1F6F54" : "#94a3b8",
                  fontWeight: current ? 650 : 500,
                }}
              >
                <span style={{ width: 20, height: 20, flexShrink: 0, display: "inline-flex", alignItems: "center", justifyContent: "center" }}>
                  {done ? (
                    <Check size={16} color="#1F6F54" />
                  ) : current ? (
                    <Loader2 size={16} className="animate-spin" color="#1B3F9C" />
                  ) : (
                    <span style={{ width: 8, height: 8, borderRadius: 99, background: "#e2e8f0" }} />
                  )}
                </span>
                {uiFr ? s.labelFr : s.labelAr}
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
