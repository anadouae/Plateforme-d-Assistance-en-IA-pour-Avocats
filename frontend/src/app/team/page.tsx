"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";

/** Ancienne route /team → الإعدادات > الفريق */
export default function TeamRedirectPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/settings?tab=team");
  }, [router]);

  return (
    <AppShell>
      <p className="text-sm text-slate-500" dir="rtl">
        جارٍ التوجيه إلى الإعدادات…
      </p>
    </AppShell>
  );
}
