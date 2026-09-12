"use client";

import { useEffect, useState } from "react";
import { AdminShell } from "@/components/layout/admin-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, ApiError, type BillingPlan } from "@/lib/api";

export default function AdminPlansPage() {
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<Record<string, Partial<BillingPlan>>>({});

  function load() {
    api
      .getAdminBillingPlans()
      .then(setPlans)
      .catch(() => setPlans([]));
  }

  useEffect(() => {
    load();
  }, []);

  function draft(id: string): BillingPlan {
    const base = plans.find((p) => p.id === id)!;
    return { ...base, ...(editing[id] || {}) } as BillingPlan;
  }

  async function save(id: string) {
    setError("");
    setMessage("");
    const d = draft(id);
    try {
      await api.updateAdminBillingPlan(id, {
        name: d.name,
        description: d.description || undefined,
        price_mad_monthly: d.price_mad_monthly,
        price_mad_yearly: d.price_mad_yearly,
        max_avocats: d.max_avocats,
        max_assistants: d.max_assistants,
        max_cases: d.max_cases,
        max_plaidoiries_month: d.max_plaidoiries_month,
        max_ai_credits_month: d.max_ai_credits_month ?? 50,
        is_recommended: d.is_recommended,
        is_active: d.is_active,
        is_public: d.is_public,
        sort_order: d.sort_order,
        trial_days: d.trial_days,
      });
      setMessage(`Plan « ${d.name} » mis à jour.`);
      setEditing((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Échec mise à jour");
    }
  }

  return (
    <AdminShell>
      <div className="space-y-4 p-6">
        <div>
          <h1 className="font-serif text-2xl font-bold text-sanad-navy">Plans tarifaires</h1>
          <p className="text-sm text-slate-600">
            Catalogue des abonnements LexHub (prix, quotas). Les <strong>factures</strong> ne sont pas ici :
            ce sont les reçus de chaque cabinet (essai, pack crédits), consultables dans{" "}
            <a href="/admin/cabinets" className="underline">
              Cabinets
            </a>{" "}
            → fiche du locataire → « Abonnement & factures ». Un cabinet sur plan Découverte sans pack n’a
            encore aucune facture.
          </p>
        </div>
        {message ? <p className="text-sm text-green-700">{message}</p> : null}
        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        <div className="grid gap-4 lg:grid-cols-2">
          {plans.map((p) => {
            const d = draft(p.id);
            const set = (patch: Partial<BillingPlan>) =>
              setEditing((prev) => ({ ...prev, [p.id]: { ...(prev[p.id] || {}), ...patch } }));
            return (
              <Card key={p.id}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between gap-2">
                    <span>
                      {p.name}{" "}
                      <span className="text-sm font-normal text-slate-500">({p.slug})</span>
                    </span>
                    {p.is_recommended ? (
                      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">
                        Recommandé
                      </span>
                    ) : null}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Input
                    label="Nom"
                    value={d.name}
                    onChange={(e) => set({ name: e.target.value })}
                  />
                  <Input
                    label="Description"
                    value={d.description || ""}
                    onChange={(e) => set({ description: e.target.value })}
                  />
                  <div className="grid grid-cols-2 gap-2">
                    <Input
                      label="Prix mensuel MAD"
                      type="number"
                      value={String(d.price_mad_monthly)}
                      onChange={(e) => set({ price_mad_monthly: Number(e.target.value) })}
                    />
                    <Input
                      label="Prix annuel MAD"
                      type="number"
                      value={String(d.price_mad_yearly)}
                      onChange={(e) => set({ price_mad_yearly: Number(e.target.value) })}
                    />
                    <Input
                      label="Max avocats"
                      type="number"
                      value={String(d.max_avocats)}
                      onChange={(e) => set({ max_avocats: Number(e.target.value) })}
                    />
                    <Input
                      label="Max assistants"
                      type="number"
                      value={String(d.max_assistants)}
                      onChange={(e) => set({ max_assistants: Number(e.target.value) })}
                    />
                    <Input
                      label="Max dossiers (−1 = ∞)"
                      type="number"
                      value={String(d.max_cases)}
                      onChange={(e) => set({ max_cases: Number(e.target.value) })}
                    />
                    <Input
                      label="Plaidoiries / mois (−1 = ∞)"
                      type="number"
                      value={String(d.max_plaidoiries_month)}
                      onChange={(e) => set({ max_plaidoiries_month: Number(e.target.value) })}
                    />
                    <Input
                      label="Crédits IA / mois"
                      type="number"
                      value={String(d.max_ai_credits_month ?? 50)}
                      onChange={(e) => set({ max_ai_credits_month: Number(e.target.value) })}
                    />
                  </div>
                  <p className="text-xs text-slate-500">
                    Les crédits IA sont gérés par plan (rédaction ≈ 10, révision ≈ 5, clé de barre ≈ 8).
                  </p>
                  <div className="flex flex-wrap gap-4 text-sm">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={!!d.is_recommended}
                        onChange={(e) => set({ is_recommended: e.target.checked })}
                      />
                      Recommandé
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={!!d.is_public}
                        onChange={(e) => set({ is_public: e.target.checked })}
                      />
                      Public
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={!!d.is_active}
                        onChange={(e) => set({ is_active: e.target.checked })}
                      />
                      Actif
                    </label>
                  </div>
                  <Button onClick={() => void save(p.id)}>Enregistrer</Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </AdminShell>
  );
}
