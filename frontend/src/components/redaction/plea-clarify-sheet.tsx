"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Loader2, Shield, Sparkles, X } from "lucide-react";
import type { ClarifyDictationResult, ClarifyQuestion } from "@/lib/api";

export type ClarifyAnswer = {
  id: string;
  choice?: string;
  other?: string;
  label?: string;
};

type Props = {
  open: boolean;
  uiFr: boolean;
  loading?: boolean;
  data: ClarifyDictationResult | null;
  onClose: () => void;
  onSkip: () => void;
  onConfirm: (answers: ClarifyAnswer[]) => void;
};

export function PleaClarifySheet({
  open,
  uiFr,
  loading,
  data,
  onClose,
  onSkip,
  onConfirm,
}: Props) {
  const questions = data?.questions || [];
  const [answers, setAnswers] = useState<Record<string, { choiceId?: string; other?: string }>>({});

  useEffect(() => {
    if (!open) setAnswers({});
  }, [open, data?.provider]);

  function selectOption(q: ClarifyQuestion, optId: string) {
    setAnswers((prev) => ({
      ...prev,
      [q.id]: { choiceId: optId, other: undefined },
    }));
  }

  function setOther(q: ClarifyQuestion, text: string) {
    setAnswers((prev) => ({
      ...prev,
      [q.id]: { choiceId: "__other__", other: text },
    }));
  }

  function buildPayload(): ClarifyAnswer[] {
    return questions.map((q) => {
      const a = answers[q.id];
      if (!a) return { id: q.id };
      if (a.choiceId === "__other__") {
        return { id: q.id, choice: "autre", other: (a.other || "").trim(), label: a.other };
      }
      const opt = q.options.find((o) => o.id === a.choiceId);
      const label = uiFr ? opt?.label_fr : opt?.label_ar;
      return { id: q.id, choice: label || a.choiceId, label: label || a.choiceId };
    });
  }

  if (!open) return null;

  return (
    <AnimatePresence>
      <motion.div
        key="clarify-backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.22 }}
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 80,
          background: "rgba(14, 21, 38, 0.45)",
          backdropFilter: "blur(6px)",
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "center",
          padding: "16px 12px 20px",
        }}
        onMouseDown={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
      >
        <motion.div
          role="dialog"
          aria-modal="true"
          aria-labelledby="clarify-title"
          initial={{ y: 40, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 28, opacity: 0 }}
          transition={{ type: "spring", stiffness: 380, damping: 32 }}
          style={{
            width: "min(560px, 100%)",
            maxHeight: "min(82vh, 720px)",
            overflow: "auto",
            borderRadius: 22,
            border: "1px solid rgba(201, 168, 74, 0.35)",
            background:
              "linear-gradient(165deg, rgba(255,252,246,0.98) 0%, rgba(245,240,230,0.96) 55%, rgba(255,255,255,0.98) 100%)",
            boxShadow: "0 24px 60px rgba(14,21,38,0.28)",
            padding: "20px 18px 16px",
          }}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
            <div>
              <p
                id="clarify-title"
                style={{
                  margin: 0,
                  fontSize: 17,
                  fontWeight: 700,
                  color: "#1B3F9C",
                  letterSpacing: "-0.02em",
                }}
              >
                {uiFr ? "Clarification rapide" : "توضيح سريع"}
              </p>
              <p style={{ margin: "6px 0 0", fontSize: 12, color: "#5c6578", lineHeight: 1.5 }}>
                {loading
                  ? uiFr
                    ? "Lecture anonymisée du dossier et des pièces…"
                    : "قراءة مجهولة الهوية للملف والمرفقات…"
                  : uiFr
                    ? data
                      ? `L’IA a croisé ${data.pieces_noted} pièce(s) · ${questions.length} point(s) à confirmer. Noms masqués (${(data.pii_tokens || []).join(", ") || "—"}) avant analyse.`
                      : "Prêt."
                    : data
                      ? `حُللت ${data.pieces_noted} مرفق(ات) · ${questions.length} نقطة للتأكيد.`
                      : "جاهز."}
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label={uiFr ? "Fermer" : "إغلاق"}
              style={{
                width: 36,
                height: 36,
                borderRadius: 999,
                border: "1px solid rgba(14,21,38,0.12)",
                background: "rgba(255,255,255,0.8)",
                display: "grid",
                placeItems: "center",
                cursor: "pointer",
              }}
            >
              <X size={16} />
            </button>
          </div>

          {loading ? (
            <div
              style={{
                marginTop: 28,
                marginBottom: 20,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 12,
                padding: "28px 12px",
              }}
            >
              <Loader2 className="h-8 w-8 animate-spin" style={{ color: "#1B3F9C" }} />
              <p style={{ margin: 0, fontSize: 13, color: "#1B3F9C", fontWeight: 600 }}>
                {uiFr ? "Analyse confidentielle en cours…" : "تحليل سري جارٍ…"}
              </p>
              <p
                style={{
                  margin: 0,
                  fontSize: 11,
                  color: "#5c6578",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                <Shield size={12} />
                {uiFr ? "PARTIE_A… — aucun vrai nom envoyé" : "PARTIE_A… — لا أسماء حقيقية"}
              </p>
            </div>
          ) : (
            <>
              {(uiFr ? data?.summary_fr : data?.summary_ar) ? (
                <p
                  style={{
                    margin: "14px 0 0",
                    padding: "10px 12px",
                    borderRadius: 14,
                    background: "rgba(27,63,156,0.06)",
                    border: "1px solid rgba(27,63,156,0.12)",
                    fontSize: 13,
                    lineHeight: 1.55,
                    color: "#1a2744",
                  }}
                >
                  {uiFr ? data?.summary_fr : data?.summary_ar}
                </p>
              ) : null}

              {questions.length === 0 ? (
                <p style={{ margin: "18px 0", fontSize: 13, color: "#5c6578", lineHeight: 1.5 }}>
                  {uiFr
                    ? "Aucune ambiguïté détectée — vous pouvez lancer la rédaction fusḥā directement."
                    : "لا غموض مكتشف — يمكن بدء الصياغة بالفصحى مباشرة."}
                </p>
              ) : (
                <div style={{ marginTop: 14, display: "grid", gap: 14 }}>
                  {questions.map((q, qi) => {
                    const a = answers[q.id];
                    return (
                      <motion.div
                        key={q.id}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: qi * 0.05 }}
                        style={{
                          padding: "12px 12px 10px",
                          borderRadius: 16,
                          border: "1px solid rgba(14,21,38,0.08)",
                          background: "rgba(255,255,255,0.72)",
                        }}
                      >
                        <p style={{ margin: "0 0 10px", fontSize: 13, fontWeight: 700, color: "#0e1526", lineHeight: 1.45 }}>
                          <span style={{ color: "#C9A84A", marginInlineEnd: 6 }}>{qi + 1}.</span>
                          {uiFr ? q.prompt_fr : q.prompt_ar}
                        </p>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                          {q.options.map((o) => {
                            const sel = a?.choiceId === o.id;
                            return (
                              <button
                                key={o.id}
                                type="button"
                                onClick={() => selectOption(q, o.id)}
                                style={{
                                  borderRadius: 999,
                                  padding: "7px 12px",
                                  fontSize: 12,
                                  fontWeight: 600,
                                  border: sel
                                    ? "1.5px solid #1B3F9C"
                                    : "1px solid rgba(14,21,38,0.14)",
                                  background: sel ? "rgba(27,63,156,0.1)" : "#fff",
                                  color: sel ? "#1B3F9C" : "#334155",
                                  cursor: "pointer",
                                }}
                              >
                                {sel ? <Check size={12} style={{ marginInlineEnd: 4, display: "inline" }} /> : null}
                                {uiFr ? o.label_fr : o.label_ar}
                              </button>
                            );
                          })}
                          {q.allow_other ? (
                            <button
                              type="button"
                              onClick={() => setOther(q, a?.other || "")}
                              style={{
                                borderRadius: 999,
                                padding: "7px 12px",
                                fontSize: 12,
                                fontWeight: 600,
                                border:
                                  a?.choiceId === "__other__"
                                    ? "1.5px solid #C9A84A"
                                    : "1px dashed rgba(14,21,38,0.2)",
                                background: a?.choiceId === "__other__" ? "rgba(201,168,74,0.12)" : "transparent",
                                color: "#5c4a1e",
                                cursor: "pointer",
                              }}
                            >
                              {uiFr ? "Autre…" : "أخرى…"}
                            </button>
                          ) : null}
                        </div>
                        {a?.choiceId === "__other__" ? (
                          <input
                            autoFocus
                            value={a.other || ""}
                            onChange={(e) => setOther(q, e.target.value)}
                            placeholder={uiFr ? "Précisez…" : "وضّحوا…"}
                            style={{
                              marginTop: 10,
                              width: "100%",
                              borderRadius: 12,
                              border: "1px solid rgba(201,168,74,0.45)",
                              padding: "9px 11px",
                              fontSize: 13,
                              background: "#fff",
                            }}
                          />
                        ) : null}
                      </motion.div>
                    );
                  })}
                </div>
              )}

              <div
                style={{
                  marginTop: 18,
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 10,
                  justifyContent: "flex-end",
                }}
              >
                <button
                  type="button"
                  onClick={onSkip}
                  style={{
                    borderRadius: 12,
                    padding: "10px 14px",
                    fontSize: 13,
                    fontWeight: 600,
                    border: "1px solid rgba(14,21,38,0.14)",
                    background: "transparent",
                    color: "#5c6578",
                    cursor: "pointer",
                  }}
                >
                  {uiFr ? "Passer et rédiger" : "تخطٍ والصياغة"}
                </button>
                <button
                  type="button"
                  onClick={() => onConfirm(buildPayload())}
                  style={{
                    borderRadius: 12,
                    padding: "10px 16px",
                    fontSize: 13,
                    fontWeight: 700,
                    border: "none",
                    background: "linear-gradient(135deg, #1B3F9C 0%, #16327a 100%)",
                    color: "#fff",
                    cursor: "pointer",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 8,
                    boxShadow: "0 8px 20px rgba(27,63,156,0.28)",
                  }}
                >
                  <Sparkles size={14} />
                  {uiFr ? "Confirmer et rédiger" : "تأكيد والصياغة"}
                </button>
              </div>
            </>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
