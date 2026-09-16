"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Building2, Users, FileText, FolderOpen, TrendingUp, CreditCard } from "lucide-react";
import { AdminShell } from "@/components/layout/admin-shell";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api, type AdminCabinet, type AdminMetrics } from "@/lib/api";
import { useTranslations } from "@/store/locale";

function UsageBar({
  label,
  value,
  max,
  color,
}: {
  label: string;
  value: number;
  max: number;
  color: string;
}) {
  const pct = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0;
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium text-sanad-navy">{label}</span>
        <span className="tabular-nums text-slate-500">
          {value}
          {max > 0 ? ` / ~${max}` : ""}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${Math.max(pct, value > 0 ? 4 : 0)}%` }}
        />
      </div>
    </div>
  );
}

export default function AdminDashboardPage() {
  const t = useTranslations().adminPlatform;
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [cabinets, setCabinets] = useState<AdminCabinet[]>([]);

  useEffect(() => {
    api.getAdminMetrics().then(setMetrics).catch(() => {});
    api.getAdminCabinets().then(setCabinets).catch(() => {});
  }, []);

  if (!t) {
    return (
      <AdminShell>
        <p className="text-sm text-slate-500">…</p>
      </AdminShell>
    );
  }

  const totalCab = (metrics?.active_cabinets || 0) + (metrics?.suspended_cabinets || 0) || 1;
  const stats = metrics
    ? [
        { label: t.statActive, value: metrics.active_cabinets, icon: Building2, color: "text-green-600" },
        { label: t.statSuspended, value: metrics.suspended_cabinets, icon: Building2, color: "text-red-600" },
        { label: t.statUsers, value: metrics.total_users, icon: Users, color: "text-sanad-blue" },
        { label: t.statDocs, value: metrics.total_documents, icon: FileText, color: "text-sanad-gold" },
      ]
    : [];

  const byCity = cabinets.reduce<Record<string, number>>((acc, c) => {
    const k = c.city || "—";
    acc[k] = (acc[k] || 0) + 1;
    return acc;
  }, {});
  const cityRows = Object.entries(byCity)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);
  const cityMax = Math.max(1, ...cityRows.map(([, n]) => n));

  return (
    <AdminShell>
      <div className="space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-sanad-slate">{t.pageTitle}</h1>
            <p className="mt-1 text-sm text-slate-500">{t.pageSubtitle}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/admin/plans">
              <Button variant="outline" size="sm" className="gap-1.5">
                <CreditCard className="h-3.5 w-3.5" />
                {t.btnPlans}
              </Button>
            </Link>
            <Link href="/admin/cabinets">
              <Button size="sm" className="gap-1.5">
                <Building2 className="h-3.5 w-3.5" />
                {t.btnCabinets}
              </Button>
            </Link>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((s) => (
            <Card key={s.label}>
              <CardContent className="flex items-center gap-4 p-6">
                <div className={`rounded-lg bg-sanad-light p-3 ${s.color}`}>
                  <s.icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-sanad-slate">{s.value}</p>
                  <p className="text-sm text-slate-500">{s.label}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardContent className="space-y-5 p-6">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-sanad-gold" />
                <h2 className="font-semibold text-sanad-slate">{t.pageSubtitle}</h2>
              </div>
              {metrics ? (
                <div className="space-y-4">
                  <UsageBar
                    label={t.statActive}
                    value={metrics.active_cabinets}
                    max={totalCab}
                    color="bg-emerald-500"
                  />
                  <UsageBar
                    label={t.statUsers}
                    value={metrics.total_users}
                    max={Math.max(metrics.total_users, 10)}
                    color="bg-sky-500"
                  />
                  <UsageBar
                    label={t.statDocs}
                    value={metrics.total_documents}
                    max={Math.max(metrics.total_documents, 20)}
                    color="bg-amber-500"
                  />
                  <UsageBar
                    label={t.cases}
                    value={cabinets.reduce((s, c) => s + (c.case_count || 0), 0)}
                    max={Math.max(
                      cabinets.reduce((s, c) => s + (c.case_count || 0), 0),
                      10,
                    )}
                    color="bg-indigo-500"
                  />
                </div>
              ) : (
                <p className="text-sm text-slate-500">Chargement…</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-5 p-6">
              <h2 className="font-semibold text-sanad-slate">Répartition par ville</h2>
              {cityRows.length ? (
                <div className="space-y-3">
                  {cityRows.map(([city, n]) => (
                    <UsageBar
                      key={city}
                      label={city}
                      value={n}
                      max={cityMax}
                      color="bg-[#1B3F9C]"
                    />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">{t.none}</p>
              )}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardContent className="p-0">
            <div className="border-b border-sanad-border px-6 py-4">
              <h2 className="font-semibold text-sanad-slate">{t.recentCabinets}</h2>
            </div>
            <div className="admin-table-scroll overflow-x-auto">
            <table className="w-full min-w-[560px] text-sm">
              <thead>
                <tr className="border-b border-sanad-border bg-sanad-light text-left text-slate-500">
                  <th className="px-4 py-3 font-medium sm:px-6">{t.btnCabinets}</th>
                  <th className="px-4 py-3 font-medium sm:px-6">{t.city}</th>
                  <th className="px-4 py-3 font-medium sm:px-6">{t.status}</th>
                  <th className="px-4 py-3 font-medium sm:px-6">{t.users}</th>
                  <th className="px-4 py-3 font-medium sm:px-6">{t.cases}</th>
                </tr>
              </thead>
              <tbody>
                {cabinets.slice(0, 8).map((c) => (
                  <tr key={c.id} className="border-b border-sanad-border">
                    <td className="px-4 py-4 font-medium sm:px-6">{c.name}</td>
                    <td className="px-4 py-4 text-slate-600 sm:px-6">{c.city}</td>
                    <td className="px-4 py-4 sm:px-6">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          c.status === "active"
                            ? "bg-green-100 text-green-700"
                            : c.status === "pending"
                              ? "bg-amber-100 text-amber-800"
                              : "bg-red-100 text-red-700"
                        }`}
                      >
                        {c.status === "active"
                          ? t.statusActive
                          : c.status === "pending"
                            ? t.statusPending
                            : t.statusSuspended}
                      </span>
                    </td>
                    <td className="px-4 py-4 sm:px-6">{c.user_count}</td>
                    <td className="px-4 py-4 sm:px-6">
                      <span className="inline-flex items-center gap-1">
                        <FolderOpen className="h-3.5 w-3.5 text-slate-400" />
                        {c.case_count}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
            <div className="px-6 py-4">
              <Link href="/admin/cabinets">
                <Button variant="outline" size="sm">
                  {t.manageAll}
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </AdminShell>
  );
}
