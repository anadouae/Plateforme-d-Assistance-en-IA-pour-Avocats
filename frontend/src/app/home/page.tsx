"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { LexHubPageLoader } from "@/components/brand/lexhub-page-loader";

/** /home → dashboard. Pas d’AppShell ici (évite l’erreur d’hydratation). */
export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const t = window.setTimeout(() => {
      router.replace("/dashboard");
    }, 520);
    return () => window.clearTimeout(t);
  }, [router]);

  return (
    <div className="sanad-boot-overlay" suppressHydrationWarning>
      <LexHubPageLoader />
    </div>
  );
}
