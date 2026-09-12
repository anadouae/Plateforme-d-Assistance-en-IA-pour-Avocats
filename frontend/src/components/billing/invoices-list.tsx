"use client";

import { Download, Eye, FileText, Receipt } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, ApiError, getAuthToken, getApiBase } from "@/lib/api";

export type InvoiceRow = {
  id: string;
  number: string;
  plan_name: string;
  amount_mad: number;
  status: string;
  issued_at?: string | null;
  kind?: string;
};

const STATUS_FR: Record<string, string> = {
  paid: "Payée",
  payee: "Payée",
  draft: "Brouillon",
  pending: "En attente",
  open: "Ouverte",
  trial: "Reçu d’essai",
  trial_confirmed: "Reçu d’essai",
};

function statusLabel(status: string) {
  const k = (status || "").toLowerCase();
  return STATUS_FR[k] || status || "—";
}

function isPaid(status: string) {
  const k = (status || "").toLowerCase();
  return k.includes("paid") || k === "payée" || k === "payee";
}

function isTrialDoc(inv: InvoiceRow) {
  return (
    inv.kind === "trial_receipt" ||
    Number(inv.amount_mad || 0) === 0 ||
    /trial|essai/i.test(inv.status || "")
  );
}

async function openHtml(id: string, print: boolean) {
  const inv = await api.getBillingInvoice(id);
  const w = window.open("", "_blank");
  if (!w || !inv.html) throw new Error("Impossible d’ouvrir la facture");
  w.document.write(inv.html);
  w.document.close();
  if (print) {
    window.setTimeout(() => {
      try {
        w.focus();
        w.print();
      } catch {
        /* ignore */
      }
    }, 350);
  }
}

async function downloadHtmlFile(id: string, number: string) {
  const token = getAuthToken();
  const res = await fetch(`${getApiBase()}/api/billing/invoices/${id}/download`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    credentials: "include",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(
      typeof body.detail === "string" ? body.detail : "Téléchargement impossible",
      res.status,
    );
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `LexHub-${number}.html`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

type Props = {
  invoices: InvoiceRow[];
  ar?: boolean;
  busyId?: string | null;
  onBusy?: (id: string | null) => void;
  onError?: (msg: string) => void;
  emptyHint?: string;
  compact?: boolean;
};

export function InvoicesList({
  invoices,
  ar = false,
  busyId = null,
  onBusy,
  onError,
  emptyHint,
  compact = false,
}: Props) {
  async function run(id: string, fn: () => Promise<void>) {
    onBusy?.(id);
    try {
      await fn();
    } catch (e) {
      onError?.(e instanceof ApiError ? e.message : e instanceof Error ? e.message : "Erreur");
    } finally {
      onBusy?.(null);
    }
  }

  if (!invoices.length) {
    return (
      <p className="text-xs text-slate-500">
        {emptyHint ||
          (ar
            ? "لا مستندات بعد. ستظهر هنا إيصالات التجربة والفواتير."
            : "Aucun document pour l’instant. Les reçus d’essai et factures apparaîtront ici.")}
      </p>
    );
  }

  return (
    <ul className={compact ? "space-y-1.5" : "space-y-2"}>
      {invoices.map((inv) => {
        const trial = isTrialDoc(inv);
        const busy = busyId === inv.id || busyId === `pdf-${inv.id}` || busyId === `dl-${inv.id}`;
        return (
          <li
            key={inv.id}
            className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2.5"
          >
            <div className="min-w-0 flex items-start gap-2">
              <span
                className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                  trial ? "bg-amber-50 text-amber-800" : "bg-emerald-50 text-emerald-800"
                }`}
              >
                {trial ? <Receipt className="h-4 w-4" /> : <FileText className="h-4 w-4" />}
              </span>
              <div className="min-w-0">
                <p className="truncate font-semibold text-[#0B1A4D]">{inv.number}</p>
                <p className="text-[11px] text-slate-500">
                  {trial
                    ? ar
                      ? "إيصال تجربة"
                      : "Reçu d’essai"
                    : ar
                      ? "فاتورة"
                      : "Facture"}
                  {" · "}
                  {inv.plan_name} · {inv.amount_mad} MAD
                  {inv.issued_at
                    ? ` · ${new Date(inv.issued_at).toLocaleDateString(ar ? "ar-MA" : "fr-FR")}`
                    : ""}
                  {" · "}
                  <span
                    className={
                      isPaid(inv.status)
                        ? "font-semibold text-emerald-700"
                        : "font-semibold text-amber-700"
                    }
                  >
                    {statusLabel(inv.status)}
                  </span>
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-1.5">
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={busy}
                title={ar ? "معاينة" : "Aperçu"}
                onClick={() => void run(inv.id, () => openHtml(inv.id, false))}
              >
                <Eye className="h-3.5 w-3.5" />
                {!compact ? (ar ? "معاينة" : "Aperçu") : null}
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={busy}
                title={ar ? "تحميل PDF (طباعة)" : "PDF (imprimer / enregistrer)"}
                onClick={() => void run(`pdf-${inv.id}`, () => openHtml(inv.id, true))}
              >
                <Download className="h-3.5 w-3.5" />
                {!compact ? "PDF" : null}
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={busy}
                title={ar ? "تحميل HTML" : "Télécharger HTML"}
                onClick={() =>
                  void run(`dl-${inv.id}`, () => downloadHtmlFile(inv.id, inv.number))
                }
              >
                {ar ? "ملف" : "Fichier"}
              </Button>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
