"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLocaleStore, useTranslations } from "@/store/locale";
import { useAuthStore } from "@/store/auth";
import { canManageTeam, isAssistant } from "@/lib/roles";
import { cn } from "@/lib/utils";

const micIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <path d="M12 1a4 4 0 0 0-4 4v6a4 4 0 0 0 8 0V5a4 4 0 0 0-4-4z" />
    <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
    <line x1="12" y1="18" x2="12" y2="22" />
  </svg>
);

/** Pile de documents validés — espace assistant (pas micro). */
const validatedPleaIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M8 6h9a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z" />
    <path d="M6 8H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-1" opacity="0.55" />
    <path d="M10 12l1.5 1.5L15 10" />
  </svg>
);

const baseNavLawyer = [
  {
    href: "/redaction",
    key: "redaction" as const,
    labelFr: "Plaidoirie",
    hintFr: "Atelier dictée",
    hintAr: "ورشة الإملاء",
    icon: micIcon,
  },
  {
    href: "/cases",
    key: "cases" as const,
    labelFr: "Dossiers",
    hintFr: "Affaires du cabinet",
    hintAr: "ملفات المكتب",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <path d="M20 7h-3l-2-2H9L7 7H4a1 1 0 0 0-1 1v11a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1V8a1 1 0 0 0-1-1z" />
      </svg>
    ),
  },
  {
    href: "/documents",
    key: "documents" as const,
    labelFr: "Documents",
    hintFr: "Pièces & extraits",
    hintAr: "القطع والمستخرجات",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <path d="M14 2v6h6" />
      </svg>
    ),
  },
  {
    href: "/agenda",
    key: "agenda" as const,
    labelFr: "Planning",
    hintFr: "Audiences & ICS",
    hintAr: "الجلسات والتصدير",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <rect x="3" y="4" width="18" height="18" rx="3" />
        <line x1="16" y1="2" x2="16" y2="6" />
        <line x1="8" y1="2" x2="8" y2="6" />
        <line x1="3" y1="10" x2="21" y2="10" />
      </svg>
    ),
  },
  {
    href: "/activity",
    key: "activity" as const,
    labelFr: "Activité",
    hintFr: "Journal du cabinet",
    hintAr: "سجل المكتب",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
      </svg>
    ),
  },
];

const teamNav = {
  href: "/team",
  key: "team" as const,
  labelFr: "Équipe",
  hintFr: "Invitations",
  hintAr: "الدعوات",
  icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
};

function DockNav() {
  const pathname = usePathname();
  const t = useTranslations().app;
  const locale = useLocaleStore((s) => s.locale);
  const role = useAuthStore((s) => s.user?.role);
  const assistant = isAssistant(role);

  const navItems = (() => {
    const items = baseNavLawyer.map((item) => {
      if (item.key === "redaction" && assistant) {
        return {
          ...item,
          icon: validatedPleaIcon,
          labelFr: "Plaidoiries validées",
          hintFr: "Textes validés",
          hintAr: "مرافعات معتمدة",
        };
      }
      return item;
    });
    return canManageTeam(role) ? [...items, teamNav] : items;
  })();

  return (
    <div className="dock-nav">
      {navItems.map((item) => {
        const active =
          pathname === item.href ||
          (item.href !== "/dashboard" && pathname.startsWith(item.href));
        const label =
          locale === "ar"
            ? item.key === "redaction" && assistant
              ? "مرافعات معتمدة"
              : t.nav[item.key]
            : item.labelFr;
        const hint = locale === "ar" ? item.hintAr : item.hintFr;
        return (
          <Link
            key={item.href}
            href={item.href}
            prefetch
            className={cn("dock-item", active && "active")}
            data-label={label}
            data-tour-id={`nav-${item.key}`}
            aria-label={label}
            aria-current={active ? "page" : undefined}
          >
            <span className="pill" aria-hidden />
            {item.icon}
            <span className="dock-item__text">
              <span className="dock-item__label">{label}</span>
              <span className="dock-item__hint">{hint}</span>
            </span>
          </Link>
        );
      })}
    </div>
  );
}

/** Dock desktop — labels visibles comme l’admin plateforme. */
export function AppSidebar() {
  return (
    <nav className="dock">
      <Link href="/dashboard" className="dock-brand" aria-label="LexHub" data-tour-id="brand">
        <Image
          src="/logo-lexhub-cube.png?v=cube-2"
          alt=""
          width={40}
          height={40}
          className="h-10 w-10 object-contain"
          unoptimized
          priority
        />
      </Link>
      <DockNav />
    </nav>
  );
}

export function AppMobileDock() {
  return null;
}
