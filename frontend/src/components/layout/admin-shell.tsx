"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import {
  Building2,
  CreditCard,
  LayoutDashboard,
  ScrollText,
  Shield,
} from "lucide-react";
import { LanguageSwitch } from "@/components/layout/language-switch";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { UserAccountMenu } from "@/components/layout/user-account-menu";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";
import { useLocaleStore, useTranslations } from "@/store/locale";
import { useIsMobile } from "@/hooks/use-is-mobile";

const adminNavDefs = [
  { href: "/admin", key: "overview" as const, icon: LayoutDashboard },
  { href: "/admin/cabinets", key: "cabinets" as const, icon: Building2 },
  { href: "/admin/plans", key: "plans" as const, icon: CreditCard },
  { href: "/admin/logs", key: "logs" as const, icon: ScrollText },
];

export function AdminShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated } = useAuthStore();
  const locale = useLocaleStore((s) => s.locale);
  const allT = useTranslations();
  const t = allT.adminPlatform;
  const isMobile = useIsMobile();
  const [dockMounted, setDockMounted] = useState(false);

  useEffect(() => setDockMounted(true), []);

  const adminNav = adminNavDefs.map((item) => {
    if (!t) {
      return { ...item, label: item.key, labelMobile: item.key, hint: "" };
    }
    if (item.key === "overview") {
      return { ...item, label: t.navOverview, labelMobile: t.navOverviewShort, hint: t.navOverviewHint };
    }
    if (item.key === "cabinets") {
      return { ...item, label: t.navCabinets, labelMobile: t.navCabinets, hint: t.navCabinetsHint };
    }
    if (item.key === "plans") {
      return { ...item, label: t.navPlans, labelMobile: t.navPlansShort, hint: t.navPlansHint };
    }
    return { ...item, label: t.navLogs, labelMobile: t.navLogsShort, hint: t.navLogsHint };
  });

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    if (user?.role !== "admin_webvoice") {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, user, router]);

  if (!isAuthenticated() || user?.role !== "admin_webvoice") {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-slate-500">…</p>
      </div>
    );
  }

  if (!t) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 px-4 text-center">
        <p className="text-sm text-slate-600">Traduction admin indisponible — rechargez la page.</p>
        <button type="button" className="chip-btn primary" onClick={() => window.location.reload()}>
          Recharger
        </button>
      </div>
    );
  }

  const dock = (
    <aside className="admin-dock" aria-label="LexHub">
      <Link href="/admin" className="admin-dock__brand" title="LexHub">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/logo-lexhub-cube.png?v=cube-3"
          alt="LexHub"
          width={28}
          height={28}
          className="h-7 w-7 object-contain"
        />
      </Link>

      <nav className="admin-dock__nav">
        {adminNav.map((item) => {
          const Icon = item.icon;
          const active =
            item.href === "/admin"
              ? pathname === "/admin"
              : pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn("admin-dock__item", active && "is-active")}
              aria-label={item.label}
            >
              <Icon className="admin-dock__icon" strokeWidth={2} />
              <span className="admin-dock__text">
                <span className="admin-dock__label admin-dock__label--desk">{item.label}</span>
                <span className="admin-dock__label admin-dock__label--mob">{item.labelMobile}</span>
                <span className="admin-dock__hint">{item.hint}</span>
              </span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );

  return (
    <div className="admin-shell" dir={locale === "ar" ? "rtl" : "ltr"}>
      {isMobile && dockMounted && typeof document !== "undefined"
        ? createPortal(dock, document.body)
        : dock}

      <div className="admin-shell__main">
        <header className="admin-shell__header">
          <Link href="/admin" className="admin-shell__brand" aria-label="LexHub">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/logo-lexhub-cube.png?v=cube-3"
              alt=""
              width={40}
              height={40}
              className="admin-shell__brand-img"
            />
            <span className="admin-shell__brand-text">
              <span className="admin-shell__brand-title">LexHub</span>
            </span>
          </Link>
          <div className="admin-shell__actions">
            <ThemeToggle />
            <LanguageSwitch variant="light" />
            <UserAccountMenu compact hideSettings />
            <div className="admin-shell__ops-badge hidden items-center gap-1.5 text-[11px] text-sanad-muted xl:flex">
              <Shield className="h-3.5 w-3.5 text-sanad-gold" />
              <span title={t.opsHint}>{t.opsBadge}</span>
            </div>
          </div>
        </header>

        <main className="admin-shell__content">{children}</main>
      </div>
    </div>
  );
}
