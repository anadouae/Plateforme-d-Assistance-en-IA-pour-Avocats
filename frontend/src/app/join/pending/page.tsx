"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Clock3 } from "lucide-react";
import { Suspense } from "react";
import { AuthLayout } from "@/components/auth/auth-layout";
import { Button } from "@/components/ui/button";
import { useLocaleStore, useTranslations } from "@/store/locale";

function PendingContent() {
  const auth = useTranslations().auth;
  const locale = useLocaleStore((s) => s.locale);
  const from = useSearchParams().get("from");
  const isRegister = from === "register";

  const title = isRegister ? auth.registerPendingTitle : auth.joinPendingTitle;
  const desc = isRegister ? auth.registerPendingDesc : auth.joinPendingDesc;

  return (
    <AuthLayout hideSideBadge>
      <div
        dir={locale === "ar" ? "rtl" : "ltr"}
        className="rounded-3xl border border-white/50 bg-white/95 p-8 text-center shadow-royal"
      >
        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-amber-50 text-amber-700">
          <Clock3 className="h-8 w-8" />
        </div>
        <h1 className="font-serif text-2xl font-semibold text-[#0B1A4D]">{title}</h1>
        <p className="mx-auto mt-3 max-w-sm text-sm leading-relaxed text-slate-600">{desc}</p>
        <Link href="/login" className="mt-8 inline-block">
          <Button type="button">{auth.joinBackLogin}</Button>
        </Link>
      </div>
    </AuthLayout>
  );
}

export default function JoinPendingPage() {
  return (
    <Suspense fallback={null}>
      <PendingContent />
    </Suspense>
  );
}
