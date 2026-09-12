"use client";

import { useMemo, useState } from "react";
import { CreditCard, Lock } from "lucide-react";
import { CardBrandBadges } from "@/components/billing/card-brand-badges";
import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ApiError, type BillingPlan } from "@/lib/api";

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

export function PlanCheckoutModal({
  open,
  onClose,
  plan,
  cycle,
  paymentMock,
  ar,
  onSuccess,
}: {
  open: boolean;
  onClose: () => void;
  plan: BillingPlan | null;
  cycle: "monthly" | "yearly";
  paymentMock: boolean;
  ar: boolean;
  onSuccess: (message: string) => void;
}) {
  const [cardNumber, setCardNumber] = useState("");
  const [expiry, setExpiry] = useState("");
  const [cvc, setCvc] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const price = useMemo(() => {
    if (!plan) return 0;
    return cycle === "yearly" ? plan.price_mad_yearly : plan.price_mad_monthly;
  }, [plan, cycle]);

  const planTitle = plan ? (ar && plan.name_ar ? plan.name_ar : plan.name) : "";

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
    const exp = new Date(year, month);
    if (exp <= now) return ar ? "البطاقة منتهية." : "Carte expirée.";
    if (cvc.replace(/\D/g, "").length < 3) return ar ? "CVC غير صالح." : "CVC invalide.";
    return null;
  }

  async function submit() {
    if (!plan) return;
    setError("");
    const v = validateCard();
    if (v) {
      setError(v);
      return;
    }
    setBusy(true);
    try {
      const res = await api.selectBillingPlan(plan.slug, cycle, {
        name: name.trim(),
        number: cardNumber.replace(/\s/g, ""),
        exp: expiry,
        cvc,
      });
      onSuccess(res.message);
      handleClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : ar ? "خطأ في الدفع." : "Erreur de paiement.");
    } finally {
      setBusy(false);
    }
  }

  if (!plan) return null;

  const trialDays = plan.trial_days > 0 ? plan.trial_days : 30;

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title={ar ? "بدء التجربة" : "Démarrer l'essai"}
      subtitle={
        ar
          ? `${planTitle} · ${trialDays} يومًا مجانًا ثم ${price.toLocaleString("fr-FR")} MAD`
          : `${planTitle} · ${trialDays} jours gratuits, puis ${price.toLocaleString("fr-FR")} MAD / ${cycle === "yearly" ? "an" : "mois"}`
      }
      icon={<CreditCard className="h-5 w-5" />}
      className="max-w-[620px]"
      footer={
        <>
          <Button type="button" variant="outline" onClick={handleClose} disabled={busy}>
            {ar ? "إلغاء" : "Annuler"}
          </Button>
          <Button type="button" disabled={busy} onClick={() => void submit()}>
            {busy ? "…" : ar ? `بدء التجربة (${trialDays} يومًا)` : `Démarrer l'essai (${trialDays} j)`}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <div className="rounded-xl border border-slate-200 bg-[#F4F6FA] p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            {ar ? "ملخص" : "Récapitulatif"}
          </p>
          <p className="mt-1 text-lg font-semibold text-[#0A1228]">{planTitle}</p>
          <p className="text-sm text-slate-600">{plan.description}</p>
          <p className="mt-2 text-sm text-[#0A1228]">
            {ar
              ? `0 درهم اليوم · بعد ${trialDays} يومًا: `
              : `0 MAD aujourd'hui · après ${trialDays} jours : `}
            <strong>
              {price.toLocaleString("fr-FR")} MAD / {cycle === "yearly" ? (ar ? "سنة" : "an") : ar ? "شهر" : "mois"}
            </strong>
          </p>
          <p className="mt-2 text-xs text-slate-500">
            {ar
              ? "ألغِ قبل نهاية التجربة لتجنب الفوترة التلقائية."
              : "Résiliez avant la fin de l'essai pour éviter la facturation automatique."}
          </p>
        </div>

        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="flex items-center gap-2 text-xs text-slate-600">
              <Lock className="h-3.5 w-3.5" />
              {ar
                ? "بطاقة مطلوبة لبدء التجربة — CMI / PayZone"
                : "Carte requise pour démarrer l'essai — CMI / PayZone"}
            </p>
            <CardBrandBadges cardNumber={cardNumber} />
          </div>
          <Input
            placeholder={ar ? "الاسم على البطاقة" : "Nom sur la carte"}
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoComplete="cc-name"
          />
          <Input
            placeholder="4242 4242 4242 4242"
            value={cardNumber}
            onChange={(e) => setCardNumber(formatCardNumber(e.target.value))}
            inputMode="numeric"
            autoComplete="cc-number"
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              placeholder="MM/AA"
              value={expiry}
              onChange={(e) => {
                let v = e.target.value.replace(/\D/g, "").slice(0, 4);
                if (v.length >= 3) v = `${v.slice(0, 2)}/${v.slice(2)}`;
                setExpiry(v);
              }}
              inputMode="numeric"
              autoComplete="cc-exp"
            />
            <Input
              placeholder="CVC"
              value={cvc}
              onChange={(e) => setCvc(e.target.value.replace(/\D/g, "").slice(0, 4))}
              inputMode="numeric"
              autoComplete="cc-csc"
            />
          </div>
          <p className="text-[11px] text-slate-500">
            {ar
              ? "استخدم بطاقة صالحة (16 رقم) للتجربة."
              : "Utilisez une carte valide (16 chiffres) en démo."}
          </p>
        </div>

        {error ? <p className="text-sm text-red-600">{error}</p> : null}
      </div>
    </Modal>
  );
}
