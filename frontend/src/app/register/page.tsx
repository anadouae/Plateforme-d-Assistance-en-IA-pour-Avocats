"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/** Ancienne route → onglet إنشاء مكتب de l'auth unifié */
export default function RegisterRedirectPage() {
  const router = useRouter();
  useEffect(() => {
    const sp = new URLSearchParams(
      typeof window !== "undefined" ? window.location.search : "",
    );
    sp.set("tab", "register");
    router.replace(`/login?${sp.toString()}`);
  }, [router]);
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F6EFDD]">
      <p className="text-sm text-[#2C3B5C]" dir="rtl">
        جارٍ التوجيه…
      </p>
    </div>
  );
}
