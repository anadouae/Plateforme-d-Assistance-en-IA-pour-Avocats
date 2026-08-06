"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Filter, Plus } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { GooeyInput } from "@/components/ui/gooey-input";
import { NoiseBackground } from "@/components/ui/noise-background";
import { api, type CaseListItem } from "@/lib/api";
import { CASE_DOMAINS } from "@/lib/case-domains";
import { FadeIn } from "@/components/motion/fade-in";
import { useTranslations } from "@/store/locale";

const statusColors: Record<string, string> = {
  "En cours": "bg-sanad-gold/20 text-sanad-navy",
  Urgent: "bg-red-100 text-red-700",
  Clôturé: "bg-sanad-stone text-sanad-navy/70",
};

type SortKey = "date" | "ref" | "client";

export default function CasesPage() {
  const t = useTranslations().app.cases;
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [domainFilter, setDomainFilter] = useState("all");
  const [sortBy, setSortBy] = useState<SortKey>("date");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  const statusOptions = [
    { value: "all", label: t.allStatuses },
    { value: "En cours", label: t.statusEnCours },
    { value: "Urgent", label: t.statusUrgent },
    { value: "Clôturé", label: t.statusCloture },
  ];

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError("");
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
    let list = cases.filter(
      (c) =>
        c.reference.toLowerCase().includes(search.toLowerCase()) ||
        c.client_name.toLowerCase().includes(search.toLowerCase()) ||
        c.case_type.toLowerCase().includes(search.toLowerCase()) ||
        c.responsible_name.toLowerCase().includes(search.toLowerCase()),
    );
    if (statusFilter !== "all") {
      list = list.filter((c) => c.status === statusFilter);
    }
    if (domainFilter !== "all") {
      list = list.filter(
        (c) => c.case_type.toLowerCase() === domainFilter.toLowerCase(),
      );
    }
    return [...list].sort((a, b) => {
      if (sortBy === "ref") return a.reference.localeCompare(b.reference);
      if (sortBy === "client") return a.client_name.localeCompare(b.client_name);
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
    });
  }, [cases, search, statusFilter, domainFilter, sortBy]);

  return (
    <AppShell>
      <FadeIn className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="font-display text-2xl font-semibold text-sanad-navy">{t.title}</h1>
            <p className="mt-1 text-sm text-slate-500">{t.subtitle}</p>
          </div>
          <Link href="/cases/new">
            <NoiseBackground containerClassName="rounded-full p-[2px]">
              <Button className="rounded-full">
                <Plus className="h-4 w-4" />
                {t.newCase}
              </Button>
            </NoiseBackground>
          </Link>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
          <div className="relative min-w-[200px] max-w-md flex-1">
            <GooeyInput
              placeholder={t.search}
              value={search}
              onValueChange={setSearch}
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <div className="relative">
              <Filter className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="h-10 rounded-lg border border-sanad-border bg-white pl-9 pr-8 text-sm text-sanad-slate transition hover:border-sanad-gold/50"
                aria-label={t.filterStatus}
              >
                {statusOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <select
              value={domainFilter}
              onChange={(e) => setDomainFilter(e.target.value)}
              className="h-10 rounded-lg border border-sanad-border bg-white px-3 text-sm text-sanad-slate transition hover:border-sanad-gold/50"
              aria-label={t.filterDomain}
            >
              <option value="all">{t.allDomains}</option>
              {CASE_DOMAINS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortKey)}
              className="h-10 rounded-lg border border-sanad-border bg-white px-3 text-sm text-sanad-slate transition hover:border-sanad-gold/50"
              aria-label={t.sortBy}
            >
              <option value="date">{t.sortDate}</option>
              <option value="ref">{t.sortRef}</option>
              <option value="client">{t.sortClient}</option>
            </select>
          </div>
        </div>

        {loadError && !loading && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <p>{loadError || t.loadError}</p>
            <button
              type="button"
              className="mt-2 font-medium text-sanad-navy underline"
              onClick={() => setReloadKey((k) => k + 1)}
            >
              {t.retry}
            </button>
          </div>
        )}

        {/* Mobile cards */}
        <div className="space-y-3 md:hidden">
          {loading ? (
            <p className="py-8 text-center text-slate-400">{t.loading}</p>
          ) : filtered.length === 0 ? (
            <p className="py-8 text-center text-slate-400">
              {t.empty}{" "}
              <Link href="/cases/new" className="text-sanad-blue hover:underline">
                {t.create}
              </Link>
            </p>
          ) : (
            filtered.map((c) => (
              <Link key={c.id} href={`/cases/${c.id}`}>
                <Card tilt className="transition-all duration-300">
                  <CardContent className="space-y-2 p-4">
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-medium text-sanad-blue">{c.reference}</p>
                      <span
                        className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          statusColors[c.status] || "bg-slate-100 text-slate-600"
                        }`}
                      >
                        {c.status}
                      </span>
                    </div>
                    <p className="text-sm text-sanad-slate">{c.client_name}</p>
                    <p className="text-xs text-slate-500">
                      <span className="rounded-md bg-sanad-gold/15 px-1.5 py-0.5 font-medium text-sanad-navy">
                        {c.case_type}
                      </span>{" "}
                      · {c.responsible_name}
                    </p>
                    <p className="text-xs text-slate-400">
                      {new Date(c.updated_at).toLocaleDateString()}
                    </p>
                  </CardContent>
                </Card>
              </Link>
            ))
          )}
        </div>

        {/* Desktop table */}
        <Card className="hidden md:block">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-sanad-border bg-sanad-light text-left text-slate-500">
                    <th className="px-6 py-3 font-medium">{t.reference}</th>
                    <th className="px-6 py-3 font-medium">{t.client}</th>
                    <th className="px-6 py-3 font-medium">{t.type}</th>
                    <th className="px-6 py-3 font-medium">{t.status}</th>
                    <th className="px-6 py-3 font-medium">{t.responsible}</th>
                    <th className="px-6 py-3 font-medium">{t.lastActivity}</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-8 text-center text-slate-400">
                        {t.loading}
                      </td>
                    </tr>
                  ) : filtered.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-8 text-center text-slate-400">
                        {t.empty}{" "}
                        <Link href="/cases/new" className="text-sanad-blue hover:underline">
                          {t.create}
                        </Link>
                      </td>
                    </tr>
                  ) : (
                    filtered.map((c) => (
                      <tr
                        key={c.id}
                        className="border-b border-sanad-border transition-colors hover:bg-sanad-gold/5"
                      >
                        <td className="px-6 py-4">
                          <Link
                            href={`/cases/${c.id}`}
                            className="font-medium text-sanad-blue hover:underline"
                          >
                            {c.reference}
                          </Link>
                        </td>
                        <td className="px-6 py-4 text-sanad-slate">{c.client_name}</td>
                        <td className="px-6 py-4 text-slate-600">{c.case_type}</td>
                        <td className="px-6 py-4">
                          <span
                            className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                              statusColors[c.status] || "bg-slate-100 text-slate-600"
                            }`}
                          >
                            {c.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-slate-600">{c.responsible_name}</td>
                        <td className="px-6 py-4 text-slate-500">
                          {new Date(c.updated_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </FadeIn>
    </AppShell>
  );
}
