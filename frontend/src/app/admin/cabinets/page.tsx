"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { AdminShell } from "@/components/layout/admin-shell";
import { InvoicesList } from "@/components/billing/invoices-list";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api, ApiError, type AdminCabinet, type AdminCabinetDetail } from "@/lib/api";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { useTranslations } from "@/store/locale";

function statusLabel(status: string) {
  if (status === "active") return { text: "Actif", cls: "bg-green-100 text-green-700" };
  if (status === "pending") return { text: "En attente", cls: "bg-amber-100 text-amber-800" };
  return { text: "Suspendu", cls: "bg-red-100 text-red-700" };
}

function fmtDate(iso?: string | null) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("fr-FR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

export default function AdminCabinetsPage() {
  const t = useTranslations().adminPlatform;
  const askConfirm = useConfirm();
  const [cabinets, setCabinets] = useState<AdminCabinet[]>([]);
  const [detail, setDetail] = useState<AdminCabinetDetail | null>(null);
  const [showDeleted, setShowDeleted] = useState(false);
  const [insights, setInsights] = useState<{
    total: number;
    by_reason: { code: string; label: string; count: number }[];
    ai_suggestion?: string | null;
  } | null>(null);
  const [message, setMessage] = useState("");
  const [messageTone, setMessageTone] = useState<"ok" | "err">("ok");
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [invBusy, setInvBusy] = useState<string | null>(null);
  const [invError, setInvError] = useState("");

  function load() {
    api.getAdminCabinets().then(setCabinets).catch(() => setCabinets([]));
    api.getAdminCancelInsights().then(setInsights).catch(() => setInsights(null));
  }

  useEffect(() => {
    load();
  }, []);

  async function openDetail(cabinet: AdminCabinet) {
    setLoadingDetail(true);
    setMessage("");
    setShowDeleted(false);
    setInvError("");
    setInvBusy(null);
    try {
      const d = await api.getAdminCabinetDetail(cabinet.id);
      setDetail(d);
    } catch {
      setMessage("Impossible de charger le détail du cabinet.");
    } finally {
      setLoadingDetail(false);
    }
  }

  async function setCabinetActive(cabinet: AdminCabinet, active: boolean) {
    const ok = await askConfirm({
      title: active ? `Activer ${cabinet.name} ?` : `Suspendre ${cabinet.name} ?`,
      description: active
        ? "Tous les comptes vérifiés pourront se reconnecter."
        : "Tous les comptes du cabinet seront bloqués immédiatement.",
      tone: active ? "default" : "danger",
    });
    if (!ok) return;
    const res = await api.updateCabinetStatus(cabinet.id, active ? "active" : "suspended");
    setMessage(res.message);
    load();
    if (detail?.id === cabinet.id) await openDetail(cabinet);
  }

  async function deleteCabinet(cabinet: AdminCabinet) {
    const ok = await askConfirm({
      title: `Supprimer définitivement « ${cabinet.name} » ?`,
      description:
        "Action irréversible. Tous les comptes, dossiers, pièces, abonnements et logs de ce cabinet seront effacés. Tapez supprimer pour confirmer.",
      tone: "danger",
      requireDeletePhrase: true,
      deleteVisual: "folder",
      confirmLabel: "Supprimer le cabinet",
    });
    if (!ok) return;
    try {
      const res = await api.deleteAdminCabinet(cabinet.id, "SUPPRIMER");
      setMessageTone("ok");
      setMessage(res.message);
      if (detail?.id === cabinet.id) setDetail(null);
      load();
    } catch (err) {
      setMessageTone("err");
      setMessage(err instanceof ApiError ? err.message : "Suppression impossible.");
    }
  }

  async function toggleUser(userId: string, activate: boolean, email: string) {
    const ok = await askConfirm({
      title: activate ? `Activer ${email} ?` : `Désactiver ${email} ?`,
      tone: activate ? "default" : "danger",
    });
    if (!ok) return;
    const res = await api.updateAdminUserStatus(userId, activate);
    setMessage(res.message);
    if (detail) {
      const refreshed = await api.getAdminCabinetDetail(detail.id);
      setDetail(refreshed);
    }
  }

  return (
    <AdminShell>
      <div className="space-y-6 p-6">
        <div>
          <h1 className="font-serif text-2xl font-bold text-[#0B1A4D]">{t.cabinetsTitle}</h1>
          <p className="text-sm text-slate-600">{t.cabinetsSubtitle}</p>
        </div>

        {insights && insights.total > 0 ? (
          <Card className="border-amber-200/70 bg-amber-50/40">
            <CardContent className="space-y-2 py-4 text-sm">
              <p className="font-semibold text-[#0B1A4D]">
                Résiliations ({insights.total}) — motifs clients
              </p>
              <div className="flex flex-wrap gap-2">
                {insights.by_reason.map((r) => (
                  <span
                    key={r.code}
                    className="rounded-full bg-white px-2.5 py-1 text-xs text-slate-700 shadow-sm"
                  >
                    {r.label}: <strong>{r.count}</strong>
                  </span>
                ))}
              </div>
              {insights.ai_suggestion ? (
                <p className="text-xs text-slate-600">{insights.ai_suggestion}</p>
              ) : (
                <p className="text-xs text-slate-600">
                  Motifs de résiliation déclarés par les cabinets — utile pour prioriser le produit.
                </p>
              )}
            </CardContent>
          </Card>
        ) : null}

        {message ? (
          <p className={`text-sm ${messageTone === "err" ? "text-red-600" : "text-green-700"}`}>
            {message}
          </p>
        ) : null}
        {loadingDetail ? <p className="text-sm text-slate-500">Chargement…</p> : null}

        <Card>
          <CardContent className="overflow-x-auto p-0">
            <table className="w-full min-w-[720px] text-sm">
              <thead>
                <tr className="bg-[#F7F5F0] text-left text-slate-500">
                  <th className="px-4 py-3 font-medium">Cabinet</th>
                  <th className="px-4 py-3 font-medium">Ville</th>
                  <th className="px-4 py-3 font-medium">Statut</th>
                  <th className="px-4 py-3 font-medium">Membres</th>
                  <th className="px-4 py-3 font-medium">Docs</th>
                  <th className="px-4 py-3 font-medium">Dossiers</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {cabinets.map((c) => {
                  const st = statusLabel(c.status);
                  return (
                    <tr key={c.id} className="border-t border-slate-100">
                      <td className="px-4 py-3 font-medium text-[#0B1A4D]">{c.name}</td>
                      <td className="px-4 py-3">{c.city}</td>
                      <td className="px-4 py-3">
                        <span className={`rounded-full px-2 py-0.5 text-xs ${st.cls}`}>{st.text}</span>
                      </td>
                      <td className="px-4 py-3">{c.user_count}</td>
                      <td className="px-4 py-3">{c.document_count}</td>
                      <td className="px-4 py-3">{c.case_count}</td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-2">
                          <Button size="sm" variant="outline" onClick={() => void openDetail(c)}>
                            Détails
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                              void setCabinetActive(c, c.status !== "active")
                            }
                          >
                            {c.status === "active" ? "Suspendre" : "Activer"}
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => void deleteCabinet(c)}
                          >
                            Supprimer
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>

      {detail && (
        <div
          className="fixed inset-0 z-[9999] flex items-center justify-center bg-[#0B1A4D]/50 p-4"
          onClick={() => setDetail(null)}
        >
          <div
            className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-slate-200 bg-white shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sticky top-0 flex items-center justify-between border-b border-slate-100 bg-white px-6 py-4">
              <div>
                <h2 className="font-serif text-xl text-[#0B1A4D]">{detail.name}</h2>
                <p className="text-sm text-slate-500">
                  {detail.city} · {detail.barreau}
                </p>
              </div>
              <button
                type="button"
                className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
                onClick={() => setDetail(null)}
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-6 px-6 py-5 text-sm">
              <section className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl bg-[#F7F5F0]/80 p-3">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Adresse</p>
                  <p className="mt-1 text-slate-700">{detail.address}</p>
                </div>
                <div className="rounded-xl bg-[#F7F5F0]/80 p-3">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-400">ICE</p>
                  <p className="mt-1 text-slate-700">{detail.ice || "—"}</p>
                </div>
                <div className="rounded-xl bg-[#F7F5F0]/80 p-3">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Inscrit le</p>
                  <p className="mt-1 text-slate-700">{fmtDate(detail.created_at)}</p>
                </div>
                <div className="rounded-xl bg-[#F7F5F0]/80 p-3">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                    Activité
                  </p>
                  <p className="mt-1 text-slate-700">
                    {detail.user_count} membre(s) · {detail.document_count} doc(s) · {detail.case_count}{" "}
                    dossier(s)
                  </p>
                </div>
              </section>

              <section className="rounded-2xl border border-[#C9A227]/35 bg-gradient-to-br from-white to-[#F7F5F0] p-4">
                <h3 className="font-semibold text-[#0B1A4D]">Abonnement & factures</h3>
                <p className="mt-1 text-xs text-slate-500">
                  Vue facturation du cabinet — plan et factures payantes (> 0 MAD) uniquement.
                </p>

                {detail.subscription ? (
                  <div className="mt-3 grid gap-2 sm:grid-cols-2">
                    <p>
                      <span className="text-slate-500">Plan :</span>{" "}
                      <strong>{detail.subscription.plan_name || "—"}</strong> (
                      {detail.subscription.plan_slug})
                    </p>
                    <p>
                      <span className="text-slate-500">Statut :</span>{" "}
                      <strong>{detail.subscription.status}</strong>
                    </p>
                    <p>
                      <span className="text-slate-500">Cycle :</span>{" "}
                      {detail.subscription.billing_cycle || "—"}
                    </p>
                    <p>
                      <span className="text-slate-500">Fin d’essai :</span>{" "}
                      {fmtDate(detail.subscription.trial_ends_at)}
                    </p>
                    <p>
                      <span className="text-slate-500">Fin de période :</span>{" "}
                      {fmtDate(detail.subscription.current_period_end)}
                    </p>
                    <p>
                      <span className="text-slate-500">Paiement :</span>{" "}
                      {detail.subscription.payment_provider || "manual"}
                    </p>
                    {detail.subscription.cancel_at_period_end ? (
                      <p className="sm:col-span-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-red-800">
                        Résiliation demandée le {fmtDate(detail.subscription.cancel_requested_at)} —{" "}
                        <strong>{detail.subscription.cancel_reason_code}</strong>
                        {detail.subscription.cancel_reason_text
                          ? ` : ${detail.subscription.cancel_reason_text}`
                          : ""}
                      </p>
                    ) : null}
                  </div>
                ) : (
                  <p className="mt-3 text-xs text-slate-500">Aucun abonnement enregistré.</p>
                )}

                <div className="mt-4 border-t border-slate-200/80 pt-4">
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Factures & reçus
                  </p>
                  {invError ? <p className="mb-2 text-xs text-red-600">{invError}</p> : null}
                  <InvoicesList
                    invoices={detail.invoices || []}
                    busyId={invBusy}
                    onBusy={setInvBusy}
                    onError={setInvError}
                    compact
                    emptyHint="Aucune facture payante (> 0 MAD) pour ce cabinet."
                  />
                </div>

                {detail.billing_history && detail.billing_history.length > 0 ? (
                  <div className="mt-4 border-t border-slate-200/80 pt-4">
                    <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Historique abonnement
                    </p>
                    <ul className="max-h-36 space-y-1 overflow-y-auto text-xs text-slate-600">
                      {detail.billing_history.map((e, i) => (
                        <li key={`${e.event_type}-${i}`}>
                          {fmtDate(e.created_at)} — {e.event_type}
                          {e.plan_slug ? ` (${e.plan_slug})` : ""}
                          {e.detail ? ` · ${e.detail}` : ""}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </section>

              <section>
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <h3 className="font-semibold text-[#0B1A4D]">Membres actifs</h3>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => setShowDeleted((v) => !v)}
                  >
                    Comptes supprimés ({detail.deleted_accounts_count || 0})
                  </Button>
                </div>
                <div className="overflow-x-auto rounded-xl border border-slate-200">
                  <table className="w-full min-w-[520px] text-sm">
                    <thead>
                      <tr className="bg-[#F7F5F0] text-left text-slate-500">
                        <th className="px-4 py-2 font-medium">Nom</th>
                        <th className="px-4 py-2 font-medium">Email</th>
                        <th className="px-4 py-2 font-medium">Rôle</th>
                        <th className="px-4 py-2 font-medium">Statut</th>
                        <th className="px-4 py-2 font-medium">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.users.map((u) => (
                        <tr key={u.id} className="border-t border-slate-100">
                          <td className="px-4 py-2">{u.full_name}</td>
                          <td className="px-4 py-2">{u.email}</td>
                          <td className="px-4 py-2">{u.role}</td>
                          <td className="px-4 py-2">{u.is_active ? "Actif" : "Inactif"}</td>
                          <td className="px-4 py-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => void toggleUser(u.id, !u.is_active, u.email)}
                            >
                              {u.is_active ? "Désactiver" : "Activer"}
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              {showDeleted ? (
                <section>
                  <h3 className="mb-2 font-semibold text-[#0B1A4D]">
                    Comptes supprimés (anonymisés)
                  </h3>
                  {(detail.deleted_accounts || []).length === 0 ? (
                    <p className="text-slate-500">Aucun compte supprimé.</p>
                  ) : (
                    <ul className="space-y-2">
                      {(detail.deleted_accounts || []).map((u) => (
                        <li
                          key={u.id}
                          className="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-xs"
                        >
                          <strong>{u.full_name}</strong> · {u.email} · {u.role} · inscrit{" "}
                          {fmtDate(u.created_at)}
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              ) : null}

              <section className="rounded-xl border border-red-200 bg-red-50/60 p-4">
                <h3 className="font-semibold text-red-900">Zone danger</h3>
                <p className="mt-1 text-xs leading-relaxed text-red-800/90">
                  Suppression définitive réservée à l’admin plateforme. Irréversible — dossiers,
                  pièces et comptes inclus.
                </p>
                <Button
                  type="button"
                  size="sm"
                  variant="destructive"
                  className="mt-3"
                  onClick={() => void deleteCabinet(detail)}
                >
                  Supprimer ce cabinet
                </Button>
              </section>
            </div>
          </div>
        </div>
      )}
    </AdminShell>
  );
}
