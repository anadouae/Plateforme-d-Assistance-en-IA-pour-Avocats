"use client";

import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { postAuthPath } from "@/lib/billing-intent";
import { useClientLocale } from "@/store/locale";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (cfg: Record<string, unknown>) => void;
          renderButton: (el: HTMLElement, cfg: Record<string, unknown>) => void;
        };
      };
    };
  }
}

const CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

/** Bouton Google — visible seulement si client id configuré. */
export function GoogleSignInButton({ onError }: { onError?: (msg: string) => void }) {
  const ar = useClientLocale() === "ar";
  const setAuth = useAuthStore((s) => s.setAuth);
  const ref = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!CLIENT_ID || !ref.current) return;
    let cancelled = false;

    async function onCredential(response: { credential?: string }) {
      if (!response.credential) return;
      try {
        const data = await api.googleLogin(response.credential);
        setAuth(data, { remember: true });
        window.location.assign(postAuthPath(data.user.role));
      } catch (e) {
        onError?.(e instanceof ApiError ? e.message : ar ? "فشل دخول Google" : "Échec Google");
      }
    }

    function boot() {
      if (cancelled || !window.google?.accounts?.id || !ref.current) return;
      window.google.accounts.id.initialize({
        client_id: CLIENT_ID,
        callback: onCredential,
      });
      ref.current.innerHTML = "";
      window.google.accounts.id.renderButton(ref.current, {
        theme: "outline",
        size: "large",
        width: 320,
        text: "continue_with",
        shape: "pill",
      });
      setReady(true);
    }

    if (window.google?.accounts?.id) {
      boot();
      return;
    }
    const s = document.createElement("script");
    s.src = "https://accounts.google.com/gsi/client";
    s.async = true;
    s.onload = () => boot();
    document.head.appendChild(s);
    return () => {
      cancelled = true;
    };
  }, [ar, onError, setAuth]);

  if (!CLIENT_ID) return null;

  return (
    <div className="mt-4 space-y-2">
      <div className="relative flex items-center gap-3 text-[11px] uppercase tracking-wide text-slate-400">
        <span className="h-px flex-1 bg-slate-200" />
        {ar ? "أو" : "ou"}
        <span className="h-px flex-1 bg-slate-200" />
      </div>
      <div ref={ref} className="flex justify-center min-h-[44px]" />
      {!ready ? (
        <p className="text-center text-xs text-slate-400">
          {ar ? "تحميل Google…" : "Chargement Google…"}
        </p>
      ) : null}
    </div>
  );
}
