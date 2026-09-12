const KEY = "lexhub_checkout_draft";

export type CheckoutDraft = {
  cardholderName: string;
  cardNumber: string;
  expiry: string;
  cvc: string;
  billingAddress: string;
  billingCity: string;
  billingEmail: string;
  agreed: boolean;
};

export function readCheckoutDraft(): CheckoutDraft | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return null;
    return JSON.parse(raw) as CheckoutDraft;
  } catch {
    return null;
  }
}

export function saveCheckoutDraft(draft: CheckoutDraft) {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(draft));
  } catch {
    /* ignore */
  }
}

export function clearCheckoutDraft() {
  try {
    sessionStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}
