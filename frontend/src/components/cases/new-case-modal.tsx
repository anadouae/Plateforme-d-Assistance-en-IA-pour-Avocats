"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, type TeamMember } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useLocaleStore, useTranslations } from "@/store/locale";
import { caseDomainOptions } from "@/lib/i18n/labels";
import { customDomainsFromCases, normalizeCaseDomain } from "@/lib/case-domains";
import {
  JURISDICTION_DEGREES,
  QUALITY_OPTIONS,
  indicativeDeadlineHint,
  opposingRoleFor,
  partyRoleOptions,
  qualityHelp,
  roleHelp,
  suggestTribunal,
} from "@/lib/case-legal";
import {
  MOROCCO_CITIES,
  courtsForCity,
  courtSeatById,
} from "@/lib/morocco-courts";
import { PROCEDURE_STATUSES } from "@/lib/case-judicial";
import { FieldCoach } from "@/components/cases/field-coach";
import type { CoachKey } from "@/lib/case-field-coach";

type Props = {
  open: boolean;
  onClose: () => void;
  onCreated?: (reference: string, id: string) => void;
  returnFocusRef?: React.RefObject<HTMLElement | null>;
  existingTypes?: string[];
  /** Depuis l’atelier plaidoirie : ouvrir le dossier avec bandeau « retour atelier ». */
  fromPlea?: boolean;
};

