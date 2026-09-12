"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  Building2,
  CreditCard,
  LayoutDashboard,
  Phone,
  ScrollText,
  Shield,
  Sparkles,
  X,
} from "lucide-react";
import { LanguageSwitch } from "@/components/layout/language-switch";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { UserAccountMenu } from "@/components/layout/user-account-menu";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";
import { api, ApiError } from "@/lib/api";
import {
  OpsCoachSection,
  normalizeOpsTips,
} from "@/components/admin/ops-coach-panel";

const adminNav = [
  { href: "/admin", label: "Vue d’ensemble", icon: LayoutDashboard, hint: "Indicateurs clés" },
  { href: "/admin/cabinets", label: "Cabinets", icon: Building2, hint: "Clients & accès" },
  { href: "/admin/plans", label: "Plans tarifaires", icon: CreditCard, hint: "Prix & quotas" },
  { href: "/admin/leads", label: "Demandes", icon: Phone, hint: "Entreprise & Sur mesure" },
  { href: "/admin/logs", label: "Journal", icon: ScrollText, hint: "Audit sécurité" },
];

type PlatformAnalysis = {
  summary_fr: string;
  recommendations: string[];
  growth_recommendations?: unknown[];
  generated_at?: string;
  period_days?: number;
  metrics?: {
    cabinets_actifs?: number;
    cabinets_suspendus?: number;
    utilisateurs?: number;
    dossiers?: number;
    documents?: number;
    connexions_30j?: number;
    plaidoiries_mois?: number;
    credits_ia_mois?: number;
    abonnements_par_statut?: Record<string, number>;
    par_ville?: Record<string, number>;
    credits_par_plan?: Record<string, number>;
    plaidoiries_par_plan?: Record<string, number>;
  };
};

const STATUS_FR: Record<string, string> = {
  trial: "Essai",
  active: "Actif",
  past_due: "Impayé",
  canceled: "Résilié",
  expired: "Expiré",
};

const PIE_COLORS = ["#0B1A4D", "#C9A84A", "#2563eb", "#dc2626", "#64748b", "#0d9488"];

function polar(cx: number, cy: number, r: number, angleDeg: number) {
  const a = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
}

