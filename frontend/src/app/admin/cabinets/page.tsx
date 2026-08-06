"use client";

import { useEffect, useState } from "react";
import { AdminShell } from "@/components/layout/admin-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api, type AdminCabinet } from "@/lib/api";

export default function AdminCabinetsPage() {
  const [cabinets, setCabinets] = useState<AdminCabinet[]>([]);
  const [message, setMessage] = useState("");

  function load() {
    api.getAdminCabinets().then(setCabinets).catch(() => setCabinets([]));
  }

  useEffect(() => { load(); }, []);

  async function toggleStatus(cabinet: AdminCabinet) {
    const newStatus = cabinet.status === "active" ? "suspended" : "active";
    if (!confirm(`${newStatus === "suspended" ? "Suspendre" : "Activer"} ${cabinet.name} ?`)) return;
    const res = await api.updateCabinetStatus(cabinet.id, newStatus);
    setMessage(res.message);
    load();
  }

  return (
    <AdminShell>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-sanad-slate">Gestion des cabinets</h1>
        {message && <p className="rounded-lg bg-green-50 px-3 py-2 text-sm text-green-700">{message}</p>}

        <Card>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-sanad-border bg-sanad-light text-left text-slate-500">
                  <th className="px-6 py-3 font-medium">Cabinet</th>
                  <th className="px-6 py-3 font-medium">Barreau</th>
                  <th className="px-6 py-3 font-medium">Statut</th>
                  <th className="px-6 py-3 font-medium">Utilisateurs</th>
                  <th className="px-6 py-3 font-medium">Documents</th>
                  <th className="px-6 py-3 font-medium">Dossiers</th>
                  <th className="px-6 py-3 font-medium">IA</th>
                  <th className="px-6 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {cabinets.map((c) => (
                  <tr key={c.id} className="border-b border-sanad-border">
                    <td className="px-6 py-4">
                      <p className="font-medium text-sanad-slate">{c.name}</p>
                      <p className="text-xs text-slate-500">{c.city}</p>
                    </td>
                    <td className="px-6 py-4 text-slate-600">{c.barreau}</td>
                    <td className="px-6 py-4">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        c.status === "active" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                      }`}>
                        {c.status === "active" ? "Actif" : "Suspendu"}
                      </span>
                    </td>
                    <td className="px-6 py-4">{c.user_count}</td>
                    <td className="px-6 py-4">{c.document_count}</td>
                    <td className="px-6 py-4">{c.case_count}</td>
                    <td className="px-6 py-4">{c.summarize_count}</td>
                    <td className="px-6 py-4">
                      <Button
                        variant={c.status === "active" ? "destructive" : "default"}
                        size="sm"
                        onClick={() => toggleStatus(c)}
                      >
                        {c.status === "active" ? "Suspendre" : "Activer"}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>
    </AdminShell>
  );
}
