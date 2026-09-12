"use client";

import { LexProductModal } from "@/components/billing/lex-product-modal";

type Props = {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  ar: boolean;
  tag: string;
  title: string;
  points: string[];
  primaryLabel: string;
  secondaryLabel?: string;
  busy?: boolean;
};

/** Confirmation d’action (paiement, export, validation, résiliation). */
export function ConfirmActionModal({
  open,
  onClose,
  onConfirm,
  ar,
  tag,
  title,
  points,
  primaryLabel,
  secondaryLabel,
  busy,
}: Props) {
  return (
    <LexProductModal
      open={open}
      onClose={onClose}
      zIndexClass="z-[88]"
      tag={tag}
      title={title}
      points={points}
      primaryLabel={busy ? "…" : primaryLabel}
      onPrimary={() => {
        if (!busy) onConfirm();
      }}
      secondaryLabel={secondaryLabel || (ar ? "إلغاء" : "Annuler")}
      closeLabel={ar ? "إغلاق" : "Fermer"}
    />
  );
}
