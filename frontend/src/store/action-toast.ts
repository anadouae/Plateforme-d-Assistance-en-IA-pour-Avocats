"use client";

import { create } from "zustand";

export type ActionToastTone = "success" | "info" | "error";

type ActionToast = {
  id: string;
  message: string;
  tone: ActionToastTone;
};

type ActionToastState = {
  toasts: ActionToast[];
  push: (message: string, tone?: ActionToastTone) => void;
  dismiss: (id: string) => void;
};

export const useActionToast = create<ActionToastState>((set) => ({
  toasts: [],
  push: (message, tone = "success") => {
    const id = `t-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    set((s) => ({
      toasts: [...s.toasts.slice(-4), { id, message, tone }],
    }));
    window.setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 3200);
  },
  dismiss: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));
