"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { TeamPanel } from "@/components/settings/team-panel";
import { canManageTeam } from "@/lib/roles";
import { useAuthStore } from "@/store/auth";
import { useClientLocale, useTranslations } from "@/store/locale";

export default function TeamPage() {
  const router = useRouter();
  const role = useAuthStore((s) => s.user?.role);
  const hasHydrated = useAuthStore((s) => s._hasHydrated);
  const locale = useClientLocale();
  const ar = locale === "ar";
  const t = useTranslations().app.team;
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!hasHydrated) return;
    if (!canManageTeam(role)) {
      router.replace("/dashboard");
      return;
    }
    setReady(true);
  }, [hasHydrated, role, router]);

  if (!hasHydrated || !ready) {
    return (
      <AppShell>
        <div className="flex min-h-[30vh] items-center justify-center text-sm text-slate-500">…</div>
      </AppShell>
    );
  }

  if (!canManageTeam(role)) {
    return null;
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-2xl space-y-6" dir={ar ? "rtl" : "ltr"}>
        <div>
          <h1 className="text-2xl font-bold text-sanad-slate">{t.title}</h1>
          <p className="mt-1 text-sm text-slate-500">{t.subtitle}</p>
        </div>
        <TeamPanel />
      </div>
    </AppShell>
  );
}
