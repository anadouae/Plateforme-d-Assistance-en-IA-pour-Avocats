"use client";

import { Download, Eye, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, ApiError } from "@/lib/api";

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
  paid_mock: "Payée",
  draft: "Brouillon",
  pending: "En attente",
  open: "Ouverte",
  issued_mock: "Émise",
  issued: "Émise",
};

function statusLabel(status: string) {
  const k = (status || "").toLowerCase();
  return STATUS_FR[k] || status || "—";
}

function isPaid(status: string) {
  const k = (status || "").toLowerCase();
  return k.includes("paid") || k === "payée" || k === "payee" || k.includes("issued");
}

/** Uniquement les factures payantes (> 0 MAD) — pas les reçus d’essai à 0. */
function isPayableInvoice(inv: InvoiceRow) {
  if (Number(inv.amount_mad || 0) <= 0) return false;
  if (inv.kind === "trial_receipt") return false;
  const st = (inv.status || "").toLowerCase();
  if (st.includes("trial") || st.includes("essai")) return false;
  return true;
}

async function openPreview(id: string) {
  const inv = await api.getBillingInvoice(id);
  const w = window.open("", "_blank");
  if (!w || !inv.html) throw new Error("Impossible d’ouvrir la facture");
  w.document.write(inv.html);
  w.document.close();
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
  const visible = invoices.filter(isPayableInvoice);

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

  if (!visible.length) {
    return (
      <p className="text-xs text-slate-500">
        {emptyHint ||
          (ar
            ? "لا فواتير مدفوعة بعد. تظهر هنا فقط الأشهر المدفوعة (بدون فواتير بـ 0 درهم)."
            : "Aucune facture payante pour l’instant. Seuls les mois payés (> 0 MAD) apparaissent ici.")}
      </p>
    );
  }

  return (
    <ul className={compact ? "space-y-1.5" : "space-y-2"}>
      {visible.map((inv) => {
        const busy = busyId === inv.id || busyId === `pdf-${inv.id}`;
        return (
          <li
            key={inv.id}
            className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2.5"
          >
            <div className="min-w-0 flex items-start gap-2">
              <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-800">
                <FileText className="h-4 w-4" />
              </span>
              <div className="min-w-0">
                <p className="truncate font-semibold text-[#0B1A4D]">{inv.number}</p>
                <p className="text-[11px] text-slate-500">
                  {ar ? "فاتورة" : "Facture"}
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
                onClick={() => void run(inv.id, () => openPreview(inv.id))}
              >
                <Eye className="h-3.5 w-3.5" />
                {!compact ? (ar ? "معاينة" : "Aperçu") : null}
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={busy}
                title={ar ? "تحميل PDF" : "Télécharger PDF"}
                onClick={() =>
                  void run(`pdf-${inv.id}`, () =>
                    api.downloadBillingInvoicePdf(inv.id, `LexHub-${inv.number}.pdf`),
                  )
                }
              >
                <Download className="h-3.5 w-3.5" />
                {!compact ? "PDF" : null}
              </Button>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
