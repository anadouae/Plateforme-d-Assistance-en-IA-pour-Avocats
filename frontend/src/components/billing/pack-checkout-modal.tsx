"use client";

import { useState } from "react";
import { CreditCard, Lock } from "lucide-react";
import { CardBrandBadges } from "@/components/billing/card-brand-badges";
import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";

function formatCardNumber(raw: string): string {
  const digits = raw.replace(/\D/g, "").slice(0, 16);
  return digits.replace(/(.{4})/g, "$1 ").trim();
}

function luhnOk(num: string): boolean {
  const digits = num.replace(/\D/g, "");
  if (digits.length < 13) return false;
  let sum = 0;
  let alt = false;
  for (let i = digits.length - 1; i >= 0; i--) {
    let n = parseInt(digits[i]!, 10);
    if (alt) {
      n *= 2;
      if (n > 9) n -= 9;
    }
    sum += n;
    alt = !alt;
  }
  return sum % 10 === 0;
}

export type PackCheckoutInfo = {
  purchase_id: string;
  pack_id: string;
  credits: number;
  amount_mad: number;
  unit_mad: number;
  label: string;
  expires_hint: string;
  expires_after_months: number;
};

/** Fenêtre de paiement pack — crédit UNIQUEMENT après confirmation. */
export function PackCheckoutModal({
  open,
  onClose,
  pack,
  ar,
  onSuccess,
}: {
  open: boolean;
  onClose: () => void;
  pack: PackCheckoutInfo | null;
  ar: boolean;
  onSuccess: (message: string) => void;
}) {
  const [cardNumber, setCardNumber] = useState("");
  const [expiry, setExpiry] = useState("");
  const [cvc, setCvc] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function resetFields() {
    setCardNumber("");
    setExpiry("");
    setCvc("");
    setName("");
    setError("");
  }

  function handleClose() {
    resetFields();
    onClose();
  }

  function validateCard(): string | null {
    const digits = cardNumber.replace(/\D/g, "");
    if (!name.trim()) return ar ? "اسم حامل البطاقة مطلوب." : "Nom du titulaire requis.";
    if (digits.length < 16 || !luhnOk(digits)) {
      return ar ? "رقم البطاقة غير صالح." : "Numéro de carte invalide.";
    }
    const m = expiry.match(/^(\d{2})\/(\d{2})$/);
    if (!m) return ar ? "تاريخ MM/AA غير صالح." : "Date MM/AA invalide.";
    const month = parseInt(m[1]!, 10);
    const year = 2000 + parseInt(m[2]!, 10);
    if (month < 1 || month > 12) return ar ? "شهر غير صالح." : "Mois invalide.";
    const now = new Date();
    if (new Date(year, month) <= now) return ar ? "البطاقة منتهية." : "Carte expirée.";
    if (cvc.replace(/\D/g, "").length < 3) return ar ? "CVC غير صالح." : "CVC invalide.";
    return null;
  }

  async function submit() {
    if (!pack) return;
    setError("");
    const v = validateCard();
    if (v) {
      setError(v);
      return;
    }
    setBusy(true);
    try {
      const res = await api.confirmCreditPackPayment(pack.purchase_id, {
        name: name.trim(),
        number: cardNumber.replace(/\s/g, ""),
        exp: expiry,
        cvc,
      });
      onSuccess(res.message || (ar ? "تم الدفع." : "Paiement confirmé."));
      handleClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : ar ? "خطأ في الدفع." : "Erreur de paiement.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal
      open={open && !!pack}
      onClose={handleClose}
      title={ar ? "دفع حزمة الأرصدة" : "Paiement du pack de crédits"}
    >
      {pack ? (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-[#F7F8FC] px-4 py-3 text-sm">
            <p className="font-semibold text-[#0B1A4D]">{pack.label}</p>
            <p className="mt-1 text-[#0B1A4D]">
              {pack.amount_mad} MAD · {pack.credits} {ar ? "رصيد" : "crédits"}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {ar
                ? `تنتهي صلاحية الأرصدة بعد 12 شهرًا (حوالي ${pack.expires_hint}).`
                : `Les crédits expirent 12 mois après l’achat (vers le ${pack.expires_hint}).`}
            </p>
            <p className="mt-2 text-[11px] text-slate-500">
              {ar
                ? "لا تُضاف الأرصدة إلا بعد تأكيد الدفع."
                : "Aucun crédit n’est ajouté avant confirmation du paiement."}
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Lock className="h-3.5 w-3.5" />
            {ar ? "نفس مسار الدفع مثل الاشتراك (CMI/PayZone)." : "Même parcours que l’abonnement (CMI/PayZone)."}
          </div>
          <CardBrandBadges />

          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-500">
                {ar ? "اسم حامل البطاقة" : "Titulaire"}
              </label>
              <Input value={name} onChange={(e) => setName(e.target.value)} autoComplete="cc-name" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-500">
                {ar ? "رقم البطاقة" : "Numéro de carte"}
              </label>
              <Input
                value={cardNumber}
                onChange={(e) => setCardNumber(formatCardNumber(e.target.value))}
                inputMode="numeric"
                autoComplete="cc-number"
                placeholder="XXXX XXXX XXXX XXXX"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-500">MM/AA</label>
                <Input
                  value={expiry}
                  onChange={(e) => {
                    const d = e.target.value.replace(/\D/g, "").slice(0, 4);
                    setExpiry(d.length >= 3 ? `${d.slice(0, 2)}/${d.slice(2)}` : d);
                  }}
                  autoComplete="cc-exp"
                  placeholder="MM/AA"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-500">CVC</label>
                <Input
                  value={cvc}
                  onChange={(e) => setCvc(e.target.value.replace(/\D/g, "").slice(0, 4))}
                  autoComplete="cc-csc"
                  placeholder="123"
                />
              </div>
            </div>
          </div>

          {error ? <p className="text-sm text-red-600">{error}</p> : null}

          <Button type="button" className="w-full" disabled={busy} onClick={() => void submit()}>
            <CreditCard className="mr-2 h-4 w-4" />
            {busy
              ? "…"
              : ar
                ? `تأكيد الدفع · ${pack.amount_mad} درهم`
                : `Confirmer le paiement · ${pack.amount_mad} MAD`}
          </Button>
        </div>
      ) : null}
    </Modal>
  );
}
