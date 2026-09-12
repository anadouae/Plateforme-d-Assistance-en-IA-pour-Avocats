"use client";

import Link from "next/link";
import { Shield } from "lucide-react";
import { LexProductModal } from "@/components/billing/lex-product-modal";

type Props = {
  open: boolean;
  onClose: () => void;
  ar: boolean;
};

/** Assistant / avocat : l'abonnement n'est pas à eux — prévenir l'admin. */
export function AskAdminBillingModal({ open, onClose, ar }: Props) {
  return (
    <LexProductModal
      open={open}
      onClose={onClose}
      zIndexClass="z-[80]"
      tag={ar ? "الاشتراك" : "Abonnement"}
      title={
        ar
          ? "فقط مسؤول المكتب يمكنه الدفع"
          : "Seul le responsable du cabinet peut payer"
      }
      points={
        ar
          ? [
              "من أنشأ مساحة المكتب يدير التجربة والاشتراك والفاتورة",
              "المساعد والمحامي يريان الحصص — دون بطاقة ولا تغيير للخطة",
              "اطلبوا من المسؤول فتح الإعدادات ← الاشتراك",
            ]
          : [
              "Qui a créé l’espace cabinet gère l’essai, l’abonnement et la facture",
              "L’assistant et l’avocat voient les quotas — sans carte ni changement de plan",
              "Demandez au responsable d’ouvrir Paramètres → Abonnement",
            ]
      }
      primaryLabel={ar ? "حسنًا" : "Compris"}
      onPrimary={onClose}
      secondaryLabel={ar ? "العودة للمساحة" : "Retour à mon espace"}
      onSecondary={() => {
        onClose();
        window.location.assign("/dashboard");
      }}
      closeLabel={ar ? "إغلاق" : "Fermer"}
    />
  );
}

export function BillingOwnerGate({ ar }: { ar: boolean }) {
  return (
    <div className="mx-auto max-w-lg rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-[#1B3F9C]/10">
        <Shield className="h-6 w-6 text-[#1B3F9C]" />
      </div>
      <h1 className="mt-4 font-display text-2xl font-semibold text-[#0A1228]">
        {ar ? "الدفع مخصص لمسؤول المكتب" : "Paiement réservé au responsable"}
      </h1>
      <p className="mt-3 text-sm leading-relaxed text-slate-600">
        {ar
          ? "فقط من أنشأ مساحة المكتب (مسؤول المكتب) يمكنه بدء تجربة أو تغيير الخطة. أخبروه بفتح الإعدادات ← الاشتراك."
          : "Seul celui qui a créé l’espace cabinet (admin) peut démarrer un essai ou changer de plan. Demandez-lui d’ouvrir Paramètres → Abonnement."}
      </p>
      <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-center">
        <Link
          href="/settings#abonnement"
          className="inline-flex items-center justify-center rounded-xl bg-[#1B3F9C] px-4 py-2.5 text-sm font-semibold text-white"
        >
          {ar ? "الإعدادات" : "Paramètres"}
        </Link>
        <Link
          href="/dashboard"
          className="inline-flex items-center justify-center rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700"
        >
          {ar ? "لوحة التحكم" : "Tableau de bord"}
        </Link>
      </div>
    </div>
  );
}
