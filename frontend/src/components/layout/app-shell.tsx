"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { useLocaleStore, useTranslations } from "@/store/locale";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { LanguageSwitch } from "@/components/layout/language-switch";

function AmbientBlobs() {
  return (
    <div className="blobs" aria-hidden>
      <div className="blob b1" />
      <div className="blob b2" />
      <div className="blob b3" />
    </div>
  );
}

function GooFilter() {
  return (
    <svg width="0" height="0" aria-hidden style={{ position: "absolute" }}>
      <filter id="goo">
        <feGaussianBlur in="SourceGraphic" stdDeviation="7" result="b" />
        <feColorMatrix
          in="b"
          mode="matrix"
          values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 20 -9"
        />
      </filter>
    </svg>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const t = useTranslations().app;
  const locale = useLocaleStore((s) => s.locale);
  const user = useAuthStore((s) => s.user);
  const hasHydrated = useAuthStore((s) => s._hasHydrated);
  const token = useAuthStore((s) => s.token);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (useAuthStore.persist.hasHydrated()) {
      useAuthStore.getState().setHasHydrated(true);
    }
  }, []);

  useEffect(() => {
    if (!mounted || !hasHydrated) return;
    const ok =
      !!token ||
      (typeof window !== "undefined" && !!localStorage.getItem("sanad_token"));
    if (!ok) {
      router.replace("/login");
      return;
    }
    const role = useAuthStore.getState().user?.role;
    if (role === "admin_webvoice" && !pathname.startsWith("/admin")) {
      router.replace("/admin");
    }
  }, [mounted, hasHydrated, token, router, pathname]);

  if (!mounted || !hasHydrated) {
    return (
      <>
        <AmbientBlobs />
        <div className="shell" style={{ placeItems: "center" }}>
          <p style={{ gridColumn: "1 / -1", color: "var(--ink-soft)" }}>{t.loading}</p>
        </div>
      </>
    );
  }

  const ok =
    !!token ||
    (typeof window !== "undefined" && !!localStorage.getItem("sanad_token"));
  if (!ok) {
    return (
      <>
        <AmbientBlobs />
        <div className="shell" style={{ placeItems: "center" }}>
          <p style={{ gridColumn: "1 / -1", color: "var(--ink-soft)" }}>{t.loading}</p>
        </div>
      </>
    );
  }

  const firstName = user?.full_name?.trim().split(/\s+/)[0] || "—";
  const greeting = locale === "ar" ? "مرحباً" : "Bonjour";

  return (
    <>
      <GooFilter />
      <AmbientBlobs />
      <div className="shell" dir={locale === "ar" ? "rtl" : "ltr"}>
        <AppSidebar />
        <div className="main">
          <div className="topbar">
            <div className="greeting">
              {greeting} <b>{firstName}</b>
            </div>
            <div className="lang-toggle">
              <LanguageSwitch />
            </div>
          </div>
          <div key={pathname} className="panel show">
            {children}
          </div>
        </div>
      </div>
    </>
  );
}
