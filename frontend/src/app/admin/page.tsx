"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Building2, MessageSquare, Users, FileText } from "lucide-react";
import { AdminShell } from "@/components/layout/admin-shell";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api, type AdminCabinet, type AdminMetrics } from "@/lib/api";

export default function AdminDashboardPage() {
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [cabinets, setCabinets] = useState<AdminCabinet[]>([]);

  useEffect(() => {
    api.getAdminMetrics().then(setMetrics).catch(() => {});
    api.getAdminCabinets().then(setCabinets).catch(() => {});
  }, []);

  const stats = metrics
    ? [
        { label: "Cabinets actifs", value: metrics.active_cabinets, icon: Building2, color: "text-green-600" },
        { label: "Cabinets suspendus", value: metrics.suspended_cabinets, icon: Building2, color: "text-red-600" },
        { label: "Utilisateurs", value: metrics.total_users, icon: Users, color: "text-sanad-blue" },
        { label: "Documents", value: metrics.total_documents, icon: FileText, color: "text-sanad-gold" },
        { label: "Actions IA aujourd'hui", value: metrics.ai_actions_today, icon: MessageSquare, color: "text-purple-600" },
        { label: "Score OCR moyen", value: `${metrics.avg_ocr_score} %`, icon: MessageSquare, color: "text-sanad-gold" },
      ]
    : [];

  return (
    <AdminShell>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-sanad-slate">Back-office WebVoice</h1>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
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

        <Card>
          <CardContent className="p-0">
            <div className="border-b border-sanad-border px-6 py-4">
              <h2 className="font-semibold text-sanad-slate">Cabinets récents</h2>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-sanad-border bg-sanad-light text-left text-slate-500">
                  <th className="px-6 py-3 font-medium">Cabinet</th>
                  <th className="px-6 py-3 font-medium">Ville</th>
                  <th className="px-6 py-3 font-medium">Statut</th>
                  <th className="px-6 py-3 font-medium">Utilisateurs</th>
                  <th className="px-6 py-3 font-medium">Synthèses</th>
                </tr>
              </thead>
              <tbody>
                {cabinets.slice(0, 5).map((c) => (
                  <tr key={c.id} className="border-b border-sanad-border">
                    <td className="px-6 py-4 font-medium">{c.name}</td>
                    <td className="px-6 py-4 text-slate-600">{c.city}</td>
                    <td className="px-6 py-4">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        c.status === "active" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                      }`}>
                        {c.status === "active" ? "Actif" : "Suspendu"}
                      </span>
                    </td>
                    <td className="px-6 py-4">{c.user_count}</td>
                    <td className="px-6 py-4">{c.summarize_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="px-6 py-4">
              <Link href="/admin/cabinets">
                <Button variant="outline" size="sm">Voir tous les cabinets</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </AdminShell>
  );
}