export function NewCaseModal({
  open,
  onClose,
  onCreated,
  returnFocusRef,
  existingTypes = [],
  fromPlea = false,
}: Props) {
  const router = useRouter();
  const locale = useLocaleStore((s) => s.locale);
  const t = useTranslations().app.cases;
  const ar = locale === "ar";
  const user = useAuthStore((s) => s.user);
  const year = new Date().getFullYear();
  const overlayRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const clientRef = useRef<HTMLInputElement>(null);
  const customRef = useRef<HTMLInputElement>(null);

  const [caseTitle, setCaseTitle] = useState("");
  const [clientName, setClientName] = useState("");
  const [caseType, setCaseType] = useState("Civil");
  const [addingCustom, setAddingCustom] = useState(false);
  const [customType, setCustomType] = useState("");
  const [status, setStatus] = useState("En cours");
  const [responsibleId, setResponsibleId] = useState("");
  const [firstHearing, setFirstHearing] = useState("");
  const [jurisdictionDegree, setJurisdictionDegree] = useState("premiere_instance");
  const [courtCity, setCourtCity] = useState("casablanca");
  const [tribunal, setTribunal] = useState("casablanca-tpi");
  const [clientRole, setClientRole] = useState("demandeur");
  const [clientQuality, setClientQuality] = useState("personne_physique");
  const [clientDomicile, setClientDomicile] = useState("");
  const [opposingName, setOpposingName] = useState("");
  const [opposingQuality, setOpposingQuality] = useState("personne_physique");
  const [opposingDomicile, setOpposingDomicile] = useState("");
  const [courtFileNumber, setCourtFileNumber] = useState("");
  const [chamber, setChamber] = useState("");
  const [greffe, setGreffe] = useState("");
  const [judgeName, setJudgeName] = useState("");
  const [procedureStatus, setProcedureStatus] = useState("instruction");
  const [description, setDescription] = useState("");
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<{
    title?: string;
    client?: string;
    type?: string;
    degree?: string;
    role?: string;
    city?: string;
    tribunal?: string;
    form?: string;
  }>({});
  const [toast, setToast] = useState("");
  const [toastShow, setToastShow] = useState(false);
  const [coachField, setCoachField] = useState<CoachKey>("client");

  const [cabinetTypes, setCabinetTypes] = useState<string[]>(existingTypes);

  const domainPills = useMemo(
    () => caseDomainOptions(locale, customDomainsFromCases(cabinetTypes)),
    [locale, cabinetTypes],
  );
  const availableCourts = useMemo(
    () => courtsForCity(courtCity, jurisdictionDegree),
    [courtCity, jurisdictionDegree],
  );

  const lawyers = useMemo(
    () =>
      team.filter(
        (m) => m.is_active && (m.role === "avocat" || m.role === "admin_cabinet"),
      ),
    [team],
  );

  useEffect(() => {
    if (!open) return;
    setCaseTitle("");
    setClientName("");
    setCaseType("Civil");
    setAddingCustom(false);
    setCustomType("");
    setStatus("En cours");
    setFirstHearing("");
    setJurisdictionDegree("premiere_instance");
    setCourtCity("casablanca");
    setTribunal("casablanca-tpi");
    setClientRole("demandeur");
    setClientQuality("personne_physique");
    setClientDomicile("");
    setOpposingName("");
    setOpposingQuality("personne_physique");
    setOpposingDomicile("");
    setCourtFileNumber("");
    setChamber("");
    setGreffe("");
    setJudgeName("");
    setProcedureStatus("instruction");
    setDescription("");
    setErrors({});
    setLoading(false);
    setResponsibleId(user?.id || "");
    setCabinetTypes(existingTypes);
    api
      .getCases()
      .then((list) => setCabinetTypes(list.map((c) => c.case_type)))
      .catch(() => {});
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
    if (!caseTitle.trim() || caseTitle.trim().length < 2) {
      next.title = ar ? "عنوان الملف مطلوب" : "L’intitulé du dossier est obligatoire";
    }
    if (!clientName.trim() || clientName.trim().length < 2) {
      next.client = ar ? "اسم الموكل مطلوب" : "Le client est obligatoire";
    }
    const resolvedType = normalizeCaseDomain(addingCustom ? customType : caseType);
    if (!resolvedType || resolvedType.length < 2) {
      next.type = ar ? "اكتب نوع القضية" : "Indiquez le type de dossier";
    }
    if (!jurisdictionDegree) {
      next.degree = ar ? "درجة التقاضي مطلوبة" : "Le degré de juridiction est obligatoire";
    }
    if (!clientRole) {
      next.role = ar ? "دور الأطراف مطلوب" : "Le rôle des parties est obligatoire";
    }
    if (!courtCity) {
      next.city = ar ? "مدينة المحكمة مطلوبة" : "La ville du tribunal est obligatoire";
    }
    if (!tribunal) {
      next.tribunal = ar ? "المحكمة المختصة مطلوبة" : "Le tribunal compétent est obligatoire";
    }
    setErrors(next);
    if (next.title || next.client || next.type || next.degree || next.role || next.city || next.tribunal) return;

    setLoading(true);
    const minWait = new Promise((r) => setTimeout(r, 700));
    try {
      const [created] = await Promise.all([
        api.createCase({
          title: caseTitle.trim(),
          client_name: clientName.trim(),
          case_type: resolvedType,
          status,
          responsible_id: responsibleId || undefined,
          first_hearing_at: firstHearing || undefined,
          jurisdiction_degree: jurisdictionDegree,
          tribunal: tribunal || undefined,
          court_city: courtCity || undefined,
          client_role: clientRole,
          client_quality: clientQuality.trim() || undefined,
          client_domicile: clientDomicile.trim() || undefined,
          opposing_name: opposingName.trim() || undefined,
          opposing_role: opposingRoleFor(clientRole),
          opposing_quality: opposingQuality.trim() || undefined,
          opposing_domicile: opposingDomicile.trim() || undefined,
          court_file_number: courtFileNumber.trim() || undefined,
          chamber: chamber.trim() || undefined,
          greffe: greffe.trim() || undefined,
          judge_name: judgeName.trim() || undefined,
          procedure_status: procedureStatus || undefined,
          description: description.trim() || undefined,
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
      window.setTimeout(() => {
        const qs = fromPlea ? "?from=plea&tab=documents" : "";
        router.push(`/cases/${created.id}${qs}`);
      }, 400);
    } catch (e) {
      setLoading(false);
      setErrors({
        form: e instanceof ApiError ? e.message : ar ? "تعذر الإنشاء" : "Création impossible",
      });
    }
  }

  const roleOpts = partyRoleOptions(addingCustom ? customType : caseType);
  const rolesHint = roleHelp(!ar);
  const resolvedDomain =
    normalizeCaseDomain(addingCustom ? customType : caseType) || caseType;

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
            <button
              type="button"
              className="modal-close"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                handleClose();
              }}
              onMouseDown={(e) => e.stopPropagation()}
              aria-label={ar ? "إغلاق" : "Fermer"}
            >
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
              ? "أعطوا ملفاً عنواناً واضحاً + هوية الموكل. المرجع يُولَّد تلقائياً."
              : "Donnez un intitulé clair au dossier + identité du client. Référence automatique."}
          </p>
          <FieldCoach field={coachField} uiFr={!ar} />

          <div className="form-grid" dir={ar ? "rtl" : "ltr"}>
            <div className="form-field full">
              <label>{ar ? "عنوان الملف" : "Intitulé du dossier"}</label>
              <input
                value={caseTitle}
                onChange={(e) => {
                  setCaseTitle(e.target.value);
                  setErrors((err) => ({ ...err, title: undefined }));
                }}
                onFocus={() => setCoachField("client")}
                placeholder={
                  ar
                    ? "مثال: بناني ضد العلمي — كراء محل تجاري"
                    : "Ex. Bennani c/ Alami — loyers locaux commerciaux"
                }
                maxLength={255}
              />
              {errors.title && (
                <span style={{ color: "#b91c1c", fontSize: 12 }}>{errors.title}</span>
              )}
            </div>

            <div className="form-field full">
              <label>{ar ? "الموكل" : "Client"}</label>
              <input
                ref={clientRef}
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
                onFocus={() => setCoachField("client")}
                placeholder={ar ? "مثال: أحمد بناني" : "Ex. Ahmed Bennani"}
              />
              {errors.client && (
                <span style={{ color: "#b91c1c", fontSize: 12 }}>{errors.client}</span>
              )}
            </div>

            <div className="form-field full">
              <label>{ar ? "وصف الملف (اختياري)" : "Description du dossier (optionnel)"}</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                onFocus={() => setCoachField("description")}
                rows={4}
                maxLength={4000}
                placeholder={
                  ar
                    ? "ملخص الوقائع، الطلبات، المواعيد… يمكن إكماله لاحقاً."
                    : "Résumé des faits, demandes, échéances… modifiable ensuite sur la fiche."
                }
                style={{
                  width: "100%",
                  resize: "vertical",
                  minHeight: 88,
                  padding: "10px 12px",
                  borderRadius: 10,
                  border: "1px solid rgba(14,21,38,0.12)",
                  font: "inherit",
                  lineHeight: 1.45,
                }}
              />
              <span className="ref-hint">
                {ar
                  ? "يظهر في ملخص الملف ويساعد التحليل والهيئة."
                  : "Visible sur la fiche dossier — utile pour l’équipe et l’analyse IA."}
              </span>
            </div>

            <div className="form-field full">
              <label>{t.domain}</label>
              <div className="type-pick" role="radiogroup" onFocus={() => setCoachField("domain")}>
                {domainPills.map((p) => (
                  <button
                    key={p.value}
                    type="button"
                    role="radio"
                    aria-checked={!addingCustom && caseType === p.value}
                    className={`type-pill${!addingCustom && caseType === p.value ? " sel" : ""}`}
                    onClick={() => {
                      setAddingCustom(false);
                      setCustomType("");
                      setCaseType(p.value);
                      setTribunal(suggestTribunal(p.value, jurisdictionDegree));
                      const roles = partyRoleOptions(p.value);
                      if (!roles.some((r) => r.value === clientRole)) {
                        setClientRole(roles[0]?.value || "demandeur");
                      }
                      setErrors((e) => ({ ...e, type: undefined }));
                    }}
                  >
                    {p.label}
                  </button>
                ))}
                <button
                  type="button"
                  role="radio"
                  aria-checked={addingCustom}
                  className={`type-pill add${addingCustom ? " sel" : ""}`}
                  onClick={() => {
                    setAddingCustom(true);
                    setCaseType("");
                    window.setTimeout(() => customRef.current?.focus(), 40);
                  }}
                >
                  + {t.addDomain}
                </button>
              </div>
              {addingCustom && (
                <>
                  <input
                    ref={customRef}
                    value={customType}
                    onChange={(e) => {
                      setCustomType(e.target.value);
                      setErrors((err) => ({ ...err, type: undefined }));
                    }}
                    placeholder={t.addDomainPlaceholder}
                    maxLength={100}
                    style={{ marginTop: 10 }}
                  />
                  <span className="ref-hint">{t.addDomainHint}</span>
                </>
              )}
              {errors.type && (
                <span style={{ color: "#b91c1c", fontSize: 12 }}>{errors.type}</span>
              )}
            </div>

            <div className="form-field">
              <label>{ar ? "درجة التقاضي *" : "Degré de juridiction *"}</label>
              <select
                value={jurisdictionDegree}
                onFocus={() => setCoachField("degree")}
                onChange={(e) => {
                  const d = e.target.value;
                  setJurisdictionDegree(d);
                  const kind = suggestTribunal(resolvedDomain, d);
                  const next = courtsForCity(courtCity, d);
                  const match = next.find((c) => c.kind === kind) || next[0];
                  if (match) setTribunal(match.id);
                  setErrors((err) => ({ ...err, degree: undefined }));
                }}
              >
                {JURISDICTION_DEGREES.map((d) => (
                  <option key={d.value} value={d.value}>
                    {ar ? d.ar : d.fr}
                  </option>
                ))}
              </select>
              {errors.degree && (
                <span style={{ color: "#b91c1c", fontSize: 12 }}>{errors.degree}</span>
              )}
              <span className="ref-hint">{indicativeDeadlineHint(jurisdictionDegree, !ar)}</span>
            </div>

            <div className="form-field">
              <label>{ar ? "مدينة المحكمة *" : "Ville du tribunal *"}</label>
              <select
                value={courtCity}
                onFocus={() => setCoachField("city")}
                onChange={(e) => {
                  const city = e.target.value;
                  setCourtCity(city);
                  const kind = suggestTribunal(resolvedDomain, jurisdictionDegree);
                  const next = courtsForCity(city, jurisdictionDegree);
                  const match = next.find((c) => c.kind === kind) || next[0];
                  setTribunal(match?.id || "");
                }}
              >
                {MOROCCO_CITIES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {ar ? c.ar : c.fr}
                  </option>
                ))}
              </select>
              <span className="ref-hint">
                {ar
                  ? "المدينة تحدد المحاكم المتاحة — يمكن أن تختلف عن مقر المكتب"
                  : "La ville filtre les sièges — peut différer du siège du cabinet"}
              </span>
              {errors.city ? (
                <span style={{ color: "#b91c1c", fontSize: 12 }}>{errors.city}</span>
              ) : null}
            </div>

            <div className="form-field">
              <label>{ar ? "المحكمة المختصة *" : "Tribunal compétent *"}</label>
              <select
                value={tribunal}
                onFocus={() => setCoachField("tribunal")}
                onChange={(e) => setTribunal(e.target.value)}
                disabled={availableCourts.length === 0}
              >
                {availableCourts.length === 0 ? (
                  <option value="">
                    {ar ? "لا محكمة لهذه الدرجة في هذه المدينة" : "Aucun siège pour ce degré / ville"}
                  </option>
                ) : (
                  availableCourts.map((s) => (
                    <option key={s.id} value={s.id}>
                      {ar ? s.ar : s.fr}
                    </option>
                  ))
                )}
              </select>
              <span className="ref-hint">
                {ar
                  ? "لائحة إرشادية — تحققوا من الاختصاص المحلي"
                  : "Liste indicative — vérifiez toujours la compétence territoriale"}
                {courtSeatById(tribunal)
                  ? ` · ${ar ? courtSeatById(tribunal)!.ar : courtSeatById(tribunal)!.fr}`
                  : ""}
              </span>
            </div>

            <div className="form-field">
              <label>{ar ? "دور موكلكم *" : "Rôle de votre client *"}</label>
              <select
                value={clientRole}
                onFocus={() => setCoachField("role")}
                onChange={(e) => {
                  setClientRole(e.target.value);
                  setErrors((err) => ({ ...err, role: undefined }));
                }}
              >
                {roleOpts.map((r) => (
                  <option key={r.value} value={r.value}>
                    {ar ? r.ar : r.fr}
                  </option>
                ))}
              </select>
              {errors.role && (
                <span style={{ color: "#b91c1c", fontSize: 12 }}>{errors.role}</span>
              )}
              <span className="ref-hint">
                {rolesHint.demandeur} {rolesHint.defendeur}
              </span>
            </div>

            <div className="form-field">
              <label>{ar ? "طبيعة الموكل" : "Nature du client"}</label>
              <select
                value={clientQuality}
                onFocus={() => setCoachField("quality")}
                onChange={(e) => setClientQuality(e.target.value)}
              >
                {QUALITY_OPTIONS.map((q) => (
                  <option key={q.value} value={q.value}>
                    {ar ? q.ar : q.fr}
                  </option>
                ))}
              </select>
              <span className="ref-hint">{qualityHelp(!ar)}</span>
            </div>

            <div className="form-field full">
              <label>{ar ? "موطن / مقر الموكل" : "Domicile / siège du client"}</label>
              <input
                value={clientDomicile}
                onFocus={() => setCoachField("domicile")}
                onChange={(e) => setClientDomicile(e.target.value)}
                placeholder={ar ? "العنوان الكامل" : "Adresse complète"}
              />
            </div>

            <div className="form-field">
              <label>{ar ? "الطرف المقابل" : "Partie adverse"}</label>
              <input
                value={opposingName}
                onFocus={() => setCoachField("opposing")}
                onChange={(e) => setOpposingName(e.target.value)}
                placeholder={ar ? "الاسم الكامل" : "Nom complet"}
              />
            </div>

            <div className="form-field">
              <label>{ar ? "طبيعة الطرف المقابل" : "Nature adverse"}</label>
              <select
                value={opposingQuality}
                onFocus={() => setCoachField("opposingQuality")}
                onChange={(e) => setOpposingQuality(e.target.value)}
              >
                {QUALITY_OPTIONS.map((q) => (
                  <option key={q.value} value={q.value}>
                    {ar ? q.ar : q.fr}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-field full">
              <label>{ar ? "موطن الطرف المقابل" : "Domicile / siège adverse"}</label>
              <input
                value={opposingDomicile}
                onFocus={() => setCoachField("opposingDomicile")}
                onChange={(e) => setOpposingDomicile(e.target.value)}
                placeholder={
                  ar
                    ? "مثال: شارع الزرقطوني رقم 210، الدار البيضاء"
                    : "Ex. : rue Zerktouni 210, Casablanca"
                }
              />
            </div>

            <div className="form-field full" style={{ gridColumn: "1 / -1" }}>
              <p className="ref-hint" style={{ marginBottom: 8, fontWeight: 600 }}>
                {ar ? "الملف القضائي (اختياري عند الإنشاء)" : "Dossier judiciaire (optionnel à la création)"}
              </p>
              <p className="ref-hint" style={{ marginBottom: 10 }}>
                {ar
                  ? "رقم الرائج (RG) هو رقم الملف لدى المحكمة بعد الإيداع. الغرفة، كتابة الضبط والقاضي المقرر تُملأ عندما تُعرف — ليست لازمة لفتح الملف في LexHub."
                  : "Le n° RG est le numéro du dossier au greffe après dépôt. Chambre, greffe et juge se remplissent quand ils sont connus — pas obligatoires pour ouvrir le dossier dans LexHub."}
              </p>
            </div>

            <div className="form-field">
              <label>{ar ? "رقم الرائج / RG" : "N° RG / رقم الرائج"}</label>
              <input
                value={courtFileNumber}
                onFocus={() => setCoachField("rg")}
                onChange={(e) => setCourtFileNumber(e.target.value)}
                placeholder="2025/1547"
                dir="ltr"
              />
            </div>

            <div className="form-field">
              <label>{ar ? "الغرفة" : "Chambre"}</label>
              <input
                value={chamber}
                onFocus={() => setCoachField("chamber")}
                onChange={(e) => setChamber(e.target.value)}
                placeholder={ar ? "الغرفة التجارية الأولى" : "1ère chambre commerciale"}
              />
            </div>

            <div className="form-field">
              <label>{ar ? "كتابة الضبط / Greffe" : "Greffe"}</label>
              <input
                value={greffe}
                onFocus={() => setCoachField("greffe")}
                onChange={(e) => setGreffe(e.target.value)}
                placeholder={ar ? "قسم القضايا التجارية" : "Greffe commercial"}
              />
            </div>

            <div className="form-field">
              <label>{ar ? "القاضي المقرر" : "Juge / مقرر"}</label>
              <input
                value={judgeName}
                onFocus={() => setCoachField("judge")}
                onChange={(e) => setJudgeName(e.target.value)}
                placeholder={ar ? "ذ. كريم المنصوري" : "Ex. Me. …"}
              />
            </div>

            <div className="form-field">
              <label>{ar ? "حالة المسطرة" : "Statut procédure"}</label>
              <select
                value={procedureStatus}
                onFocus={() => setCoachField("procedure")}
                onChange={(e) => setProcedureStatus(e.target.value)}
                title={
                  ar
                    ? "مرحلة المسطرة أمام المحكمة"
                    : "Étape de la procédure devant le tribunal"
                }
              >
                {PROCEDURE_STATUSES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {ar ? s.ar : s.fr}
                  </option>
                ))}
              </select>
              <span className="ref-hint">
                {ar
                  ? "افتتاح = إيداع العريضة · تحقيق = تبادل المذكرات · جلسة · مداولة · حكم · تبليغ · استئناف · تنفيذ · مغلق."
                  : "Ouverture = dépôt · Instruction = échanges · Audience · Délibéré · Jugement · Notification · Appel · Exécution · Clos."}
              </span>
            </div>

            <div className="form-field full">
              <span className="ref-hint">
                {ar
                  ? "اسم المحامي على التصدير = ملف المكتب / المستخدم المتصل (الإعدادات)."
                  : "Avocat plaidant à l’export = profil connecté / branding cabinet (Paramètres)."}
              </span>
            </div>

            <div className="form-field">
              <label>{ar ? "المسؤول" : "Responsable"}</label>
              <select
                value={responsibleId}
                onFocus={() => setCoachField("responsible")}
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
              <select
                value={status}
                onFocus={() => setCoachField("status")}
                onChange={(e) => setStatus(e.target.value)}
              >
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
                onFocus={() => setCoachField("hearing")}
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
