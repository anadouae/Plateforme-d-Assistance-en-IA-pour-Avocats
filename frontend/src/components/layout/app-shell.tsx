"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { useClientLocale, useTranslations } from "@/store/locale";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { LanguageSwitch } from "@/components/layout/language-switch";
import { UserAccountMenu } from "@/components/layout/user-account-menu";
import { TopbarActionIcons } from "@/components/layout/topbar-action-icons";
import { CommandPalette } from "@/components/layout/command-palette";
import { SubscriptionBanner } from "@/components/billing/subscription-banner";
import { SmartInsightsStrip } from "@/components/billing/smart-insights-strip";
import { PlansNudgeModal } from "@/components/billing/plans-nudge-modal";
import { ReferralNudgeModal } from "@/components/billing/referral-nudge-modal";
import { CreditSpendHost } from "@/components/billing/credit-spend-toast";
import { QuotaGuidanceHost } from "@/components/billing/quota-guidance-host";
import { ActionToastHost } from "@/components/ui/action-toast-host";
import { LexHubPageLoader } from "@/components/brand/lexhub-page-loader";
import { LexHubOnboarding } from "@/components/onboarding/lexhub-onboarding";
import { ProfileCompletionModal } from "@/components/onboarding/profile-completion-modal";
import { PageTransition } from "@/components/motion/page-transition";
import { useOnboardingTour } from "@/hooks/use-onboarding";
import { getUiDensity, getUiTheme } from "@/hooks/use-ui-prefs";
import { workspaceRoleLabel } from "@/lib/i18n/labels";
import { useCabinetRealtime } from "@/hooks/use-cabinet-realtime";
import { api } from "@/lib/api";

function AmbientBlobs() {
  return (
    <div className="blobs" aria-hidden suppressHydrationWarning>
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

function BootScreen() {
  return (
    <div className="sanad-boot-overlay" suppressHydrationWarning>
      <LexHubPageLoader />
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const t = useTranslations().app;
  const locale = useClientLocale();
  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.token);
  /** Toujours false au SSR et au 1er paint → arbre identique. */
  const [mounted, setMounted] = useState(false);
  const [routeBusy, setRouteBusy] = useState(false);
  const firstPath = useRef(true);
  const { open: tourOpen, complete: completeTour } = useOnboardingTour();
  const [cabinetLogo, setCabinetLogo] = useState<string | null>(null);
  useCabinetRealtime(!!token || !!user);

  useEffect(() => {
    setMounted(true);
    document.documentElement.dataset.density = getUiDensity();
    document.documentElement.dataset.theme = getUiTheme();
    void useAuthStore.persist.rehydrate().then(() => {
      if (useAuthStore.persist.hasHydrated()) {
        useAuthStore.getState().setHasHydrated(true);
      }
    });
  }, []);

  useEffect(() => {
    if (!mounted) return;
    if (firstPath.current) {
      firstPath.current = false;
      return;
    }
    setRouteBusy(true);
    const tmr = window.setTimeout(() => setRouteBusy(false), 380);
    return () => window.clearTimeout(tmr);
  }, [pathname, mounted]);

  useEffect(() => {
    if (!mounted || !user?.cabinet_has_logo) {
      setCabinetLogo(null);
      return;
    }
    let cancelled = false;
    api
      .getCabinetLogoDataUrl()
      .then((url) => {
        if (!cancelled) setCabinetLogo(url);
      })
      .catch(() => {
        if (!cancelled) setCabinetLogo(null);
      });
    return () => {
      cancelled = true;
    };
  }, [mounted, user?.cabinet_has_logo, user?.cabinet_name]);

  useEffect(() => {
    if (!mounted) return;
    const ok =
      !!useAuthStore.getState().token ||
      !!localStorage.getItem("lexhub_token") || localStorage.getItem("sanad_token") ||
      !!sessionStorage.getItem("lexhub_token") || sessionStorage.getItem("sanad_token");
    if (!ok) {
      router.replace("/login");
      return;
    }
    if (useAuthStore.getState().user?.role === "admin_webvoice" && !pathname.startsWith("/admin")) {
      router.replace("/admin");
    }
  }, [mounted, token, router, pathname]);

  if (!mounted) {
    return <BootScreen />;
  }

  const displayName = user?.full_name?.trim() || "—";
  const greeting = locale === "ar" ? "أهلاً بك" : "Bienvenue";
  const cabinetName =
    (locale === "ar" && user?.cabinet_name_ar) ||
    user?.cabinet_name ||
    (locale === "ar" ? "المكتب" : "Cabinet");

  return (
    <>
      <GooFilter />
      <AmbientBlobs />
      <div className="shell" dir={locale === "ar" ? "rtl" : "ltr"} suppressHydrationWarning>
        <AppSidebar />
        <div className="main">
          <header className="topbar">
            <div className="topbar-identity">
              <div className="greeting">
                {greeting} <b>{displayName}</b>
              </div>
              <div className="topbar-workspace-role">{workspaceRoleLabel(user?.role, locale)}</div>
              <div className="topbar-cabinet" title={cabinetName}>
                {cabinetLogo ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={cabinetLogo} alt="" className="topbar-cabinet__logo" />
                ) : (
                  <span className="topbar-cabinet__mark" aria-hidden>
                    {cabinetName.slice(0, 1).toUpperCase()}
                  </span>
                )}
                <span className="topbar-cabinet__name">{cabinetName}</span>
              </div>
            </div>
            <div
              className="lang-toggle"
              style={{ display: "flex", alignItems: "center", gap: 12 }}
            >
              <TopbarActionIcons />
              <div data-tour-id="lang-toggle">
                <LanguageSwitch />
              </div>
              <UserAccountMenu />
            </div>
          </header>
          <div className="main-scroll">
            <SubscriptionBanner />
            <SmartInsightsStrip />
            <div className="panel show">
              <PageTransition>{children}</PageTransition>
            </div>
          </div>
        </div>
      </div>
      {routeBusy ? (
        <div className="sanad-route-bar" aria-hidden>
          <span />
        </div>
      ) : null}
      <LexHubOnboarding open={tourOpen} onComplete={() => void completeTour()} />
      <ProfileCompletionModal />
      <PlansNudgeModal />
      <ReferralNudgeModal />
      <CommandPalette />
      <CreditSpendHost />
      <QuotaGuidanceHost />
      <ActionToastHost />
    </>
  );
}
