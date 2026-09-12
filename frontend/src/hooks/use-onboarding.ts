"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

const RESTART_EVENT = "sanad-onboarding-restart";

/** Relance manuelle depuis Paramètres — n’efface pas le flag backend. */
export function restartOnboardingTour() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(RESTART_EVENT));
  }
}

/** Alias pour les imports existants. */
export const restartOnboarding = restartOnboardingTour;

export function useOnboardingTour() {
  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.token);
  const [ready, setReady] = useState(false);
  const [open, setOpen] = useState(false);
  const [manual, setManual] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let delayTmr = 0;

    async function boot() {
      if (!token) {
        setReady(true);
        return;
      }
      let seen = !!user?.has_seen_onboarding_tour;
      try {
        const me = await api.getMe();
        if (cancelled) return;
        useAuthStore.setState({ user: me });
        seen = !!me.has_seen_onboarding_tour;
      } catch {
        /* garde le flag du store */
      }
      if (cancelled) return;
      setReady(true);
      if (!seen) {
        delayTmr = window.setTimeout(() => {
          if (!cancelled) {
            setManual(false);
            setOpen(true);
          }
        }, 500);
      }
    }

    void boot();

    function onRestart() {
      setManual(true);
      setOpen(true);
    }
    window.addEventListener(RESTART_EVENT, onRestart);

    return () => {
      cancelled = true;
      if (delayTmr) window.clearTimeout(delayTmr);
      window.removeEventListener(RESTART_EVENT, onRestart);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- boot once per token session
  }, [token]);

  const complete = useCallback(async () => {
    setOpen(false);
    if (manual) {
      setManual(false);
      return;
    }
    try {
      const me = await api.completeOnboardingTour();
      useAuthStore.setState({ user: me });
    } catch {
      useAuthStore.setState((s) =>
        s.user ? { user: { ...s.user, has_seen_onboarding_tour: true } } : s,
      );
    }
  }, [manual]);

  return { ready, open, complete };
}

/** Alias pour AppShell. */
export const useOnboarding = useOnboardingTour;
