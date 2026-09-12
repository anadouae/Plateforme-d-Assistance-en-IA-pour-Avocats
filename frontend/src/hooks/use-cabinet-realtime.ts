"use client";

import { useEffect, useRef } from "react";
import { getApiBase } from "@/lib/api";

const EVENT = "lexhub-cabinet-event";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("lexhub_token") || sessionStorage.getItem("sanad_token") || localStorage.getItem("lexhub_token") || localStorage.getItem("sanad_token");
}

/** Sync multi-onglets / multi-navigateurs via WebSocket Redis. */
export function useCabinetRealtime(enabled = true) {
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    let timer = 0;

    function connect() {
      const token = getToken();
      if (!token || cancelled) return;
      const base = getApiBase().replace(/^http/, "ws");
      const url = `${base}/api/ws/cabinet?token=${encodeURIComponent(token)}`;
      try {
        const ws = new WebSocket(url);
        wsRef.current = ws;
        ws.onopen = () => {
          retryRef.current = 0;
        };
        ws.onmessage = (ev) => {
          try {
            const data = JSON.parse(String(ev.data));
            window.dispatchEvent(new CustomEvent(EVENT, { detail: data }));
          } catch {
            /* ignore */
          }
        };
        ws.onclose = () => {
          wsRef.current = null;
          if (cancelled) return;
          const delay = Math.min(15000, 1200 * 2 ** Math.min(retryRef.current, 4));
          retryRef.current += 1;
          timer = window.setTimeout(connect, delay);
        };
        ws.onerror = () => {
          try {
            ws.close();
          } catch {
            /* ignore */
          }
        };
      } catch {
        timer = window.setTimeout(connect, 4000);
      }
    }

    connect();
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
      try {
        wsRef.current?.close();
      } catch {
        /* ignore */
      }
    };
  }, [enabled]);
}

export function useCabinetEvent(handler: (data: { event?: string; payload?: unknown }) => void) {
  const handlerRef = useRef(handler);
  handlerRef.current = handler;
  useEffect(() => {
    const on = (e: Event) => handlerRef.current((e as CustomEvent).detail || {});
    window.addEventListener(EVENT, on);
    return () => window.removeEventListener(EVENT, on);
  }, []);
}
