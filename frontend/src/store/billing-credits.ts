"use client";

import { create } from "zustand";
import { api, type BillingEntitlements } from "@/lib/api";

export type CreditToastKind = "spend" | "low" | "empty" | "daily" | "daily-empty";

export type CreditToast = {
  id: string;
  kind: CreditToastKind;
  delta: number;
  remaining: number | null;
  limit: number | null;
  label: string;
  dailyRemaining?: number | null;
  dailyLimit?: number | null;
};

type BillingCreditsState = {
  entitlements: BillingEntitlements | null;
  toasts: CreditToast[];
  loading: boolean;
  refresh: () => Promise<BillingEntitlements | null>;
  notifySpend: (action: string, label?: string) => Promise<void>;
  dismiss: (id: string) => void;
};

const ACTION_LABELS: Record<string, string> = {
  polish: "Correction de forme",
  ask: "Question document",
  clarify: "Questions de clarification",
  synthesis: "Synthèse document",
  summarize: "Résumé",
  revise: "Révision plaidoirie",
  analyse: "Analyse dossier",
  cle_de_barre: "Clé de barre",
  compose: "Rédaction plaidoirie",
};

let seq = 0;

export const useBillingCredits = create<BillingCreditsState>((set, get) => ({
  entitlements: null,
  toasts: [],
  loading: false,

  refresh: async () => {
    set({ loading: true });
    try {
      const ent = await api.getBillingEntitlements();
      set({ entitlements: ent, loading: false });
      return ent;
    } catch {
      set({ loading: false });
      return null;
    }
  },

  dismiss: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),

  notifySpend: async (action, label) => {
    const costs = get().entitlements?.ai_credit_costs || {};
    let delta = Number(costs[action] ?? 0);
    if (!delta || delta < 0) {
      // fallback known costs if entitlements not loaded yet
      const fallback: Record<string, number> = {
        polish: 1,
        ask: 2,
        clarify: 3,
        synthesis: 4,
        summarize: 4,
        revise: 5,
        analyse: 8,
        cle_de_barre: 8,
        compose: 10,
      };
      delta = fallback[action] ?? 0;
    }

    const before = get().entitlements;
    const beforeRem =
      before?.usage?.ai_credits_limit != null && before.usage.ai_credits_limit >= 0
        ? Math.max(0, (before.usage.ai_credits_limit || 0) - (before.usage.ai_credits_used || 0))
        : null;

    const ent = await get().refresh();
    const used = ent?.usage?.ai_credits_used ?? 0;
    const lim = ent?.usage?.ai_credits_limit ?? -1;
    const remaining = lim < 0 ? null : Math.max(0, lim - used);
    const dailyLim = ent?.ai_daily_limit ?? 0;
    const dailyUsed = ent?.ai_daily_used ?? 0;
    const dailyRemaining = dailyLim > 0 ? Math.max(0, dailyLim - dailyUsed) : null;
    const id = `c${Date.now()}-${++seq}`;
    const title = label || ACTION_LABELS[action] || action;

    if (delta > 0) {
      set((s) => ({
        toasts: [
          ...s.toasts,
          {
            id,
            kind: "spend",
            delta,
            remaining,
            limit: lim < 0 ? null : lim,
            label: title,
            dailyRemaining,
            dailyLimit: dailyLim > 0 ? dailyLim : null,
          },
        ],
      }));
      window.setTimeout(() => get().dismiss(id), 4200);
    }

    // Friendly low-credit warning (~15% left or < 15 credits)
    if (remaining != null && lim > 0) {
      const pctLeft = remaining / Math.max(lim, 1);
      const crossedLow =
        remaining <= 15 ||
        pctLeft <= 0.15 ||
        (beforeRem != null && beforeRem > 15 && remaining <= 15);
      if (crossedLow && remaining > 0) {
        const lid = `${id}-low`;
        set((s) => ({
          toasts: [
            ...s.toasts,
            {
              id: lid,
              kind: "low",
              delta: 0,
              remaining,
              limit: lim,
              label: "Solde crédits bas",
            },
          ],
        }));
        window.setTimeout(() => get().dismiss(lid), 6500);
      } else if (remaining === 0) {
        const eid = `${id}-empty`;
        set((s) => ({
          toasts: [
            ...s.toasts,
            {
              id: eid,
              kind: "empty",
              delta: 0,
              remaining: 0,
              limit: lim,
              label: "Crédits épuisés",
            },
          ],
        }));
        window.setTimeout(() => get().dismiss(eid), 7000);
      }
    }

    if (dailyRemaining != null && dailyLim > 0) {
      if (dailyRemaining === 0) {
        const did = `${id}-day-empty`;
        set((s) => ({
          toasts: [
            ...s.toasts,
            {
              id: did,
              kind: "daily-empty",
              delta: 0,
              remaining,
              limit: lim < 0 ? null : lim,
              label: "Limite du jour",
              dailyRemaining: 0,
              dailyLimit: dailyLim,
            },
          ],
        }));
        window.setTimeout(() => get().dismiss(did), 8000);
      } else if (dailyRemaining / dailyLim <= 0.2 || dailyRemaining <= 8) {
        const did = `${id}-day`;
        set((s) => ({
          toasts: [
            ...s.toasts,
            {
              id: did,
              kind: "daily",
              delta: 0,
              remaining,
              limit: lim < 0 ? null : lim,
              label: "Usage du jour",
              dailyRemaining,
              dailyLimit: dailyLim,
            },
          ],
        }));
        window.setTimeout(() => get().dismiss(did), 6500);
      }
    }
  },
}));