function PieChart({
  data,
}: {
  data: { label: string; value: number; color: string }[];
}) {
  const total = data.reduce((s, d) => s + d.value, 0);
  if (!total) {
    return <p className="text-xs text-slate-500">Aucune donnée</p>;
  }
  const cx = 90;
  const cy = 90;
  const r = 72;
  let angle = 0;
  const slices = data.map((d) => {
    const sweep = (d.value / total) * 360;
    const start = angle;
    const end = angle + sweep;
    angle = end;
    const large = sweep > 180 ? 1 : 0;
    const p0 = polar(cx, cy, r, start);
    const p1 = polar(cx, cy, r, end);
    const dPath =
      sweep >= 359.9
        ? `M ${cx} ${cy - r} A ${r} ${r} 0 1 1 ${cx - 0.01} ${cy - r} Z`
        : `M ${cx} ${cy} L ${p0.x} ${p0.y} A ${r} ${r} 0 ${large} 1 ${p1.x} ${p1.y} Z`;
    return { ...d, dPath, pct: Math.round((d.value / total) * 100) };
  });

  return (
    <div className="flex flex-col items-center gap-3 sm:flex-row sm:items-start">
      <svg viewBox="0 0 180 180" className="h-40 w-40 shrink-0" role="img" aria-label="Abonnements">
        {slices.map((s) => (
          <path key={s.label} d={s.dPath} fill={s.color} className="transition-opacity hover:opacity-90">
            <title>
              {s.label}: {s.value} ({s.pct}%)
            </title>
          </path>
        ))}
        <circle cx={cx} cy={cy} r={34} fill="var(--admin-pie-hole, #fff)" />
        <text x={cx} y={cy - 4} textAnchor="middle" className="fill-sanad-navy" fontSize="16" fontWeight="700">
          {total}
        </text>
        <text x={cx} y={cy + 14} textAnchor="middle" fill="#64748b" fontSize="9">
          abo.
        </text>
      </svg>
      <ul className="w-full space-y-1.5 text-xs">
        {slices.map((s) => (
          <li key={s.label} className="flex items-center justify-between gap-2">
            <span className="flex items-center gap-2 text-slate-700">
              <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: s.color }} />
              {s.label}
            </span>
            <span className="tabular-nums font-semibold text-sanad-navy">
              {s.value} · {s.pct}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function BarChart({
  data,
  color = "#2563eb",
}: {
  data: { label: string; value: number }[];
  color?: string;
}) {
  if (!data.length) {
    return <p className="text-xs text-slate-500">Aucune donnée</p>;
  }
  const max = Math.max(...data.map((d) => d.value), 1);
  const h = 140;
  const pad = 8;
  const barW = Math.min(48, Math.floor(220 / data.length) - 8);
  const gap = 12;
  const width = data.length * (barW + gap) + pad * 2;

  return (
    <div className="w-full overflow-x-auto">
      <svg
        viewBox={`0 0 ${width} ${h + 36}`}
        className="mx-auto h-[176px] w-full max-w-md"
        role="img"
        aria-label="Répartition"
      >
        {data.map((d, i) => {
          const bh = Math.max(4, Math.round((d.value / max) * h));
          const x = pad + i * (barW + gap);
          const y = h - bh + 4;
          return (
            <g key={d.label}>
              <rect
                x={x}
                y={y}
                width={barW}
                height={bh}
                rx={6}
                fill={color}
                className="origin-bottom transition-all duration-700"
              >
                <title>
                  {d.label}: {d.value}
                </title>
              </rect>
              <text
                x={x + barW / 2}
                y={y - 6}
                textAnchor="middle"
                className="fill-sanad-navy"
                fontSize="11"
                fontWeight="700"
              >
                {d.value}
              </text>
              <text x={x + barW / 2} y={h + 22} textAnchor="middle" fill="#64748b" fontSize="10">
                {d.label.length > 10 ? `${d.label.slice(0, 9)}…` : d.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function MetricTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-sanad-stone bg-white px-3 py-2.5 text-center">
      <p className="text-lg font-bold tabular-nums text-sanad-navy">{value}</p>
      <p className="text-[11px] text-slate-500">{label}</p>
    </div>
  );
}

export function AdminShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated } = useAuthStore();
  const [analysisBusy, setAnalysisBusy] = useState(false);
  const [analysisOpen, setAnalysisOpen] = useState(false);
  const [analysis, setAnalysis] = useState<PlatformAnalysis | null>(null);
  const [analysisErr, setAnalysisErr] = useState("");

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    if (user?.role !== "admin_webvoice") {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, user, router]);

  if (!isAuthenticated() || user?.role !== "admin_webvoice") {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-slate-500">…</p>
      </div>
    );
  }

  async function runAnalysis() {
    setAnalysisBusy(true);
    setAnalysisErr("");
    setAnalysisOpen(true);
    try {
      const r = await api.runPlatformAnalysis();
      setAnalysis({
        summary_fr: r.summary_fr,
        recommendations: r.recommendations || [],
        growth_recommendations: r.growth_recommendations || [],
        generated_at: r.generated_at,
        period_days: r.period_days,
        metrics: (r.metrics || {}) as PlatformAnalysis["metrics"],
      });
    } catch (e) {
      setAnalysisErr(e instanceof ApiError ? e.message : "Erreur analyse");
    } finally {
      setAnalysisBusy(false);
    }
  }

  const m = analysis?.metrics;
  const cityEntries = Object.entries(m?.par_ville || {}).sort((a, b) => b[1] - a[1]);
  const subEntries = Object.entries(m?.abonnements_par_statut || {});
  const creditPlanEntries = Object.entries(m?.credits_par_plan || {}).sort((a, b) => b[1] - a[1]);

  const pieData = subEntries.map(([k, v], i) => ({
    label: STATUS_FR[k] || k,
    value: v,
    color: PIE_COLORS[i % PIE_COLORS.length],
  }));
  const cityBars = cityEntries.map(([label, value]) => ({ label, value }));
  const creditBars = creditPlanEntries.map(([label, value]) => ({ label, value }));

  return (
    <div className="admin-shell">
      <aside className="admin-dock" aria-label="Navigation admin">
        <Link href="/admin" className="admin-dock__brand" title="LexHub Admin">
          <Image
            src="/logo-lexhub-cube.png"
            alt="LexHub"
            width={28}
            height={28}
            className="h-7 w-7 object-contain"
          />
        </Link>

        <nav className="admin-dock__nav">
          {adminNav.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn("admin-dock__item", active && "is-active")}
              >
                <Icon className="admin-dock__icon" strokeWidth={2} />
                <span className="admin-dock__text">
                  <span className="admin-dock__label">{item.label}</span>
                  <span className="admin-dock__hint">{item.hint}</span>
                </span>
              </Link>
            );
          })}
          <button
            type="button"
            className={cn("admin-dock__item admin-dock__item--coach", analysisOpen && "is-active")}
            disabled={analysisBusy}
            onClick={() => void runAnalysis()}
          >
            <Sparkles className="admin-dock__icon" strokeWidth={2} />
            <span className="admin-dock__text">
              <span className="admin-dock__label">
                {analysisBusy ? "Chargement…" : "Coach exploitation"}
              </span>
              <span className="admin-dock__hint">Conseils & e-mails cabinets</span>
            </span>
          </button>
        </nav>
      </aside>

      <div className="admin-shell__main">
        <header className="admin-shell__header">
          <div>
            <p className="text-sm font-semibold text-sanad-navy">Administration plateforme</p>
            <p className="max-w-[280px] truncate text-[11px] text-sanad-muted">
              {user?.full_name || "Admin"} · métriques ops (pas les dossiers)
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <ThemeToggle />
            <LanguageSwitch variant="light" />
            <UserAccountMenu compact />
            <div className="hidden items-center gap-1.5 text-[11px] text-sanad-muted xl:flex">
              <Shield className="h-3.5 w-3.5 text-sanad-gold" />
              <span title="Exploitation de la plateforme (ops = operations), pas un module avocat">
                Exploitation LexHub
              </span>
            </div>
          </div>
        </header>

        <main className="admin-shell__content">{children}</main>
      </div>

      {analysisOpen ? (
        <div
          className="admin-report-overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="admin-report-title"
          onClick={(e) => {
            if (e.target === e.currentTarget) setAnalysisOpen(false);
          }}
        >
          <div className="admin-report-modal">
            <div className="flex items-start justify-between gap-3 border-b border-sanad-stone px-5 py-4">
              <div>
                <h2 id="admin-report-title" className="font-serif text-lg font-bold text-sanad-navy">
                  Ops Coach — activité & gains
                </h2>
                <p className="text-xs text-slate-500">
                  Aligné sur le tableau de bord (cabinets clients)
                  {analysis?.period_days ? ` · ${analysis.period_days} j` : ""}
                  {analysis?.generated_at
                    ? ` · ${new Date(analysis.generated_at).toLocaleString("fr-FR")}`
                    : ""}
                </p>
              </div>
              <button
                type="button"
                className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100"
                onClick={() => setAnalysisOpen(false)}
                aria-label="Fermer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="max-h-[min(70vh,640px)] overflow-y-auto px-5 py-4">
              {analysisBusy && !analysis ? (
                <p className="text-sm text-slate-500">Chargement des métriques…</p>
              ) : null}
              {analysisErr ? <p className="text-sm text-red-600">{analysisErr}</p> : null}
              {analysis ? (
                <div className="space-y-4">
                  <p className="text-sm leading-relaxed text-slate-700">{analysis.summary_fr}</p>

                  {m ? (
                    <>
                      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                        <MetricTile label="Cabinets actifs" value={Number(m.cabinets_actifs || 0)} />
                        <MetricTile label="Utilisateurs" value={Number(m.utilisateurs || 0)} />
                        <MetricTile label="Connexions 30 j" value={Number(m.connexions_30j || 0)} />
                        <MetricTile label="Crédits IA (mois)" value={Number(m.credits_ia_mois || 0)} />
                        <MetricTile label="Plaidoiries (mois)" value={Number(m.plaidoiries_mois || 0)} />
                        <MetricTile label="Dossiers" value={Number(m.dossiers || 0)} />
                        <MetricTile label="Documents" value={Number(m.documents || 0)} />
                        <MetricTile label="Suspendus" value={Number(m.cabinets_suspendus || 0)} />
                      </div>

                      <div className="grid gap-4 lg:grid-cols-2">
                        <div className="rounded-xl border border-sanad-stone bg-slate-50 p-4">
                          <p className="mb-3 text-sm font-semibold text-sanad-navy">Abonnements</p>
                          <PieChart data={pieData} />
                        </div>
                        <div className="rounded-xl border border-sanad-stone bg-slate-50 p-4">
                          <p className="mb-3 text-sm font-semibold text-sanad-navy">Par ville</p>
                          <BarChart data={cityBars} color="#2563eb" />
                        </div>
                      </div>

                      <div className="rounded-xl border border-sanad-stone bg-slate-50 p-4">
                        <p className="mb-3 text-sm font-semibold text-sanad-navy">Crédits IA par plan</p>
                        {creditBars.length ? (
                          <BarChart data={creditBars} color="#0d9488" />
                        ) : (
                          <p className="text-xs text-slate-500">0 crédit consommé ce mois</p>
                        )}
                      </div>
                    </>
                  ) : null}

                  {analysis.recommendations.length ? (
                    <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                      <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-600">
                        Constats (faits uniquement)
                      </p>
                      <ul className="list-disc space-y-1 ps-4 text-sm text-slate-700">
                        {analysis.recommendations.map((r) => (
                          <li key={r}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}

                  <OpsCoachSection tips={normalizeOpsTips(analysis.growth_recommendations)} />

                  <p className="text-[11px] text-slate-400">
                    Mêmes filtres que le tableau de bord — cabinet interne WebVoice exclu. Aucun contenu de dossier.
                    Les emails ne partent qu’après votre validation.
                  </p>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
