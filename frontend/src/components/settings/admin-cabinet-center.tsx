"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type BillingEntitlements, type WorkspaceActivityItem } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useClientLocale } from "@/store/locale";

/** Centre admin cabinet : santé abo + audit équipe (pas de facture manuelle). */
export function AdminCabinetCenter() {
  const ar = useClientLocale() === "ar";
  const [ent, setEnt] = useState<BillingEntitlements | null>(null);
  const [audit, setAudit] = useState<WorkspaceActivityItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    void api.getBillingEntitlements().then(setEnt).catch(() => setEnt(null));
    void api
      .workspaceActivity(60)
      .then((rows) => {
        setAudit(
          rows
            .filter(
              (r) =>
                r.action?.startsWith("team.") ||
                r.action?.includes("invite") ||
                r.action === "payment_failed" ||
                r.action?.startsWith("billing."),
            )
            .slice(0, 12),
        );
      })
      .catch(() => setAudit([]));
  }, []);

  async function remind() {
    setBusy(true);
    setMsg("");
    try {
      const r = await api.sendPaymentReminder();
      setMsg(r.message);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Erreur");
    } finally {
      setBusy(false);
    }
  }

  const u = ent?.usage;
  const pastDue = ent?.status === "past_due";
  const restricted = !!ent?.access_restricted;
  const inTrial = ent?.status === "trial";
  // Relance utile seulement si paiement échoué (pas pendant l’essai)
  const showRemind = pastDue;

  return (
    <div className="space-y-4" id="admin-cabinet-center">
      <Card className="border-[#4C7CFF]/25">
        <CardHeader>
          <CardTitle className="text-base">
            {ar ? "صحة الاشتراك" : "Santé de l’abonnement"}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-slate-700">
          {!ent ? (
            <p>…</p>
          ) : (
            <>
              <p>
                <strong>{ar ? "الحالة" : "Statut"} :</strong>{" "}
                {inTrial
                  ? ar
                    ? "تجربة"
                    : "Essai"
                  : ent.status}
                {ent.trial_days_left != null
                  ? ` · ${ent.trial_days_left} ${ar ? "يوم متبقٍ" : "j. restants"}`
                  : ""}
                {pastDue
                  ? ` · ${ar ? "فشل الدفع" : "paiement échoué"}${
                      ent.past_due_days != null ? ` (${ent.past_due_days} j)` : ""
                    }`
                  : ""}
                {restricted ? (ar ? " · وصول مقيّد" : " · accès restreint") : ""}
              </p>
              <p>
                {ar ? "محامون" : "Avocats"} {u?.avocats_used ?? 0}/{u?.avocats_limit ?? "—"} ·{" "}
                {ar ? "مساعدون" : "Assistants"} {u?.assistants_used ?? 0}/
                {u?.assistants_limit ?? "—"} · {ar ? "مرافعات" : "Plaidoiries"}{" "}
                {u?.plaidoiries_used ?? 0}/{u?.plaidoiries_limit ?? "—"}
              </p>
              <div className="flex flex-wrap gap-2">
                {showRemind ? (
                  <Button type="button" size="sm" variant="outline" disabled={busy} onClick={() => void remind()}>
                    {ar ? "إرسال تذكير تسوية بالبريد" : "Envoyer un e-mail de régularisation"}
                  </Button>
                ) : null}
                <Link
                  href="#abonnement"
                  onClick={() => {
                    if (typeof window !== "undefined") {
                      window.history.replaceState(null, "", "#abonnement");
                    }
                  }}
                  className="text-sm font-medium text-[#0B1A4D] underline"
                >
                  {ar ? "الخطة والفواتير ↓" : "Plan & factures ↓"}
                </Link>
              </div>
              {inTrial ? (
                <p className="text-xs text-slate-500">
                  {ar
                    ? "أثناء التجربة لا تُنشأ فاتورة مدفوعة. تظهر الفواتير تلقائياً بعد بدء الاشتراك المدفوع."
                    : "Pendant l’essai : aucune facture payante. Les factures apparaissent automatiquement après le début de l’abonnement."}
                </p>
              ) : (
                <p className="text-xs text-slate-500">
                  {ar
                    ? "الفواتير تُنشأ عند الدفع — تظهر أدناه مع حالتها (مدفوعة / غير مدفوعة)."
                    : "Les factures sont créées au paiement — liste ci-dessous avec statut (payée / en attente)."}
                </p>
              )}
              {msg ? <p className="text-xs text-emerald-700">{msg}</p> : null}
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{ar ? "تدقيق الفريق" : "Audit équipe"}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {audit.length === 0 ? (
            <p className="text-slate-500">
              {ar
                ? "لا أحداث دعوة/إزالة حديثة."
                : "Aucun événement d’invitation / retrait récent."}
            </p>
          ) : (
            <ul className="space-y-1.5">
              {audit.map((a, i) => (
                <li key={`${a.id || a.action}-${i}`} className="text-xs text-slate-600">
                  {a.created_at ? new Date(a.created_at).toLocaleString() : ""} — {a.actor_name || "—"}{" "}
                  {a.label || a.action}
                </li>
              ))}
            </ul>
          )}
          <Link href="/team" className="inline-block text-sm font-medium text-[#0B1A4D] underline">
            {ar ? "فتح الفريق" : "Ouvrir l’équipe"}
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
