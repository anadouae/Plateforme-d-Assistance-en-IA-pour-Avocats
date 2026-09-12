"use client";

import Link from "next/link";
import { LexProductModal } from "@/components/billing/lex-product-modal";

type Props = {
  open: boolean;
  ar: boolean;
  planName: string;
  trialDays: number;
  invoiceNumber?: string;
  invoiceHtml?: string;
  onClose: () => void;
};

export function PaymentSuccessModal({
  open,
  ar,
  planName,
  trialDays,
  invoiceNumber,
  invoiceHtml,
  onClose,
}: Props) {
  function openInvoice() {
    if (!invoiceHtml) return;
    const w = window.open("", "_blank");
    if (!w) return;
    w.document.write(invoiceHtml);
    w.document.close();
  }

  return (
    <LexProductModal
      open={open}
      onClose={onClose}
      zIndexClass="z-[90]"
      tag={ar ? "تم التفعيل" : "Activé"}
      title={ar ? "تم تفعيل التجربة!" : "Essai activé !"}
      points={[
        ar
          ? `خطة ${planName} · ${trialDays} يومًا مجانًا · 0 درهم اليوم`
          : `Plan ${planName} · ${trialDays} jours gratuits · 0 MAD aujourd'hui`,
        ar
          ? "ألغوا قبل نهاية التجربة إذا لم ترغبوا في الاشتراك"
          : "Résiliez avant la fin de l’essai si vous ne souhaitez pas l’abonnement",
        invoiceNumber
          ? ar
            ? `إيصال التجربة : ${invoiceNumber}`
            : `Reçu d’essai : ${invoiceNumber}`
          : ar
            ? "اشتراككم جاهز في الإعدادات"
            : "Votre abonnement est prêt dans les paramètres",
      ]}
      primaryLabel={ar ? "عرض اشتراكي" : "Voir mon abonnement"}
      primaryHref="/settings#abonnement"
      secondaryLabel={ar ? "الذهاب للوحة التحكم" : "Aller au tableau de bord"}
      onSecondary={() => {
        onClose();
        window.location.assign("/dashboard");
      }}
      closeLabel={ar ? "إغلاق" : "Fermer"}
    >
      {invoiceHtml ? (
        <button
          type="button"
          className="self-start text-left text-sm text-[#5a8bff] underline"
          onClick={openInvoice}
        >
          {ar ? "معاينة الإيصال" : "Aperçu du reçu"}
        </button>
      ) : null}
    </LexProductModal>
  );
}
