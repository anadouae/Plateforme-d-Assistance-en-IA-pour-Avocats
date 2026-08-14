"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/app-shell";
import { NewCaseModal } from "@/components/cases/new-case-modal";
import { api, type CaseListItem } from "@/lib/api";
import { useLocaleStore, useTranslations } from "@/store/locale";
import { caseDomainLabel, caseStatusLabel } from "@/lib/i18n/labels";

export default function CasesPage() {
  const t = useTranslations().app.cases;
  const locale = useLocaleStore((s) => s.locale);
  const ar = locale === "ar";
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const [modalOpen, setModalOpen] = useState(false);
  const btnNewRef = useRef<HTMLButtonElement>(null);
  const ghostRef = useRef<HTMLButtonElement>(null);
  const lastTrigger = useRef<HTMLElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .getCases()
      .then((data) => {
        if (!cancelled) setCases(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setCases([]);
          setLoadError(err instanceof Error ? err.message : t.loadError);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [reloadKey, t.loadError]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim();
    let list = cases;
    if (q) {
      list = list.filter(
        (c) =>
          c.reference.toLowerCase().includes(q) ||
          c.client_name.toLowerCase().includes(q) ||
          c.case_type.toLowerCase().includes(q) ||
          c.responsible_name.toLowerCase().includes(q),
      );
    }
    return [...list].sort(
      (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
    );
  }, [cases, search]);

  function openModal(from: HTMLElement | null) {
    lastTrigger.current = from;
    setModalOpen(true);
  }

  return (
    <AppShell>
      <div className="section-title">{t.title}</div>
      <div className="section-sub">
        {ar
          ? "كل ملفات المكتب، متزامنة مع التخطيط والوثائق."
          : "Toutes les affaires du cabinet, synchronisées avec le planning et les documents."}
      </div>

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
          onClick={() => openModal(btnNewRef.current)}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          {t.newCase}
        </button>
      </div>

      {loadError && !loading && (
        <div className="card" style={{ color: "#b91c1c" }}>
          {loadError}
          <button type="button" className="chip-btn" style={{ marginTop: 10 }} onClick={() => setReloadKey((k) => k + 1)}>
            {t.retry}
          </button>
        </div>
      )}

      <div className="dossier-grid">
        {loading ? (
          <p className="section-sub">{t.loading}</p>
        ) : (
          <>
            {filtered.map((c) => (
              <Link key={c.id} href={`/cases/${c.id}`} className="card dossier-card">
                <div className="dossier-head">
                  <span className="dossier-ref">{c.reference}</span>
                  <span
                    className={`status-pill${c.status === "Clôturé" ? " status-pill--closed" : ""}`}
                  >
                    {caseStatusLabel(c.status, locale)}
                  </span>
                </div>
                <div className="dossier-client">{c.client_name}</div>
                <div className="dossier-meta">
                  <span>{caseDomainLabel(c.case_type, locale)}</span>
                  <span>·</span>
                  <span>
                    {new Date(c.updated_at).toLocaleDateString(ar ? "ar-MA" : "fr-FR")}
                  </span>
                </div>
                <div className="avatar-stack">
                  <div className="av" title={c.responsible_name} />
                </div>
              </Link>
            ))}
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
      />
    </AppShell>
  );
}
