"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { useAuthStore } from "@/store/auth";
import { isAssistant } from "@/lib/roles";
import { useLocaleStore } from "@/store/locale";
import {
  clearPleaSession,
  hasMeaningfulPleaSession,
  loadPleaSession,
  pleaResumeHref,
  pleaSessionPreview,
  startFreshPleaHref,
} from "@/lib/plea-session";

function NewPlaidoirieInner() {
  const router = useRouter();
  const search = useSearchParams();
  const user = useAuthStore((s) => s.user);
  const locale = useLocaleStore((s) => s.locale);
  const uiFr = locale !== "ar";
  const forceFresh = search.get("fresh") === "1";
  const [ready, setReady] = useState(false);
  const [hasDraft, setHasDraft] = useState(false);

  const preview = useMemo(() => (ready && hasDraft ? pleaSessionPreview() : ""), [ready, hasDraft]);
  const savedLabel = useMemo(() => {
    if (!ready || !hasDraft) return "";
    const at = loadPleaSession()?.savedAt;
    if (!at) return "";
    try {
      return new Date(at).toLocaleString(uiFr ? "fr-FR" : "ar-MA", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "";
    }
  }, [ready, hasDraft, uiFr]);

  useEffect(() => {
    if (isAssistant(user?.role)) {
      router.replace("/redaction");
      return;
    }
    if (forceFresh) {
      clearPleaSession();
      router.replace("/redaction/libre?fresh=1");
      return;
    }
    setHasDraft(hasMeaningfulPleaSession());
    setReady(true);
  }, [user?.role, router, forceFresh]);

  useEffect(() => {
    if (!ready || hasDraft) return;
    router.replace("/redaction/libre?fresh=1");
  }, [ready, hasDraft, router]);

  if (isAssistant(user?.role) || !ready || !hasDraft) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-sm text-slate-500">
        …
      </div>
    );
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-xl space-y-5" dir={uiFr ? "ltr" : "rtl"} style={{ paddingTop: 12 }}>
        <div>
          <div className="section-title" style={{ marginBottom: 6 }}>
            {uiFr ? "Nouvelle plaidoirie" : "مرافعة جديدة"}
          </div>
          <p className="section-sub" style={{ margin: 0 }}>
            {uiFr
              ? "Un brouillon est encore ouvert dans cet ordinateur. Choisissez : le reprendre, ou vraiment tout recommencer."
              : "توجد مسودة مفتوحة على هذا الجهاز. اختاروا: استئنافها أو البدء من صفحة فارغة."}
          </p>
        </div>
        <div
          className="card"
          style={{
            padding: 18,
            border: "1px solid var(--line)",
            borderRadius: 16,
            background: "rgba(255,255,255,0.9)",
          }}
        >
          <p style={{ margin: "0 0 6px", fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>
            {uiFr ? "Brouillon en cours" : "مسودة جارية"}
            {savedLabel ? ` · ${savedLabel}` : ""}
          </p>
          {preview ? (
            <p
              style={{
                margin: 0,
                fontSize: 14,
                lineHeight: 1.55,
                color: "var(--ink)",
                whiteSpace: "pre-wrap",
              }}
              dir="auto"
            >
              {preview}
            </p>
          ) : (
            <p className="section-sub" style={{ margin: 0 }}>
              {uiFr ? "Atelier commencé, sans aperçu de texte." : "ورشة بدأت دون نص للمعاينة."}
            </p>
          )}
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          <button
            type="button"
            className="chip-btn"
            onClick={() => {
              const snap = loadPleaSession();
              router.replace(pleaResumeHref(snap?.templateId || "libre"));
            }}
          >
            {uiFr ? "Reprendre ce brouillon" : "استئناف هذه المسودة"}
          </button>
          <button
            type="button"
            className="chip-btn primary"
            onClick={() => {
              router.replace(startFreshPleaHref());
            }}
          >
            {uiFr ? "Commencer une nouvelle" : "بدء مرافعة جديدة"}
          </button>
        </div>
        <p className="section-sub" style={{ margin: 0, fontSize: 12 }}>
          {uiFr
            ? "« Commencer une nouvelle » efface seulement l’atelier local. Les plaidoiries déjà enregistrées dans la liste restent."
            : "« بدء مرافعة جديدة » يمسح الورشة المحلية فقط. المرافعات المحفوظة في القائمة تبقى."}
        </p>
      </div>
    </AppShell>
  );
}

export default function NewPlaidoiriePage() {
  return (
    <Suspense fallback={<div className="flex min-h-[40vh] items-center justify-center text-sm text-slate-500">…</div>}>
      <NewPlaidoirieInner />
    </Suspense>
  );
}
