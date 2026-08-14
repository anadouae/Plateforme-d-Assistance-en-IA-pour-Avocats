"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, type TeamMember } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useLocaleStore } from "@/store/locale";

const TYPE_PILLS = [
  { value: "Bail commercial", labelFr: "Bail commercial", labelAr: "كراء تجاري" },
  { value: "Recouvrement", labelFr: "Recouvrement", labelAr: "تحصيل" },
  { value: "Droit du travail", labelFr: "Droit du travail", labelAr: "قانون الشغل" },
  { value: "Pénal", labelFr: "Pénal", labelAr: "جنائي" },
  { value: "Famille", labelFr: "Famille", labelAr: "أسرة" },
  { value: "Autre", labelFr: "Autre", labelAr: "أخرى" },
] as const;

type Props = {
  open: boolean;
  onClose: () => void;
  onCreated?: (reference: string, id: string) => void;
  returnFocusRef?: React.RefObject<HTMLElement | null>;
};

export function NewCaseModal({ open, onClose, onCreated, returnFocusRef }: Props) {
  const router = useRouter();
  const locale = useLocaleStore((s) => s.locale);
  const ar = locale === "ar";
  const user = useAuthStore((s) => s.user);
  const year = new Date().getFullYear();
  const overlayRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const clientRef = useRef<HTMLInputElement>(null);

  const [clientName, setClientName] = useState("");
  const [caseType, setCaseType] = useState("Bail commercial");
  const [status, setStatus] = useState("En cours");
  const [responsibleId, setResponsibleId] = useState("");
  const [firstHearing, setFirstHearing] = useState("");
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<{ client?: string; type?: string; form?: string }>(
    {},
  );
  const [toast, setToast] = useState("");
  const [toastShow, setToastShow] = useState(false);

  const lawyers = useMemo(
    () =>
      team.filter(
        (m) => m.is_active && (m.role === "avocat" || m.role === "admin_cabinet"),
      ),
    [team],
  );

  useEffect(() => {
    if (!open) return;
    setClientName("");
    setCaseType("Bail commercial");
    setStatus("En cours");
    setFirstHearing("");
    setErrors({});
    setLoading(false);
    setResponsibleId(user?.id || "");
    api
      .getTeam()
      .then((list) => {
        setTeam(list);
        if (user?.id) setResponsibleId(user.id);
      })
      .catch(() => setTeam([]));

    const t = window.setTimeout(() => clientRef.current?.focus(), 50);
    return () => window.clearTimeout(t);
  }, [open, user?.id]);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        handleClose();
        return;
      }
      if (e.key !== "Tab" || !cardRef.current) return;
      const list = Array.from(
        cardRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      );
      if (!list.length) return;
      const first = list[0];
      const last = list[list.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  function handleClose() {
    onClose();
    window.setTimeout(() => returnFocusRef?.current?.focus?.(), 50);
  }

  async function handleCreate() {
    const next: typeof errors = {};
    if (!clientName.trim() || clientName.trim().length < 2) {
      next.client = ar ? "اسم الموكل مطلوب" : "Le client est obligatoire";
    }
    if (!caseType) {
      next.type = ar ? "اختر نوع القضية" : "Choisissez un type d’affaire";
    }
    setErrors(next);
    if (next.client || next.type) return;

    setLoading(true);
    const minWait = new Promise((r) => setTimeout(r, 700));
    try {
      const [created] = await Promise.all([
        api.createCase({
          client_name: clientName.trim(),
          case_type: caseType,
          status,
          responsible_id: responsibleId || undefined,
          first_hearing_at: firstHearing || undefined,
        }),
        minWait,
      ]);
      setLoading(false);
      handleClose();
      setToast(
        ar
          ? `تم إنشاء الملف ${created.reference}`
          : `Dossier ${created.reference} créé`,
      );
      setToastShow(true);
      window.setTimeout(() => setToastShow(false), 2800);
      onCreated?.(created.reference, created.id);
      window.setTimeout(() => router.push(`/cases/${created.id}`), 400);
    } catch (e) {
      setLoading(false);
      setErrors({
        form: e instanceof ApiError ? e.message : ar ? "تعذر الإنشاء" : "Création impossible",
      });
    }
  }

  const options =
    lawyers.length > 0
      ? lawyers
      : user
        ? [
            {
              id: user.id,
              full_name: user.full_name,
              email: user.email,
              role: user.role,
              is_active: true,
              is_verified: true,
            } as TeamMember,
          ]
        : [];

  return (
    <>
      <div
        ref={overlayRef}
        className={`modal-overlay${open ? " open" : ""}`}
        onMouseDown={(e) => {
          if (e.target === overlayRef.current) handleClose();
        }}
      >
        <div
          ref={cardRef}
          className="modal-card"
          role="dialog"
          aria-modal="true"
          aria-labelledby="new-case-title"
          onMouseDown={(e) => e.stopPropagation()}
        >
          <div className="modal-head">
            <div>
              <div className="icon-new">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 7h-3l-2-2H9L7 7H4a1 1 0 0 0-1 1v11a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1V8a1 1 0 0 0-1-1z" />
                </svg>
              </div>
            </div>
            <button type="button" className="modal-close" onClick={handleClose} aria-label="Fermer">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
          <h3 id="new-case-title" className="modal-title">
            {ar ? "ملف جديد" : "Nouveau dossier"}
          </h3>
          <p className="modal-sub">
            {ar
              ? "يُولَّد المرجع تلقائياً. يظهر الملف فوراً في التخطيط والوثائق."
              : "La référence est générée automatiquement. Le dossier apparaît aussitôt dans Planning et Documents."}
          </p>

          <div className="form-grid" dir={ar ? "rtl" : "ltr"}>
            <div className="form-field full">
              <label>{ar ? "الموكل" : "Client"}</label>
              <input
                ref={clientRef}
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
                placeholder={ar ? "مثال: أحمد بناني" : "Ex. Ahmed Bennani"}
              />
              {errors.client && (
                <span style={{ color: "#b91c1c", fontSize: 12 }}>{errors.client}</span>
              )}
            </div>

            <div className="form-field full">
              <label>{ar ? "نوع القضية" : "Type d’affaire"}</label>
              <div className="type-pick" role="radiogroup">
                {TYPE_PILLS.map((p) => (
                  <button
                    key={p.value}
                    type="button"
                    role="radio"
                    aria-checked={caseType === p.value}
                    className={`type-pill${caseType === p.value ? " sel" : ""}`}
                    onClick={() => setCaseType(p.value)}
                  >
                    {ar ? p.labelAr : p.labelFr}
                  </button>
                ))}
              </div>
              {errors.type && (
                <span style={{ color: "#b91c1c", fontSize: 12 }}>{errors.type}</span>
              )}
            </div>

            <div className="form-field">
              <label>{ar ? "المسؤول" : "Responsable"}</label>
              <select
                value={responsibleId}
                onChange={(e) => setResponsibleId(e.target.value)}
              >
                {options.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.full_name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label>{ar ? "الحالة" : "Statut initial"}</label>
              <select value={status} onChange={(e) => setStatus(e.target.value)}>
                <option value="En cours">{ar ? "جارٍ" : "En cours"}</option>
                <option value="En attente">{ar ? "قيد الانتظار" : "En attente"}</option>
                <option value="Clôturé">{ar ? "مغلق" : "Clôturé"}</option>
              </select>
            </div>

            <div className="form-field">
              <label>{ar ? "المرجع" : "Référence"}</label>
              <input
                disabled
                value={`WV-${year}-····`}
                style={{ color: "var(--ink-soft)", background: "rgba(14,21,38,0.03)" }}
              />
              <span className="ref-hint">
                {ar ? "تُولَّد تلقائياً" : "générée automatiquement"}
              </span>
            </div>

            <div className="form-field">
              <label>{ar ? "أول جلسة (اختياري)" : "Première audience (optionnel)"}</label>
              <input
                type="date"
                value={firstHearing}
                onChange={(e) => setFirstHearing(e.target.value)}
              />
            </div>
          </div>

          {errors.form && (
            <p style={{ color: "#b91c1c", fontSize: 13, marginBottom: 8 }}>{errors.form}</p>
          )}

          <div className="modal-foot">
            <button type="button" className="btn-ghost" onClick={handleClose}>
              {ar ? "إلغاء" : "Annuler"}
            </button>
            <button
              type="button"
              className={`btn-create${loading ? " loading" : ""}`}
              disabled={loading}
              onClick={() => void handleCreate()}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              {ar ? "إنشاء الملف" : "Créer le dossier"}
            </button>
          </div>
        </div>
      </div>

      <div className={`toast${toastShow ? " show" : ""}`} role="status" aria-live="polite">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="16" height="16">
          <polyline points="20 6 9 17 4 12" />
        </svg>
        {toast}
      </div>
    </>
  );
}
