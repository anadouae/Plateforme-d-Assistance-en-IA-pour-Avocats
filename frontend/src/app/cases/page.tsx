"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/app-shell";
import { NewCaseModal } from "@/components/cases/new-case-modal";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { api, type CaseListItem } from "@/lib/api";
import { inDateRange } from "@/lib/date-range";
import { useLocaleStore, useTranslations } from "@/store/locale";
import {
  caseDomainLabel,
  caseStatusLabel,
  caseStatusOptions,
  normalizeCaseStatus,
} from "@/lib/i18n/labels";
import { filterDomainValues, normalizeCaseDomain } from "@/lib/case-domains";
import { isAssistant } from "@/lib/roles";
import { canDeleteCase } from "@/lib/ownership";
import { useAuthStore } from "@/store/auth";
import { caseDisplayTitle } from "@/lib/case-display";

const PIN_TAG = "pinned";

function initials(name: string) {
  return (name || "?")
    .split(/\s+/)
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

function isPinned(c: CaseListItem) {
  return (c.tags || []).includes(PIN_TAG);
}

export default function CasesPage() {
  const t = useTranslations().app.cases;
  const locale = useLocaleStore((s) => s.locale);
  const ar = locale === "ar";
  const confirm = useConfirm();
  const user = useAuthStore((s) => s.user);
  const assistant = isAssistant(user?.role);
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [search, setSearch] = useState("");
  const [domain, setDomain] = useState("");
  const [status, setStatus] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const btnNewRef = useRef<HTMLButtonElement>(null);
  const ghostRef = useRef<HTMLButtonElement>(null);
  const lastTrigger = useRef<HTMLElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError("");
    const watchdog = window.setTimeout(() => {
      if (!cancelled) {
        setLoading(false);
        setLoadError(
          ar
            ? "التحميل يستغرق وقتاً طويلاً. تحققوا من الشبكة ثم أعيدوا المحاولة."
            : "Le chargement met trop de temps. Vérifiez la connexion puis réessayez.",
        );
      }
    }, 18000);
    api
      .getCases()
      .then((data) => {
        if (!cancelled) {
          setCases(data);
          setLoadError("");
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setCases([]);
          setLoadError(err instanceof Error ? err.message : t.loadError);
        }
      })
      .finally(() => {
        window.clearTimeout(watchdog);
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
      window.clearTimeout(watchdog);
    };
  }, [reloadKey, ar, t.loadError]);

  const domainOptions = useMemo(() => {
    const values = filterDomainValues(cases.map((c) => c.case_type));
    return values.map((value) => ({ value, label: caseDomainLabel(value, locale) }));
  }, [cases, locale]);

  const statusOptions = useMemo(() => caseStatusOptions(locale), [locale]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim();
    let list = cases;
    if (domain) {
      list = list.filter((c) => normalizeCaseDomain(c.case_type) === domain);
    }
    if (status) {
      list = list.filter((c) => normalizeCaseStatus(c.status) === status);
    }
    if (dateFrom || dateTo) {
      list = list.filter((c) => inDateRange(c.updated_at, dateFrom, dateTo));
    }
    if (q) {
      list = list.filter(
        (c) =>
          c.reference.toLowerCase().includes(q) ||
          c.client_name.toLowerCase().includes(q) ||
          (c.title || "").toLowerCase().includes(q) ||
          c.case_type.toLowerCase().includes(q) ||
          caseDomainLabel(c.case_type, locale).toLowerCase().includes(q) ||
          caseStatusLabel(c.status, locale).toLowerCase().includes(q) ||
          c.responsible_name.toLowerCase().includes(q),
      );
    }
    return [...list].sort((a, b) => {
      const pinDiff = Number(isPinned(b)) - Number(isPinned(a));
      if (pinDiff !== 0) return pinDiff;
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
    });
  }, [cases, search, domain, status, dateFrom, dateTo, locale]);

  function openModal(from: HTMLElement | null) {
    lastTrigger.current = from;
    setModalOpen(true);
  }

  async function togglePin(c: CaseListItem, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    const tags = [...(c.tags || [])].filter((x) => x && x !== PIN_TAG);
    const next = isPinned(c) ? tags : [...tags, PIN_TAG];
    setBusyId(c.id);
    try {
      const updated = await api.updateCase(c.id, { tags: next });
      setCases((prev) => prev.map((x) => (x.id === c.id ? { ...x, ...updated, tags: updated.tags } : x)));
    } catch {
      await confirm({
        title: ar ? "تعذّر التثبيت." : "Impossible d’épingler.",
        tone: "default",
        confirmLabel: ar ? "حسناً" : "OK",
      });
    } finally {
      setBusyId(null);
    }
  }

  async function archiveCase(c: CaseListItem, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    const nextStatus = normalizeCaseStatus(c.status) === "Clôturé" ? "En cours" : "Clôturé";
    const ok = await confirm({
      title:
        nextStatus === "Clôturé"
          ? ar
            ? "أرشفة هذا الملف؟"
            : "Archiver ce dossier ?"
          : ar
            ? "إعادة فتح هذا الملف؟"
            : "Rouvrir ce dossier ?",
      description:
        nextStatus === "Clôturé"
          ? ar
            ? "سيتم وضع الملف في حالة «مغلق»."
            : "Le dossier passera en statut « Clôturé »."
          : ar
            ? "سيعود الملف إلى حالة «جارٍ»."
            : "Le dossier repassera en « En cours ».",
      tone: "default",
      confirmLabel: nextStatus === "Clôturé" ? (ar ? "أرشفة" : "Archiver") : ar ? "إعادة فتح" : "Rouvrir",
    });
    if (!ok) return;
    setBusyId(c.id);
    try {
      const updated = await api.updateCase(c.id, { status: nextStatus });
      setCases((prev) => prev.map((x) => (x.id === c.id ? { ...x, ...updated } : x)));
    } catch {
      await confirm({
        title: ar ? "تعذّر الأرشفة." : "Archivage impossible.",
        confirmLabel: ar ? "حسناً" : "OK",
      });
    } finally {
      setBusyId(null);
    }
  }

  async function removeCase(c: CaseListItem, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (!canDeleteCase({ role: user?.role, userId: user?.id, responsibleId: c.responsible_id })) {
      await confirm({
        title: ar ? "الحذف غير متاح" : "Suppression non autorisée",
        description: ar
          ? "وحده المحامي المسؤول عن هذا الملف يمكنه حذفه."
          : "Seul l’avocat responsable de ce dossier peut le supprimer.",
        confirmLabel: ar ? "حسناً" : "OK",
        cancelLabel: ar ? "إغلاق" : "Fermer",
      });
      return;
    }
    const docs = await api.getDocuments(c.id).catch(() => []);
    const docNames = docs.map((d) => d.original_name).filter(Boolean);
    const shown = docNames.slice(0, 4);
    const extraDocs = Math.max(0, docNames.length - shown.length);
    const ok = await confirm({
      title: ar ? "حذف الملف نهائياً" : "Supprimer le dossier",
      description: ar
        ? `سيتم حذف ${c.reference} دون إمكانية استرجاع.`
        : `Le dossier ${c.reference} sera définitivement supprimé.`,
      preview: (
        <div>
          <div className="sanad-confirm-preview__ref">{c.reference}</div>
          <div className="sanad-confirm-preview__row">
            <span>
              {ar ? "الزبون" : "Client"} : <strong>{c.client_name || "—"}</strong>
              {c.title ? (
                <>
                  <br />
                  {ar ? "العنوان" : "Intitulé"} : <strong>{c.title}</strong>
                </>
              ) : null}
            </span>
          </div>
          <div className="sanad-confirm-preview__meta">
            <span className="sanad-confirm-preview__chip">
              {caseDomainLabel(c.case_type, locale)}
            </span>
            <span className="sanad-confirm-preview__chip">
              {caseStatusLabel(c.status, locale)}
            </span>
          </div>
          {c.responsible_name ? (
            <div className="sanad-confirm-preview__row">
              <span>
                {ar ? "المسؤول" : "Responsable"} : <strong>{c.responsible_name}</strong>
              </span>
            </div>
          ) : null}
          <div className="sanad-confirm-preview__row" style={{ marginTop: 8 }}>
            <span>
              {ar ? "الوثائق" : "Documents"} :{" "}
              <strong>
                {docNames.length}
              </strong>
            </span>
          </div>
          {shown.length > 0 ? (
            <ul className="sanad-confirm-preview__docs">
              {shown.map((name, i) => (
                <li key={`${i}-${name}`}>{name}</li>
              ))}
              {extraDocs > 0 ? (
                <li>{ar ? `و ${extraDocs} أخرى…` : `et ${extraDocs} autre${extraDocs > 1 ? "s" : ""}…`}</li>
              ) : null}
            </ul>
          ) : null}
          <p className="sanad-confirm-preview__warn">
            {ar
              ? "ستُحذف نهائياً الوثائق والمهام والتخطيط والمرافعات المرتبطة بهذا الملف."
              : "Les documents, tâches, agenda et plaidoiries liés seront définitivement supprimés."}
          </p>
        </div>
      ),
      tone: "danger",
      requireDeletePhrase: true,
      deleteVisual: "folder",
    });
    if (!ok) return;
    setBusyId(c.id);
    try {
      await api.deleteCase(c.id);
      setCases((prev) => prev.filter((x) => x.id !== c.id));
    } catch (err) {
      await confirm({
        title: ar ? "تعذّر الحذف." : "Suppression impossible.",
        description:
          err instanceof Error && err.message
            ? err.message
            : assistant
              ? ar
                ? "دور المساعد لا يسمح بحذف الملفات."
                : "Le rôle assistant ne permet pas de supprimer un dossier."
              : ar
                ? "تحققوا من الصلاحيات أو أعيدوا المحاولة."
                : "Vérifiez vos droits ou réessayez.",
        confirmLabel: ar ? "حسناً" : "OK",
        cancelLabel: ar ? "إغلاق" : "Fermer",
      });
    } finally {
      setBusyId(null);
    }
  }

  const filterFieldStyle: React.CSSProperties = {
    border: "1px solid rgba(76,124,255,0.22)",
    borderRadius: 12,
    padding: "11px 14px",
    fontSize: 14,
    background: "var(--parchment)",
    color: "var(--ink)",
  };

  return (
    <AppShell>
      <div className="section-title">{t.title}</div>
      <div className="section-sub">{t.subtitle}</div>

      <div className="dossiers-top">
        <div className="search-fluid">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8a8f9e" strokeWidth="2">
            <circle cx="11" cy="11" r="7" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            placeholder={t.search}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <button
          ref={btnNewRef}
          type="button"
          className="btn-new"
          data-tour="new-case"
          onClick={() => openModal(btnNewRef.current)}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          {t.newCase}
        </button>
      </div>

      <div
        className="cases-filters card"
        style={{
          marginBottom: 20,
          padding: "16px 18px",
          border: "1px solid rgba(76,124,255,0.16)",
          background: "var(--card)",
          display: "grid",
          gap: 14,
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        }}
      >
        <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>{t.filterDomain}</span>
          <select
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            aria-label={t.filterDomain}
            style={filterFieldStyle}
          >
            <option value="">{t.allDomains}</option>
            {domainOptions.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>{t.filterStatus}</span>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            aria-label={t.filterStatus}
            style={filterFieldStyle}
          >
            <option value="">{t.allStatuses}</option>
            {statusOptions.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>
            {ar ? "من تاريخ" : "Du"}
          </span>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            style={filterFieldStyle}
            aria-label={ar ? "من تاريخ" : "Date de début"}
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>
            {ar ? "إلى تاريخ" : "Au"}
          </span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            style={filterFieldStyle}
            aria-label={ar ? "إلى تاريخ" : "Date de fin"}
          />
        </label>
      </div>

      {loadError && !loading && (
        <div className="card" style={{ color: "#b91c1c" }}>
          {loadError}
          <button type="button" className="chip-btn primary" style={{ marginTop: 10 }} onClick={() => setReloadKey((k) => k + 1)}>
            {t.retry}
          </button>
        </div>
      )}

      <div className="dossier-grid">
        {loading ? (
          <p className="section-sub">{t.loading}</p>
        ) : (
          <>
            {filtered.length === 0 && (
              <p className="section-sub" style={{ gridColumn: "1 / -1" }}>
                {t.empty}
              </p>
            )}
            {filtered.map((c) => {
              const closed = normalizeCaseStatus(c.status) === "Clôturé";
              const pinned = isPinned(c);
              const busy = busyId === c.id;
              return (
                <div key={c.id} className={`card dossier-card${pinned ? " is-pinned" : ""}`}>
                  <Link href={`/cases/${c.id}`} className="dossier-card-link">
                    <div className="dossier-head">
                      <span className="dossier-ref">{c.reference}</span>
                      <span className={`status-pill${closed ? " status-pill--closed" : ""}`}>
                        {caseStatusLabel(c.status, locale)}
                      </span>
                    </div>
                    <div className="dossier-client">{caseDisplayTitle(c)}</div>
                    {c.title && c.client_name && c.title.trim() !== c.client_name.trim() ? (
                      <div className="dossier-meta" style={{ marginTop: 2 }}>
                        <span>{ar ? "الموكل" : "Client"} : {c.client_name}</span>
                      </div>
                    ) : null}
                    <div className="dossier-meta">
                      <span>{caseDomainLabel(c.case_type, locale)}</span>
                      <span>·</span>
                      <span>{new Date(c.updated_at).toLocaleDateString(ar ? "ar-MA" : "fr-FR")}</span>
                    </div>
                    {c.responsible_name ? (
                      <div className="avatar-stack" title={c.responsible_name}>
                        <div className="av av--initials">{initials(c.responsible_name)}</div>
                        <span className="av-name">{c.responsible_name}</span>
                      </div>
                    ) : null}
                  </Link>
                  <div
                    className="dossier-actions"
                    onClick={(e) => e.stopPropagation()}
                    style={{
                      display: "flex",
                      flexWrap: "wrap",
                      gap: 8,
                      marginTop: 10,
                      paddingTop: 10,
                      borderTop: "1px solid rgba(76,124,255,0.12)",
                    }}
                  >
                    <button
                      type="button"
                      className="chip-btn"
                      disabled={busy}
                      onClick={(e) => void togglePin(c, e)}
                      style={{
                        padding: "8px 12px",
                        borderRadius: 10,
                        border: "1px solid rgba(76,124,255,0.28)",
                        background: pinned ? "rgba(76,124,255,0.14)" : "#fff",
                        color: "var(--royal-800)",
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                    >
                      {pinned ? (ar ? "مثبّت" : "Épinglé") : ar ? "تثبيت" : "Épingler"}
                    </button>
                    <button
                      type="button"
                      className="chip-btn"
                      disabled={busy}
                      onClick={(e) => void archiveCase(c, e)}
                      style={{
                        padding: "8px 12px",
                        borderRadius: 10,
                        border: "1px solid rgba(76,124,255,0.28)",
                        background: "#fff",
                        color: "var(--royal-800)",
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                    >
                      {closed ? (ar ? "إعادة فتح" : "Rouvrir") : ar ? "أرشفة" : "Archiver"}
                    </button>
                    {canDeleteCase({
                      role: user?.role,
                      userId: user?.id,
                      responsibleId: c.responsible_id,
                    }) ? (
                    <button
                      type="button"
                      className="chip-btn chip-btn--danger"
                      disabled={busy}
                      onClick={(e) => void removeCase(c, e)}
                      style={{
                        padding: "8px 12px",
                        borderRadius: 10,
                        border: "1px solid rgba(185,28,28,0.35)",
                        background: "rgba(185,28,28,0.06)",
                        color: "#b91c1c",
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                    >
                      {ar ? "حذف" : "Supprimer"}
                    </button>
                    ) : null}
                  </div>
                </div>
              );
            })}
            <button
              ref={ghostRef}
              type="button"
              className="dossier-card ghost card"
              onClick={() => openModal(ghostRef.current)}
            >
              <div className="plus-circle">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
              </div>
              <span style={{ fontSize: 13, fontWeight: 600 }}>
                {ar ? "إضافة ملف" : "Ajouter un dossier"}
              </span>
            </button>
          </>
        )}
      </div>

      <NewCaseModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={() => setReloadKey((k) => k + 1)}
        returnFocusRef={lastTrigger}
        existingTypes={cases.map((c) => c.case_type)}
      />
    </AppShell>
  );
}
