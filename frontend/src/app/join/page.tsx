"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/** Ancienne route « code cabinet » : l’entrée se fait uniquement par invitation e-mail. */
export default function JoinRedirectPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/login");
  }, [router]);
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F4F6FA]">
      <p className="text-sm text-[#0A1228]">Redirection…</p>
    </div>
  );
}
