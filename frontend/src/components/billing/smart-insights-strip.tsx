"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useClientLocale } from "@/store/locale";
import { localizeInsight, type InsightLike } from "@/lib/localize-insights";

type Insight = InsightLike & { priority: number; tone: string };

const TONE: Record<string, string> = {
  urgent: "lex-app-banner lex-app-banner--urgent border-orange-300 bg-gradient-to-r from-orange-50 to-amber-50",
  warn: "lex-app-banner lex-app-banner--urgent border-amber-200 bg-amber-50/80",
  upgrade: "lex-app-banner border-[#C9A227]/50 bg-gradient-to-r from-[#F7F5F0] to-amber-50",
  security: "lex-app-banner lex-app-banner--info border-sky-200 bg-sky-50/70",
  tip: "lex-app-banner border-emerald-200/80 bg-emerald-50/50",
  info: "lex-app-banner lex-app-banner--info border-slate-200 bg-white",
};

/** Idées intelligentes contextuelles (activation / rétention / sécurité). */
export function SmartInsightsStrip() {
  const ar = useClientLocale() === "ar";
  const user = useAuthStore((s) => s.user);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [dismissed, setDismissed] = useState<string[]>([]);

  useEffect(() => {
    if (!user || user.role === "admin_webvoice") return;
    let cancelled = false;
    try {
      const raw = sessionStorage.getItem("lexhub_insights_dismissed");
      if (raw) setDismissed(JSON.parse(raw) as string[]);
    } catch {
      /* ignore */
    }
    api
      .getBillingInsights()
      .then((r) => {
        if (!cancelled) setInsights((r.insights || []) as Insight[]);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [user?.id, user?.role]);

  const skip = new Set([
    "trial_countdown",
    "free_upgrade",
    "quota_plea",
    "seats_avocat",
    "seats_assistant",
  ]);
  const visible = insights
    .filter((i) => !dismissed.includes(i.id) && !skip.has(i.id))
    .filter((i) => i.tone === "urgent" || i.tone === "warn")
    .filter((i) => i.id !== "first_plea")
    .slice(0, 1)
    .map((i) => localizeInsight(i, ar) as Insight);
  if (!visible.length) return null;

  const dismiss = (id: string) => {
    const next = [...dismissed, id];
    setDismissed(next);
    try {
      sessionStorage.setItem("lexhub_insights_dismissed", JSON.stringify(next));
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="mx-4 mt-2 space-y-2 sm:mx-6" dir={ar ? "rtl" : "ltr"}>
      {visible.map((tip) => (
        <div
          key={tip.id}
          className={`flex flex-wrap items-center justify-between gap-2 rounded-xl border px-4 py-2.5 text-sm shadow-sm ${TONE[tip.tone] || TONE.info}`}
        >
          <div className="lex-app-banner__body min-w-0 flex-1">
            <p className="font-semibold">{tip.title}</p>
            <p className="lex-app-banner__muted text-xs text-slate-600 sm:text-sm">{tip.body}</p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Link
              href={tip.href}
              className="lex-app-banner__cta rounded-lg bg-sanad-navy px-3 py-1.5 text-xs font-semibold text-white hover:bg-sanad-navy/90"
            >
              {tip.cta}
            </Link>
            <button
              type="button"
              aria-label={ar ? "إخفاء" : "Masquer"}
              className="lex-app-banner__dismiss rounded px-2 py-1 text-xs text-slate-500 hover:bg-black/5"
              onClick={() => dismiss(tip.id)}
            >
              ✕
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
