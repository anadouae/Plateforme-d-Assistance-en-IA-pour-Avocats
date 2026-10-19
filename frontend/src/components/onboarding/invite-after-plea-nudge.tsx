"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Users, X } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { useClientLocale } from "@/store/locale";
import { canManageTeam } from "@/lib/roles";

const KEY = "lexhub_invite_loop_dismissed";

/**
 * Après 1ʳᵉ plaidoirie : carte compacte (pas plein écran).
 * Mobile : bottom sheet au-dessus de la nav.
 */
export function InviteAfterPleaNudge({ pleaCount }: { pleaCount: number }) {
  const user = useAuthStore((s) => s.user);
  const ar = useClientLocale() === "ar";
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!canManageTeam(user?.role)) return;
    if (pleaCount < 1) return;
    try {
      if (localStorage.getItem(KEY) === "1") return;
    } catch {
      return;
    }
    const t = window.setTimeout(() => setOpen(true), 2500);
    return () => window.clearTimeout(t);
  }, [pleaCount, user?.role]);

  if (!open) return null;

  function dismiss() {
    try {
      localStorage.setItem(KEY, "1");
    } catch {
      /* ignore */
    }
    setOpen(false);
  }

  return (
    <div
      className="pointer-events-none fixed inset-x-0 bottom-0 z-[10040] flex justify-center p-3 pb-[calc(4.5rem+env(safe-area-inset-bottom,0px))] sm:bottom-4 sm:pb-3"
      role="status"
    >
      <div
        className="pointer-events-auto w-full max-w-md rounded-2xl border border-[var(--line)] bg-white p-4 shadow-xl"
        dir={ar ? "rtl" : "ltr"}
      >
        <div className="mb-2 flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#0B1A4D] text-amber-300">
              <Users className="h-4 w-4" />
            </span>
            <h3 className="font-serif text-base text-[#0B1A4D]">
              {ar ? "ادعوا زميلاً" : "Invitez un collègue"}
            </h3>
          </div>
          <button
            type="button"
            onClick={dismiss}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"
            aria-label="Fermer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <p className="text-sm leading-relaxed text-slate-600">
          {ar
            ? "لديكم مرافعة. ادعوا مساعداً للمراجعة أو التصدير."
            : "Vous avez une plaidoirie. Invitez un assistant pour relecture / export."}
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Link
            href="/team"
            onClick={dismiss}
            className="rounded-xl bg-[#0B1A4D] px-3.5 py-2 text-sm font-semibold text-white"
          >
            {ar ? "الفريق" : "Équipe"}
          </Link>
          <button
            type="button"
            onClick={dismiss}
            className="rounded-xl border border-slate-200 px-3.5 py-2 text-sm text-slate-600"
          >
            {ar ? "لاحقاً" : "Plus tard"}
          </button>
        </div>
      </div>
    </div>
  );
}
