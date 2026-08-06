"use client";

import { useEffect, useState } from "react";
import { AdminShell } from "@/components/layout/admin-shell";
import { Card, CardContent } from "@/components/ui/card";
import { api, type AuditLogItem } from "@/lib/api";

export default function AdminLogsPage() {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);

  useEffect(() => {
    api.getAuditLogs().then(setLogs).catch(() => setLogs([]));
  }, []);

  return (
    <AdminShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-sanad-slate">Logs & Audit</h1>
          <p className="text-sm text-slate-500">Traçabilité complète — conservation 5 ans</p>
        </div>

        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-sanad-border bg-sanad-light text-left text-slate-500">
                    <th className="px-6 py-3 font-medium">Date</th>
                    <th className="px-6 py-3 font-medium">Action</th>
                    <th className="px-6 py-3 font-medium">Utilisateur</th>
                    <th className="px-6 py-3 font-medium">IP</th>
                    <th className="px-6 py-3 font-medium">Détails</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-slate-400">
                        Aucun log enregistré
                      </td>
                    </tr>
                  ) : (
                    logs.map((log) => (
                      <tr key={log.id} className="border-b border-sanad-border">
                        <td className="px-6 py-4 whitespace-nowrap text-slate-600">
                          {new Date(log.created_at).toLocaleString("fr-FR")}
                        </td>
                        <td className="px-6 py-4">
                          <span className="rounded bg-slate-100 px-2 py-0.5 font-mono text-xs">
                            {log.action}
                          </span>
                        </td>
                        <td className="px-6 py-4 font-mono text-xs text-slate-500">
                          {log.user_id?.slice(0, 8) || "—"}
                        </td>
                        <td className="px-6 py-4 text-slate-500">{log.ip_address || "—"}</td>
                        <td className="max-w-xs truncate px-6 py-4 text-slate-600">
                          {log.details || "—"}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </AdminShell>
  );
}
