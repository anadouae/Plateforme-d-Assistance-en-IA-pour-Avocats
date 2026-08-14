"use client";

import Link from "next/link";
import { Clock3 } from "lucide-react";
import { AuthLayout } from "@/components/auth/auth-layout";
import { Button } from "@/components/ui/button";
import { useLocaleStore, useTranslations } from "@/store/locale";

export default function JoinPendingPage() {
  const auth = useTranslations().auth;
  const locale = useLocaleStore((s) => s.locale);

  return (
    <AuthLayout>
      <div
        dir={locale === "ar" ? "rtl" : "ltr"}
        className="rounded-3xl border border-white/50 bg-white/95 p-8 text-center shadow-royal"
      >
        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-amber-50 text-amber-700">
          <Clock3 className="h-8 w-8" />
        </div>
        <h1 className="font-serif text-2xl font-semibold text-[#0B1F4A]">
          {auth.joinPendingTitle}
        </h1>
        <p className="mx-auto mt-3 max-w-sm text-sm leading-relaxed text-slate-600">
          {auth.joinPendingDesc}
        </p>
        <Link href="/login" className="mt-8 inline-block">
          <Button type="button">{auth.joinBackLogin}</Button>
        </Link>
      </div>
    </AuthLayout>
  );
}
