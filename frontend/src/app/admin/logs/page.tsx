"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronRight, Search } from "lucide-react";
import { AdminShell } from "@/components/layout/admin-shell";
import { api, type AuditLogItem } from "@/lib/api";

type ActionFamily = "" | "auth" | "case" | "document" | "dictation" | "plaidoirie" | "admin" | "other";

/** Affiche l’IP masquée — précise si réseau Docker / privé */
function maskIp(ip: string | null | undefined): string {
  if (!ip) return "—";
  const v4 = ip.split(".");
  if (v4.length === 4) {
    const masked = `${v4[0]}.${v4[1]}.xxx.xxx`;
    const a = Number(v4[0]);
    const b = Number(v4[1]);
    if (a === 172 && b >= 16 && b <= 31) return `${masked} (réseau serveur)`;
    if (a === 10 || (a === 192 && b === 168)) return `${masked} (réseau privé)`;
    return masked;
  }
  if (ip.includes(":")) {
    const parts = ip.split(":");
    return `${parts.slice(0, 2).join(":")}:…`;
  }
  return `${ip.slice(0, 6)}…`;
}

const FAMILY_OPTIONS: { value: ActionFamily; label: string }[] = [
  { value: "", label: "Tous" },
  { value: "auth", label: "Auth" },
  { value: "case", label: "Dossiers" },
  { value: "document", label: "Documents" },
  { value: "dictation", label: "Dictée" },
  { value: "plaidoirie", label: "Plaidoirie" },
  { value: "admin", label: "Admin" },
  { value: "other", label: "Autres" },
];

const ACTION_LABELS: Record<string, string> = {
  "auth.login_success": "Connexion réussie",
  "auth.login_failed": "Échec de connexion",
  "auth.google_login": "Connexion Google",
  "auth.2fa_failed": "Échec 2FA",
  "auth.2fa_enabled": "2FA activée",
  "auth.2fa_disabled": "2FA désactivée",
  "auth.forgot_password": "Mot de passe oublié",
  "case.create": "Création de dossier",
  "case.update": "Mise à jour dossier",
  "case.delete": "Suppression de dossier",
  "document.upload": "Upload document",
  "document.delete": "Suppression document",
  "document.download": "Téléchargement document",
  "document.reextract": "Ré-extraction OCR",
  "document.ask": "Question sur document",
  "document.summarize": "Synthèse document",
  "dictation.transcribe": "Transcription dictée",
  "plaidoirie.validate": "Validation plaidoirie",
  "plaidoirie.assign": "Assignation plaidoirie",
  "admin.corpus_reindex": "Réindexation corpus",
  "admin.platform_analysis": "Rapport Ops Coach (métriques)",
  "admin.ops_coach_draft": "Brouillon email Ops Coach",
  "admin.ops_coach_send": "Envoi email Ops Coach",
  "team.update": "Mise à jour équipe",
  "team.join_code_regenerate": "Régénération code cabinet",
  "settings.cabinet_update": "Paramètres cabinet",
  "settings.password_change": "Changement mot de passe",
  "settings.profile_names": "Mise à jour profil",
  "note.create": "Création note",
  "task.create": "Création tâche",
  "agenda.create": "Création événement",
};

function actionFamily(action: string): ActionFamily {
  const a = (action || "").toLowerCase();
  if (a.startsWith("auth.")) return "auth";
  if (a.startsWith("case.")) return "case";
  if (a.startsWith("document.")) return "document";
  if (a.startsWith("dictation.")) return "dictation";
  if (a.startsWith("plaidoirie") || a.includes("plaidoirie")) return "plaidoirie";
  if (a.startsWith("admin.") || a.startsWith("team.") || a.startsWith("settings.")) return "admin";
  return "other";
}

function actionLabel(action: string) {
  return ACTION_LABELS[action] || action.replace(/\./g, " · ");
}

