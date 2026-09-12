"use client";

import { coachFor, type CoachKey } from "@/lib/case-field-coach";

export function FieldCoach({
  field,
  uiFr,
}: {
  field: CoachKey;
  uiFr: boolean;
}) {
  const c = coachFor(field, uiFr);
  return (
    <aside
      aria-live="polite"
      dir={uiFr ? "ltr" : "rtl"}
      style={{
        margin: "0 0 14px",
        padding: "12px 14px",
        borderRadius: 14,
        border: "1px solid rgba(180, 83, 9, 0.28)",
        background: "linear-gradient(180deg, #fffbeb 0%, #fff7ed 100%)",
      }}
    >
      <p style={{ margin: 0, fontSize: 11, fontWeight: 700, letterSpacing: 0.3, color: "#9a3412" }}>
        {uiFr ? "POURQUOI CE CHAMP ?" : "لماذا هذا الحقل؟"}
      </p>
      <p style={{ margin: "4px 0 6px", fontSize: 14, fontWeight: 700, color: "#0B1A4D" }}>{c.title}</p>
      <p style={{ margin: 0, fontSize: 13, lineHeight: 1.5, color: "#334155" }}>{c.why}</p>
      <p style={{ margin: "8px 0 0", fontSize: 12.5, lineHeight: 1.45, color: "#57534e" }}>
        <strong>{uiFr ? "Exemple : " : "مثال: "}</strong>
        {c.example}
      </p>
    </aside>
  );
}
