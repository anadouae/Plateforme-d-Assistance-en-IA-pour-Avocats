"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Briefcase, CalendarDays, FileText, Mic, Plus } from "lucide-react";
import { StatusPill } from "@/components/ui/status-pill";
import {
  api,
  type AgendaEventItem,
  type CaseListItem,
  type DocumentItem,
} from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useLocaleStore, useTranslations } from "@/store/locale";
import { caseDomainLabel, caseStatusLabel } from "@/lib/i18n/labels";
import { cn } from "@/lib/utils";

/** Contenu tableau de bord — réutilisé sur /home et /dashboard. */
export function DashboardOverview() {
  const user = useAuthStore((s) => s.user);
  const locale = useLocaleStore((s) => s.locale);
  const ar = locale === "ar";
  const t = useTranslations().app.dashboard;
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [events, setEvents] = useState<AgendaEventItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [c, d, e] = await Promise.all([
          api.getCases().catch(() => [] as CaseListItem[]),
          api.getDocuments().catch(() => [] as DocumentItem[]),
          api.getAgenda().catch(() => [] as AgendaEventItem[]),
        ]);
        if (cancelled) return;
        setCases(c);
        setDocs(d);
        const now = Date.now();
        setEvents(
          e
            .filter((ev) => new Date(ev.starts_at).getTime() >= now - 3600_000)
            .sort(
              (a, b) =>
                new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime(),
            )
            .slice(0, 5),
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const activeCases = cases.filter((c) => (c.status || "").toLowerCase() !== "closed");
  const recent = [...cases]
    .sort(
      (a, b) =>
        new Date(b.updated_at || 0).getTime() - new Date(a.updated_at || 0).getTime(),
    )
    .slice(0, 5);

  const stats = [
    {
      label: t.activeCases,
      value: loading ? "…" : String(activeCases.length),
      href: "/cases",
      icon: Briefcase,
    },
    {
      label: t.documents,
      value: loading ? "…" : String(docs.length),
      href: "/documents",
      icon: FileText,
    },
    {
      label: t.upcomingEvents || t.aiQuestions,
      value: loading ? "…" : String(events.length),
      href: "/agenda",
      icon: CalendarDays,
    },
  ];

  const actions = [
    {
      href: "/cases/new",
      icon: Plus,
      title: t.newCase,
      desc: t.actionCasesDesc,
    },
    {
      href: "/redaction/new",
      icon: Mic,
      title: t.newPlea,
      desc: t.actionPleaDesc,
    },
    {
      href: "/documents",
      icon: FileText,
      title: t.manageDocs,
      desc: t.actionDocsDesc,
    },
  ];

  return (
    <div dir={ar ? "rtl" : "ltr"} className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="section-title">{t.title}</div>
          <div className="section-sub">
            {t.welcome}
            {user?.full_name ? `, ${user.full_name}` : ""}
          </div>
        </div>
        <Link href="/cases/new" className="btn btn-primary inline-flex items-center gap-2">
          <Plus className="h-4 w-4" />
          {t.newCase}
        </Link>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        {stats.map((s) => {
          const Icon = s.icon;
          return (
            <Link
              key={s.href}
              href={s.href}
              className="card flex items-center gap-4 p-5 transition hover:border-[var(--gold)]/40"
            >
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--navy)] text-[var(--gold)]">
                <Icon className="h-5 w-5" />
              </span>
              <div>
                <div className="text-2xl font-semibold text-[var(--ink)]">{s.value}</div>
                <div className="text-xs text-[var(--ink-soft)]">{s.label}</div>
              </div>
            </Link>
          );
        })}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-serif text-lg font-semibold text-[var(--ink)]">
              {t.recentCases}
            </h2>
            <Link href="/cases" className="text-xs font-medium text-[var(--gold-deep)]">
              {t.seeAll}
            </Link>
          </div>
          {loading ? (
            <p className="text-sm text-[var(--ink-soft)]">…</p>
          ) : recent.length === 0 ? (
            <p className="text-sm text-[var(--ink-soft)]">{t.emptyCases}</p>
          ) : (
            <ul className="space-y-2">
              {recent.map((c) => (
                <li key={c.id}>
                  <Link
                    href={`/cases/${c.id}`}
                    className={cn(
                      "flex items-center justify-between gap-3 rounded-xl px-3 py-2.5",
                      "hover:bg-[var(--navy)]/5",
                    )}
                  >
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-medium text-[var(--ink)]">
                        {c.client_name || c.reference}
                      </span>
                      <span className="text-xs text-[var(--ink-soft)]">
                        {c.reference}
                        {c.case_type ? ` · ${caseDomainLabel(c.case_type, locale)}` : ""}
                      </span>
                    </span>
                    {c.status ? (
                      <StatusPill>{caseStatusLabel(c.status, locale)}</StatusPill>
                    ) : null}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-serif text-lg font-semibold text-[var(--ink)]">
              {t.upcomingEvents || t.aiQuestions}
            </h2>
            <Link href="/agenda" className="text-xs font-medium text-[var(--gold-deep)]">
              {t.seeAll}
            </Link>
          </div>
          {loading ? (
            <p className="text-sm text-[var(--ink-soft)]">…</p>
          ) : events.length === 0 ? (
            <p className="text-sm text-[var(--ink-soft)]">
              {ar ? "لا مواعيد قادمة" : "Aucun événement à venir"}
            </p>
          ) : (
            <ul className="space-y-2">
              {events.map((ev) => (
                <li
                  key={ev.id}
                  className="rounded-xl px-3 py-2.5 hover:bg-[var(--navy)]/5"
                >
                  <div className="text-sm font-medium text-[var(--ink)]">{ev.title}</div>
                  <div className="text-xs text-[var(--ink-soft)]">
                    {new Date(ev.starts_at).toLocaleString(ar ? "ar-MA" : "fr-FR", {
                      dateStyle: "medium",
                      timeStyle: "short",
                    })}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <section>
        <h2 className="mb-3 font-serif text-lg font-semibold text-[var(--ink)]">
          {t.quickAccess}
        </h2>
        <div className="grid gap-3 sm:grid-cols-3">
          {actions.map((a) => {
            const Icon = a.icon;
            return (
              <Link
                key={a.href}
                href={a.href}
                className="card flex flex-col gap-2 p-5 transition hover:-translate-y-0.5 hover:border-[var(--gold)]/40"
              >
                <Icon className="h-5 w-5 text-[var(--gold-deep)]" />
                <span className="font-medium text-[var(--ink)]">{a.title}</span>
                <span className="text-xs text-[var(--ink-soft)]">{a.desc}</span>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}