function severityClass(action: string) {
  const a = (action || "").toLowerCase();
  if (a === "auth.login_failed" || a.includes("login_failed") || a.endsWith("_failed")) {
    return "bg-red-50 text-red-800 border-red-200";
  }
  if (a.includes(".delete") || a.endsWith("delete")) {
    return "bg-amber-50 text-amber-900 border-amber-200";
  }
  if (a === "auth.login_success" || a.includes("login_success")) {
    return "bg-emerald-50/80 text-emerald-800/80 border-emerald-100";
  }
  return "bg-slate-50 text-slate-700 border-slate-200";
}

function whoLabel(log: AuditLogItem) {
  const name = log.user_name?.trim();
  const email = log.user_email?.trim();
  if (name && email) return { primary: name, secondary: email };
  if (name) return { primary: name, secondary: null };
  if (email) return { primary: email, secondary: null };
  return { primary: "—", secondary: null };
}

function humanizeDetails(action: string, details: string | null | undefined): string {
  const text = (details || "").trim();
  if (!text) return "";
  const scenarios: Record<string, string> = {
    trial_convert: "relance essai → plan payant",
    trial_ending: "essai bientôt terminé",
    past_due: "rappel paiement",
    cancel_retain: "rétention (résiliation)",
    upsell_solo: "proposition upgrade Solo",
    heavy_usage: "usage IA élevé",
    activate_billing: "activation abonnement",
    first_plea: "première plaidoirie",
  };
  if (text === "ok") {
    if (action === "admin.platform_analysis") return "Rapport d’activité généré avec succès.";
    return "Action réussie.";
  }
  if (text.startsWith("tip=") || text.includes(" cab=")) {
    const tip = /tip=([^\s]+)/.exec(text)?.[1] || "";
    const to = /to=([^\s]+)/.exec(text)?.[1];
    const subj = /subj=(.+)$/.exec(text)?.[1];
    const label = scenarios[tip] || tip || "Ops Coach";
    if (to) return `Email envoyé (${label}) à ${to}${subj ? ` — « ${subj} »` : ""}.`;
    return `Action Ops Coach : ${label}.`;
  }
  const draft = /^([a-z_]+):([0-9a-f-]{8,})$/i.exec(text);
  if (draft) {
    const label = scenarios[draft[1]] || draft[1];
    return `Brouillon email préparé (${label}).`;
  }
  return text;
}

function DetailsCell({ action, details }: { action: string; details: string | null }) {
  const [open, setOpen] = useState(false);
  const text = humanizeDetails(action, details);
  if (!text) return <span className="text-slate-400">—</span>;
  const long = text.length > 90;
  if (!long) return <span className="text-slate-600">{text}</span>;
  return (
    <button
      type="button"
      className="group flex max-w-md items-start gap-1 text-left text-slate-600 hover:text-slate-900"
      onClick={() => setOpen((v) => !v)}
    >
      {open ? (
        <ChevronDown className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-400" />
      ) : (
        <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-400" />
      )}
      <span className={open ? "whitespace-pre-wrap break-words" : "truncate"}>
        {open ? text : `${text.slice(0, 90)}…`}
      </span>
    </button>
  );
}

