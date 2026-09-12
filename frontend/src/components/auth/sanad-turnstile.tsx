"use client";

import { useEffect, useRef, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

declare global {
  interface Window {
    turnstile?: {
      render: (
        el: HTMLElement,
        opts: {
          sitekey: string;
          callback?: (token: string) => void;
          "expired-callback"?: () => void;
          "error-callback"?: () => void;
          theme?: "light" | "dark" | "auto";
          size?: "normal" | "compact" | "flexible";
          appearance?: "always" | "execute" | "interaction-only";
        },
      ) => string;
      reset: (widgetId?: string) => void;
      remove: (widgetId?: string) => void;
    };
    onSanadTurnstileLoad?: () => void;
  }
}

const SCRIPT_ID = "cf-turnstile-script";

function loadTurnstileScript(): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();
  if (window.turnstile) return Promise.resolve();
  const existing = document.getElementById(SCRIPT_ID);
  if (existing) {
    return new Promise((resolve) => {
      window.onSanadTurnstileLoad = () => resolve();
      if (window.turnstile) resolve();
    });
  }
  return new Promise((resolve, reject) => {
    window.onSanadTurnstileLoad = () => resolve();
    const script = document.createElement("script");
    script.id = SCRIPT_ID;
    script.src =
      "https://challenges.cloudflare.com/turnstile/v0/api.js?onload=onSanadTurnstileLoad&render=explicit";
    script.async = true;
    script.defer = true;
    script.onerror = () => reject(new Error("turnstile_script"));
    document.head.appendChild(script);
  });
}

export function SanadTurnstile({
  siteKey,
  onToken,
  onLoadError,
  label,
  hint,
  className,
  resetKey = 0,
}: {
  siteKey: string;
  onToken: (token: string | null) => void;
  onLoadError?: () => void;
  label: string;
  hint?: string;
  className?: string;
  /** Change to force widget reset (e.g. after failed login). */
  resetKey?: number;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const widgetIdRef = useRef<string | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    onToken(null);
    setLoadFailed(false);

    (async () => {
      try {
        await loadTurnstileScript();
        if (cancelled || !hostRef.current || !window.turnstile) return;
        if (widgetIdRef.current) {
          try {
            window.turnstile.remove(widgetIdRef.current);
          } catch {
            /* ignore */
          }
          widgetIdRef.current = null;
        }
        hostRef.current.innerHTML = "";
        widgetIdRef.current = window.turnstile.render(hostRef.current, {
          sitekey: siteKey,
          theme: "light",
          size: "flexible",
          appearance: "always",
          callback: (token) => {
            if (!cancelled) onToken(token);
          },
          "expired-callback": () => {
            if (!cancelled) onToken(null);
          },
          "error-callback": () => {
            if (!cancelled) {
              onToken(null);
              setLoadFailed(true);
              onLoadError?.();
            }
          },
        });
      } catch {
        if (!cancelled) {
          onToken(null);
          setLoadFailed(true);
          onLoadError?.();
        }
      }
    })();

    return () => {
      cancelled = true;
      if (widgetIdRef.current && window.turnstile) {
        try {
          window.turnstile.remove(widgetIdRef.current);
        } catch {
          /* ignore */
        }
        widgetIdRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reset via resetKey
  }, [siteKey, resetKey]);

  return (
    <div
      className={cn(
        "rounded-2xl border border-[#E85A00]/40 bg-gradient-to-br from-[#0B1A4D]/[0.04] to-[#E85A00]/10 p-3.5 shadow-[0_10px_28px_-18px_rgba(11,31,74,0.45)]",
        className,
      )}
    >
      <div className="mb-2.5 flex items-center gap-2">
        <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#0B1A4D] text-[#FFB07A]">
          <ShieldCheck className="h-4 w-4" />
        </span>
        <div>
          <p className="text-sm font-medium text-[#0B1A4D]">{label}</p>
          {hint ? <p className="text-[11px] text-[#2C3B5C]/80">{hint}</p> : null}
        </div>
      </div>
      <div ref={hostRef} className="min-h-[65px] overflow-hidden rounded-xl bg-white/80" />
      {loadFailed ? (
        <p className="mt-2 text-xs text-red-600">
          Captcha indisponible — vous pouvez continuer la connexion.
        </p>
      ) : null}
    </div>
  );
}

/** Alias marque LexHub (même composant). */
export const LexHubTurnstile = SanadTurnstile;
