"use client";

import { LexHubPageLoader } from "@/components/brand/lexhub-page-loader";

/** Même markup que AppShell BootScreen — évite mismatch Suspense. */
export default function Loading() {
  return (
    <div className="sanad-boot-overlay" suppressHydrationWarning>
      <LexHubPageLoader />
    </div>
  );
}