export default function AdminLogsPage() {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [qDebounced, setQDebounced] = useState("");
  const [family, setFamily] = useState<ActionFamily>("");
  const [archives, setArchives] = useState<
    {
      id: string;
      filename: string;
      period_start: string;
      period_end: string;
      row_count: number;
      created_at: string;
    }[]
  >([]);
  const [archiveBusy, setArchiveBusy] = useState(false);

  const loadArchives = useCallback(async () => {
    try {
      setArchives(await api.getAuditArchives());
    } catch {
      setArchives([]);
    }
  }, []);

  useEffect(() => {
    const t = window.setTimeout(() => setQDebounced(q.trim()), 280);
    return () => window.clearTimeout(t);
  }, [q]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const actionParam =
        family && family !== "other"
          ? family === "case"
            ? "case"
            : family
          : undefined;
      const data = await api.getAuditLogs({
        limit: 200,
        q: qDebounced || undefined,
        action: actionParam,
      });
      setLogs(data);
    } catch {
      setLogs([]);
    } finally {
      setLoading(false);
    }
  }, [family, qDebounced]);

  useEffect(() => {
    void load();
    void loadArchives();
  }, [load, loadArchives]);

  const filtered = useMemo(() => {
    if (family !== "other") return logs;
    return logs.filter((l) => actionFamily(l.action) === "other");
  }, [logs, family]);

  const stats = useMemo(() => {
    const authFail = filtered.filter((l) =>
      (l.action || "").toLowerCase().includes("login_failed"),
    ).length;
    const deletes = filtered.filter((l) =>
      (l.action || "").toLowerCase().includes(".delete"),
    ).length;
    const logins = filtered.filter((l) => {
      const a = (l.action || "").toLowerCase();
      return a.includes("login_success") || a === "auth.google_login";
    }).length;
    return { total: filtered.length, authFail, deletes, logins };
  }, [filtered]);

  return (
    <AdminShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-sanad-slate">Journal d&apos;audit</h1>
          <p className="mt-1 max-w-2xl text-sm text-slate-500">
            Trace technique des opérations plateforme (connexions, exports, admin) — comme
            dans toute application SaaS professionnelle (traçabilité sécurité, pas surveillance
            du contenu). La colonne <strong>IP</strong> est l’adresse réseau de la requête (bureau,
            4G, VPN) : changer de ville ou de box change l’IP. Ce n’est pas une erreur de saisie.
            Aucun texte de plaidoirie ni pièce jointe. Conservation 5 ans ; au-delà
            de 90 jours les entrées anciennes passent en archive Excel téléchargeable ci-dessous.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {[
            { label: "Chargés", value: stats.total, tone: "bg-slate-100 text-slate-700" },
            {
              label: "Échecs auth",
              value: stats.authFail,
              tone: "bg-red-50 text-red-800",
            },
            {
              label: "Suppressions",
              value: stats.deletes,
              tone: "bg-amber-50 text-amber-900",
            },
            {
              label: "Connexions",
              value: stats.logins,
              tone: "bg-emerald-50 text-emerald-800",
            },
          ].map((chip) => (
            <div
              key={chip.label}
              className={`inline-flex items-center gap-2 rounded-full border border-black/5 px-3.5 py-1.5 text-sm ${chip.tone}`}
            >
              <span className="text-lg font-semibold tabular-nums leading-none">{chip.value}</span>
              <span className="text-xs font-medium opacity-80">{chip.label}</span>
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <label className="relative flex min-w-0 flex-1 items-center">
            <Search className="pointer-events-none absolute start-3 h-4 w-4 text-slate-400" />
            <input
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Rechercher (action, IP, détails, e-mail…)"
              className="w-full rounded-xl border border-sanad-border bg-white py-2.5 pe-3 ps-10 text-sm text-slate-800 outline-none ring-sanad-blue/30 placeholder:text-slate-400 focus:ring-2"
            />
          </label>
          <select
            value={family}
            onChange={(e) => setFamily(e.target.value as ActionFamily)}
            className="rounded-xl border border-sanad-border bg-white px-3 py-2.5 text-sm text-slate-800 outline-none ring-sanad-blue/30 focus:ring-2"
            aria-label="Famille d'actions"
          >
            {FAMILY_OPTIONS.map((o) => (
              <option key={o.value || "all"} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        <div className="overflow-hidden rounded-2xl border border-sanad-border bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[880px] text-sm">
              <thead>
                <tr className="border-b border-sanad-border bg-sanad-light/80 text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-5 py-3 font-semibold">Date-heure</th>
                  <th className="px-5 py-3 font-semibold">Action</th>
                  <th className="px-5 py-3 font-semibold">Qui</th>
                  <th className="px-5 py-3 font-semibold">Cabinet</th>
                  <th className="px-5 py-3 font-semibold" title="Adresse du réseau d’où l’action a été faite (ville / VPN / bureau). Derrière Caddy, ce n’est plus l’IP interne Docker.">
                    IP
                  </th>
                  <th className="px-5 py-3 font-semibold">Détails</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-5 py-14 text-center text-slate-400">
                      Chargement du journal…
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-5 py-14 text-center">
                      <div className="text-slate-500">Aucun événement pour ces filtres</div>
                      <p className="mt-1 text-xs text-slate-400">
                        Élargissez la recherche ou changez de famille d&apos;actions.
                      </p>
                    </td>
                  </tr>
                ) : (
                  filtered.map((log) => {
                    const who = whoLabel(log);
                    return (
                      <tr
                        key={log.id}
                        className="border-b border-sanad-border/80 last:border-0 hover:bg-slate-50/70"
                      >
                        <td className="whitespace-nowrap px-5 py-3.5 text-slate-600">
                          {new Date(log.created_at).toLocaleString("fr-FR", {
                            dateStyle: "short",
                            timeStyle: "medium",
                          })}
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="flex flex-col gap-1">
                            <span
                              className={`inline-flex w-fit rounded-md border px-2 py-0.5 text-xs font-semibold ${severityClass(log.action)}`}
                            >
                              {actionLabel(log.action)}
                            </span>
                            <span className="font-mono text-[10px] text-slate-400">
                              {log.action}
                            </span>
                          </div>
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="font-medium text-slate-800">{who.primary}</div>
                          {who.secondary ? (
                            <div className="text-xs text-slate-400">{who.secondary}</div>
                          ) : null}
                        </td>
                        <td className="px-5 py-3.5 text-slate-600">
                          {log.cabinet_name || "—"}
                        </td>
                        <td className="px-5 py-3.5 font-mono text-xs text-slate-500" title={log.ip_address || undefined}>
                          {maskIp(log.ip_address)}
                        </td>
                        <td className="px-5 py-3.5">
                          <DetailsCell action={log.action} details={log.details} />
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        <section className="rounded-2xl border border-sanad-border bg-white p-5 shadow-sm">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-sanad-slate">Archives Excel</h2>
              <p className="text-sm text-slate-500">
                Logs de plus de 90 jours — export automatique ou manuel, téléchargement ici.
              </p>
            </div>
            <button
              type="button"
              disabled={archiveBusy}
              className="rounded-lg bg-sanad-navy px-4 py-2 text-sm font-medium text-white hover:bg-sanad-navy/90 disabled:opacity-50"
              onClick={() => {
                setArchiveBusy(true);
                void api
                  .runAuditArchive()
                  .then(() => Promise.all([loadArchives(), load()]))
                  .finally(() => setArchiveBusy(false));
              }}
            >
              {archiveBusy ? "Archivage…" : "Archiver les logs > 90 j"}
            </button>
          </div>
          {archives.length === 0 ? (
            <p className="text-sm text-slate-400">Aucune archive pour le moment.</p>
          ) : (
            <ul className="divide-y divide-sanad-border">
              {archives.map((a) => (
                <li
                  key={a.id}
                  className="flex flex-wrap items-center justify-between gap-3 py-3 text-sm"
                >
                  <div>
                    <p className="font-medium text-slate-800">{a.filename}</p>
                    <p className="text-xs text-slate-500">
                      {a.row_count} lignes ·{" "}
                      {new Date(a.period_start).toLocaleDateString("fr-FR")} →{" "}
                      {new Date(a.period_end).toLocaleDateString("fr-FR")} · archivé le{" "}
                      {new Date(a.created_at).toLocaleString("fr-FR")}
                    </p>
                  </div>
                  <button
                    type="button"
                    className="rounded-lg border border-sanad-border px-3 py-1.5 text-sm font-medium text-sanad-navy hover:bg-sanad-light"
                    onClick={() => void api.downloadAuditArchive(a.id, a.filename)}
                  >
                    Télécharger
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </AdminShell>
  );
}
