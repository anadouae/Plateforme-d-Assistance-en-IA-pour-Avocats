"use client";

import { useEffect, useState } from "react";
import { AdminShell } from "@/components/layout/admin-shell";
import { Button } from "@/components/ui/button";
import { api, ApiError, type CommercialLead } from "@/lib/api";
import { useTranslations } from "@/store/locale";

const STATUS: { id: CommercialLead["status"]; label: string }[] = [
  { id: "new", label: "Nouveau" },
  { id: "contacted", label: "Contacté" },
  { id: "qualified", label: "Qualifié" },
  { id: "closed", label: "Clos" },
];

export default function AdminLeadsPage() {
  const t = useTranslations().adminPlatform;
  const [rows, setRows] = useState<CommercialLead[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  function load() {
    api
      .getAdminCommercialLeads()
      .then(setRows)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Chargement impossible"));
  }

  useEffect(() => {
    load();
  }, []);

  async function setStatus(id: string, status: CommercialLead["status"]) {
    setBusy(id);
    setError("");
    try {
      await api.updateAdminCommercialLead(id, status);
      setRows((prev) => prev.map((r) => (r.id === id ? { ...r, status } : r)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Mise à jour impossible");
    } finally {
      setBusy(null);
    }
  }

  return (
    <AdminShell>
      <div className="space-y-4 p-6">
        <div>
          <h1 className="font-serif text-2xl font-bold text-sanad-navy">{t.leadsTitle}</h1>
          <p className="max-w-2xl text-sm text-slate-600">{t.leadsSubtitle}</p>
        </div>
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <div className="overflow-x-auto rounded-xl border border-sanad-border bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2">Date</th>
                <th className="px-3 py-2">Type</th>
                <th className="px-3 py-2">Contact</th>
                <th className="px-3 py-2">Cabinet</th>
                <th className="px-3 py-2">Message</th>
                <th className="px-3 py-2">Statut</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-3 py-8 text-center text-slate-500">
                    Aucune demande pour l’instant.
                  </td>
                </tr>
              ) : (
                rows.map((r) => (
                  <tr key={r.id} className="border-t border-slate-100 align-top">
                    <td className="whitespace-nowrap px-3 py-2 text-xs text-slate-500">
                      {r.created_at ? new Date(r.created_at).toLocaleString("fr-FR") : "—"}
                    </td>
                    <td className="px-3 py-2 font-medium">
                      {r.kind === "custom" ? "Sur mesure" : "Entreprise"}
                    </td>
                    <td className="px-3 py-2">
                      <div className="font-medium">{r.full_name}</div>
                      <a className="text-xs text-sanad-blue underline" href={`mailto:${r.email}`}>
                        {r.email}
                      </a>
                      {r.phone ? <div className="text-xs text-slate-500">{r.phone}</div> : null}
                    </td>
                    <td className="px-3 py-2 text-xs">
                      <div>{r.cabinet_name || "—"}</div>
                      <div className="text-slate-500">
                        {r.city || "—"}
                        {r.lawyers_count ? ` · ${r.lawyers_count} avocats` : ""}
                      </div>
                    </td>
                    <td className="max-w-xs px-3 py-2 text-xs text-slate-600">{r.message || "—"}</td>
                    <td className="px-3 py-2">
                      <select
                        className="rounded-md border border-slate-200 px-2 py-1 text-xs"
                        value={r.status}
                        disabled={busy === r.id}
                        onChange={(e) => void setStatus(r.id, e.target.value as CommercialLead["status"])}
                      >
                        {STATUS.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.label}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <Button type="button" variant="outline" size="sm" onClick={load}>
          Actualiser
        </Button>
      </div>
    </AdminShell>
  );
}
