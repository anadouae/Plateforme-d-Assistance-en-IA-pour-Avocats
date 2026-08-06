"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, ApiError } from "@/lib/api";
import { CASE_DOMAINS } from "@/lib/case-domains";
import { FadeIn } from "@/components/motion/fade-in";

export default function NewCasePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    client_name: "",
    case_type: "Civil",
    status: "En cours",
    description: "",
  });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const created = await api.createCase({
        client_name: form.client_name,
        case_type: form.case_type,
        status: form.status,
        description: form.description || undefined,
      });
      router.push(`/cases/${created.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur lors de la création");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <FadeIn className="mx-auto max-w-xl space-y-6">
        <Link href="/cases" className="inline-flex items-center gap-1 text-sm text-sanad-blue hover:underline">
          <ArrowLeft className="h-4 w-4" />
          Retour
        </Link>
        <Card className="shadow-luxe">
          <CardHeader>
            <CardTitle className="font-display text-sanad-navy">Nouveau dossier</CardTitle>
            <p className="text-sm text-slate-500">
              Choisissez un domaine pour faciliter la recherche et la réutilisation des plaidoiries.
            </p>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Nom du client"
                value={form.client_name}
                onChange={(e) => setForm({ ...form, client_name: e.target.value })}
                required
              />
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-sanad-slate">Domaine</label>
                <select
                  value={form.case_type}
                  onChange={(e) => setForm({ ...form, case_type: e.target.value })}
                  className="flex h-10 w-full rounded-lg border border-sanad-border bg-white px-3 text-sm"
                  required
                >
                  {CASE_DOMAINS.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-sanad-slate">Statut</label>
                <select
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="flex h-10 w-full rounded-lg border border-sanad-border bg-white px-3 text-sm"
                >
                  <option>En cours</option>
                  <option>Urgent</option>
                  <option>Clôturé</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-sanad-slate">Description</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={3}
                  className="w-full rounded-lg border border-sanad-border bg-white px-3 py-2 text-sm"
                />
              </div>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Création..." : "Créer le dossier"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </FadeIn>
    </AppShell>
  );
}
