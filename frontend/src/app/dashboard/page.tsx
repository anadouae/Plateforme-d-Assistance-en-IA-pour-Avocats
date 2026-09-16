"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Briefcase,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  FileText,
  Mic,
  Plus,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { StatusPill } from "@/components/ui/status-pill";
import {
  api,
  type AgendaEventItem,
  type CaseListItem,
  type DocumentItem,
  type PlaidoirieDraftItem,
} from "@/lib/api";
import { isAssistant } from "@/lib/roles";
import { useAuthStore } from "@/store/auth";
import { useLocaleStore, useTranslations } from "@/store/locale";
import { caseStatusLabel } from "@/lib/i18n/labels";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const locale = useLocaleStore((s) => s.locale);
  const ar = locale === "ar";
  const t = useTranslations().app.dashboard;
  const assistant = isAssistant(user?.role);

  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [events, setEvents] = useState<AgendaEventItem[]>([]);
  const [drafts, setDrafts] = useState<PlaidoirieDraftItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [c, d, e, p] = await Promise.all([
          api.getCases().catch(() => [] as CaseListItem[]),
          api.getDocuments().catch(() => [] as DocumentItem[]),
          api.getAgenda().catch(() => [] as AgendaEventItem[]),
          api.listPlaidoirieDrafts().catch(() => [] as PlaidoirieDraftItem[]),
        ]);
        if (cancelled) return;
        setCases(c);
        setDocs(d);
        setDrafts(p);
        const now = Date.now();
        setEvents(
          e
            .filter((ev) => new Date(ev.starts_at).getTime() >= now - 3600_000)
            .sort(
              (a, b) =>
                new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime(),
            ),
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const assignedDrafts = useMemo(() => {
    if (!user?.id) return [];
    return drafts.filter((d) => d.assigned_to_user_id === user.id);
  }, [drafts, user?.id]);

  const validatedDrafts = useMemo(
    () => drafts.filter((d) => d.status === "validated"),
    [drafts],
  );

  const events48h = useMemo(() => {
    const now = Date.now();
    const until = now + 48 * 3600_000;
    return events.filter((ev) => {
      const t0 = new Date(ev.starts_at).getTime();
      return t0 >= now - 3600_000 && t0 <= until;
    });
  }, [events]);

  const activeCases = cases.filter((c) => (c.status || "").toLowerCase() !== "closed");
  const recent = [...cases]
    .sort(
      (a, b) =>
        new Date(b.updated_at || 0).getTime() - new Date(a.updated_at || 0).getTime(),
    )
    .slice(0, 5);

  if (assistant) {
    const assistStats = [
      {
        label: ar ? "مرافعات مُسندة إليّ" : "Plaidoiries assignées à moi",
        value: loading ? "…" : String(assignedDrafts.length),
        href: "/redaction",
        icon: ClipboardList,
      },
      {
        label: ar ? "مرافعات مُصادق عليها" : "Plaidoiries validées disponibles",
        value: loading ? "…" : String(validatedDrafts.length),
        href: "/redaction",
        icon: CheckCircle2,
      },
      {
        label: ar ? "أحداث خلال 48س" : "Événements à venir (48h)",
        value: loading ? "…" : String(events48h.length),
        href: "/agenda",
        icon: CalendarDays,
      },
    ];

    const assistActions = [
      {
        href: "/redaction",
        icon: CheckCircle2,
        title: ar ? "فتح المرافعات المُصادق عليها" : "Ouvrir plaidoiries validées",
        desc: ar
          ? "اطّلعوا واطبعوا وحملوا المرافعات الجاهزة"
          : "Consulter, imprimer et télécharger les plaidoiries prêtes",
      },
      {
        href: "/agenda",
        icon: CalendarDays,
        title: ar ? "التخطيط" : "Planning",
        desc: t.actionAgendaDesc,
      },
      {
        href: "/documents",
        icon: FileText,
        title: ar ? "الوثائق" : "Documents",
        desc: t.actionDocsAssistDesc || t.actionDocsDesc,
      },
    ];

    return (
      <AppShell>
        <div dir={ar ? "rtl" : "ltr"} className="mx-auto max-w-5xl space-y-6">
          <div>
            <div className="section-title">
              {ar ? "فضاء المتدرّج" : "Espace stagiaire"}
            </div>
            <div className="section-sub">
              {ar
                ? `مرحباً${user?.full_name ? `، ${user.full_name}` : ""} — مساحة عمل المساعد / المتدرّج`
                : `${t.welcome}${user?.full_name ? `, ${user.full_name}` : ""} — workspace assistant / stagiaire`}
            </div>
            <p className="mt-1 text-xs text-[var(--ink-soft)]">{t.assistantSpace}</p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {assistStats.map((s) => {
              const Icon = s.icon;
              return (
                <Link
                  key={s.label}
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
                  {ar ? "مرافعاتي المُسندة" : "Mes plaidoiries assignées"}
                </h2>
                <Link href="/redaction" className="text-xs font-medium text-[var(--gold-deep)]">
                  {t.seeAll}
                </Link>
              </div>
              {loading ? (
                <p className="text-sm text-[var(--ink-soft)]">…</p>
              ) : assignedDrafts.length === 0 ? (
                <p className="text-sm text-[var(--ink-soft)]">
                  {ar ? "لا مرافعات مُسندة حالياً" : "Aucune plaidoirie assignée pour le moment"}
                </p>
              ) : (
                <ul className="space-y-2">
                  {assignedDrafts.slice(0, 6).map((d) => (
                    <li key={d.id}>
                      <Link
                        href="/redaction"
                        className={cn(
                          "flex items-center justify-between gap-3 rounded-xl px-3 py-2.5",
                          "hover:bg-[var(--navy)]/5",
                        )}
                      >
                        <span className="min-w-0">
                          <span className="block line-clamp-2 break-words text-sm font-medium text-[var(--ink)]" dir="auto">
                            {d.title || (ar ? "مرافعة" : "Plaidoirie")}
                          </span>
                          <span className="text-xs text-[var(--ink-soft)]">
                            {d.case_reference || "—"}
                            {d.status ? ` · ${d.status}` : ""}
                          </span>
                        </span>
                        {d.status ? <StatusPill>{d.status}</StatusPill> : null}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="card p-5">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-serif text-lg font-semibold text-[var(--ink)]">
                  {ar ? "مُصادق عليها للمعالجة" : "Validées à traiter"}
                </h2>
                <Link href="/redaction" className="text-xs font-medium text-[var(--gold-deep)]">
                  {t.seeAll}
                </Link>
              </div>
              {loading ? (
                <p className="text-sm text-[var(--ink-soft)]">…</p>
              ) : validatedDrafts.length === 0 ? (
                <p className="text-sm text-[var(--ink-soft)]">
                  {ar ? "لا مرافعات مُصادق عليها" : "Aucune plaidoirie validée disponible"}
                </p>
              ) : (
                <ul className="space-y-2">
                  {validatedDrafts.slice(0, 6).map((d) => (
                    <li key={d.id}>
                      <Link
                        href="/redaction"
                        className={cn(
                          "flex items-center justify-between gap-3 rounded-xl px-3 py-2.5",
                          "hover:bg-[var(--navy)]/5",
                        )}
                      >
                        <span className="min-w-0">
                          <span className="block line-clamp-2 break-words text-sm font-medium text-[var(--ink)]" dir="auto">
                            {d.title || (ar ? "مرافعة" : "Plaidoirie")}
                          </span>
                          <span className="text-xs text-[var(--ink-soft)]">
                            {d.case_reference || "—"}
                            {d.assigned_to_name ? ` · ${d.assigned_to_name}` : ""}
                          </span>
                        </span>
                        <StatusPill>{ar ? "مُصادق" : "Validée"}</StatusPill>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <section className="card p-5">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-serif text-lg font-semibold text-[var(--ink)]">
                  {ar ? "المواعيد والجلسات القادمة" : "Prochains rendez-vous / audiences"}
                </h2>
                <Link href="/agenda" className="text-xs font-medium text-[var(--gold-deep)]">
                  {t.seeAll}
                </Link>
              </div>
              {loading ? (
                <p className="text-sm text-[var(--ink-soft)]">…</p>
              ) : events.slice(0, 5).length === 0 ? (
                <p className="text-sm text-[var(--ink-soft)]">
                  {ar ? "لا مواعيد قادمة" : "Aucun événement à venir"}
                </p>
              ) : (
                <ul className="space-y-2">
                  {events.slice(0, 5).map((ev) => (
                    <li key={ev.id} className="rounded-xl px-3 py-2.5 hover:bg-[var(--navy)]/5">
                      <div className="text-sm font-medium text-[var(--ink)]">{ev.title}</div>
                      <div className="text-xs text-[var(--ink-soft)]">
                        {new Date(ev.starts_at).toLocaleString(ar ? "ar-MA" : "fr-FR", {
                          dateStyle: "medium",
                          timeStyle: "short",
                        })}
                        {ev.case_reference ? ` · ${ev.case_reference}` : ""}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="card p-5">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-serif text-lg font-semibold text-[var(--ink)]">
                  {ar ? "ملفات المكتب" : "Dossiers du cabinet"}
                </h2>
                <Link href="/cases" className="text-xs font-medium text-[var(--gold-deep)]">
                  {t.seeAll}
                </Link>
              </div>
              {loading ? (
                <p className="text-sm text-[var(--ink-soft)]">…</p>
              ) : recent.length === 0 ? (
                <p className="text-sm text-[var(--ink-soft)]">
                  {ar ? "لا ملفات للعرض" : "Aucun dossier visible"}
                </p>
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
                          <span className="text-xs text-[var(--ink-soft)]">{c.reference}</span>
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
          </div>

          <section>
            <h2 className="mb-3 font-serif text-lg font-semibold text-[var(--ink)]">
              {t.quickAccess}
            </h2>
            <div className="grid gap-3 sm:grid-cols-3">
              {assistActions.map((a) => {
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
      </AppShell>
    );
  }

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
      value: loading ? "…" : String(events.slice(0, 5).length),
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
    <AppShell>
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
                          {c.case_type ? ` · ${c.case_type}` : ""}
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
            ) : events.slice(0, 5).length === 0 ? (
              <p className="text-sm text-[var(--ink-soft)]">
                {ar ? "لا مواعيد قادمة" : "Aucun événement à venir"}
              </p>
            ) : (
              <ul className="space-y-2">
                {events.slice(0, 5).map((ev) => (
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
    </AppShell>
  );
}
