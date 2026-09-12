"use client";

import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, Copy, ListTree, X } from "lucide-react";

export type FormEdit = {
  id: string;
  original: string;
  proposed: string;
  kind: string;
};

export type PleaVariable = {
  kind: string;
  value: string;
  label_ar: string;
  label_fr: string;
};

export type StructureHint = {
  section_ar: string;
  section_fr: string;
  excerpt: string;
  message_ar: string;
  message_fr: string;
};

export type LawSuggestion = {
  code_ar: string;
  code_fr: string;
  article: string;
  reason_ar: string;
  reason_fr: string;
  insert_ar: string;
};

type Props = {
  uiFr: boolean;
  edits: FormEdit[];
  variables: PleaVariable[];
  polished: string;
  onPolishedChange: (next: string) => void;
};

/**
 * Panneau d'assistance non-destructive :
 * - Accepter / Refuser chaque correction de forme
 * - Variables extraites (copie)
 */
export function PleaAssistPanel({
  uiFr,
  edits,
  variables,
  polished,
  onPolishedChange,
}: Props) {
  const [editState, setEditState] = useState<Record<string, "pending" | "accepted" | "rejected">>(
    {},
  );
  const [copied, setCopied] = useState<string | null>(null);

  const pendingEdits = useMemo(() => {
    const real = edits.filter((e) => {
      const o = (e.original || "").replace(/\s+/g, " ").trim();
      const p = (e.proposed || "").replace(/\s+/g, " ").trim();
      if (!o || !p || o === p || o === "…") return false;
      // Même texte « visuel » (diacritiques / ة↔ه / ponctuation)
      const norm = (s: string) =>
        s
          .replace(/[\u064B-\u065F\u0670\u0640]/g, "")
          .replace(/[،,.;:؟!?()[\]‹›«»"'\-–—/]/g, "")
          .replace(/[أإآ]/g, "ا")
          .replace(/ة/g, "ه")
          .replace(/\s+/g, "");
      return norm(o) !== norm(p);
    });
    return real.filter((e) => (editState[e.id] || "pending") === "pending");
  }, [edits, editState]);

  const visibleEdits = useMemo(() => {
    return edits.filter((e) => {
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
  }, [edits]);

  function mark(id: string, status: "accepted" | "rejected") {
    setEditState((s) => ({ ...s, [id]: status }));
  }

  function acceptEdit(e: FormEdit) {
    // Déjà dans le texte corrigé — on retire juste le marquage ‹ ›
    let next = polished;
    if (e.proposed && e.proposed !== "…") {
      next = next.replaceAll(`‹${e.proposed}›`, e.proposed);
    }
    onPolishedChange(next);
    mark(e.id, "accepted");
  }

  function rejectEdit(e: FormEdit) {
    let next = polished;
    if (e.kind === "removed" || e.proposed === "—") {
      next = `${e.original} ${next}`.replace(/\s{2,}/g, " ").trim();
    } else if (e.original && e.original !== "…" && e.proposed && e.proposed !== "—") {
      next = next.replaceAll(`‹${e.proposed}›`, e.original);
      if (next === polished) {
        next = next.replace(e.proposed, e.original);
      }
    } else if (e.kind === "insert" && e.proposed) {
      next = next.replace(e.proposed, "").replace(/\s{2,}/g, " ").trim();
    } else if (e.proposed) {
      next = next.replaceAll(`‹${e.proposed}›`, e.proposed);
    }
    onPolishedChange(next);
    mark(e.id, "rejected");
  }

  function acceptAll() {
    let next = polished.replace(/‹([^›]+)›/g, "$1");
    onPolishedChange(next);
    const all: Record<string, "accepted"> = {};
    for (const e of visibleEdits) all[e.id] = "accepted";
    setEditState(all);
  }

  function rejectAll() {
    let next = polished;
    for (const e of visibleEdits) {
      if (e.original && e.original !== "…" && e.proposed) {
        next = next.replaceAll(`‹${e.proposed}›`, e.original);
        next = next.replace(e.proposed, e.original);
      }
    }
    next = next.replace(/‹([^›]+)›/g, "$1");
    onPolishedChange(next);
    const all: Record<string, "rejected"> = {};
    for (const e of visibleEdits) all[e.id] = "rejected";
    setEditState(all);
  }

  async function copyValue(v: string) {
    try {
      await navigator.clipboard.writeText(v);
      setCopied(v);
      setTimeout(() => setCopied(null), 1500);
    } catch {
      /* ignore */
    }
  }

  if (!visibleEdits.length && !variables.length) {
    return null;
  }

  return (
    <div className="plea-assist" dir={uiFr ? "ltr" : "rtl"}>
      <p className="plea-assist__banner">
        {uiFr
          ? "Assistance non-destructive — corrections STT déjà appliquées dans le texte. Variables extraites ci-dessous."
          : "مساعدة غير مدمّرة — تصحيحات التفريغ مُطبَّقة في النص. المعطيات المستخرجة أدناه."}
      </p>

      {visibleEdits.length > 0 && (
        <section className="plea-assist__section">
          <header className="plea-assist__head">
            <ListTree className="h-4 w-4" />
            <span>
              {uiFr
                ? `Corrections restantes (${pendingEdits.length})`
                : `تصحيحات متبقية (${pendingEdits.length})`}
            </span>
            <div className="plea-assist__actions">
              <button type="button" className="chip-btn primary polish-chip-btn" onClick={acceptAll}>
                {uiFr ? "Tout accepter" : "قبول الكل"}
              </button>
              <button type="button" className="chip-btn polish-chip-btn" onClick={rejectAll}>
                {uiFr ? "Tout refuser" : "رفض الكل"}
              </button>
            </div>
          </header>
          <AnimatePresence initial={false}>
            {visibleEdits.map((e) => {
              const st = editState[e.id] || "pending";
              if (st !== "pending") return null;
              return (
                <motion.div
                  key={e.id}
                  layout
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  className="plea-assist__edit"
                >
                      <p className={`plea-assist__edit-text${uiFr ? "" : " arabic-text"}`} dir={uiFr ? "ltr" : "rtl"}>
                        {e.kind === "removed" || e.proposed === "—" ? (
                          <>
                            <del>{e.original}</del>
                            <span aria-hidden> → </span>
                            <span className="plea-assist__removed-tag">
                              {uiFr ? "supprimé (STT)" : "حذف (تفريغ)"}
                            </span>
                          </>
                        ) : e.original !== "…" ? (
                          <>
                            <del>{e.original}</del>
                            <span aria-hidden> → </span>
                            <ins>{e.proposed}</ins>
                          </>
                        ) : (
                          <ins>{e.proposed}</ins>
                        )}
                      </p>
                  <div className="plea-assist__edit-btns">
                    <button
                      type="button"
                      className="chip-btn primary polish-chip-btn"
                      onClick={() => acceptEdit(e)}
                    >
                      <Check className="h-3.5 w-3.5" />
                      {uiFr ? "Accepter" : "قبول"}
                    </button>
                    <button
                      type="button"
                      className="chip-btn polish-chip-btn"
                      onClick={() => rejectEdit(e)}
                    >
                      <X className="h-3.5 w-3.5" />
                      {uiFr ? "Refuser" : "رفض"}
                    </button>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </section>
      )}

      {variables.length > 0 && (
        <section className="plea-assist__section">
          <header className="plea-assist__head">
            <Copy className="h-4 w-4" />
            <span>{uiFr ? "Données extraites (n°, date, noms — clic = copier)" : "معطيات مستخرجة (رقم، تاريخ، أسماء — انقر للنسخ)"}</span>
          </header>
          <div className="plea-assist__chips">
            {variables.map((v) => (
              <button
                key={`${v.kind}-${v.value}`}
                type="button"
                className="chip-btn polish-chip-btn"
                title={uiFr ? v.label_fr : v.label_ar}
                onClick={() => void copyValue(v.value)}
              >
                <span className="plea-assist__chip-label">
                  {uiFr ? v.label_fr : v.label_ar}
                </span>
                {v.value}
                {copied === v.value ? " ✓" : ""}
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
