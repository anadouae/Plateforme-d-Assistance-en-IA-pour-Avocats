"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LogOut, Settings } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { useLocaleStore, useTranslations } from "@/store/locale";
import { cn } from "@/lib/utils";

const navConfig = [
  {
    href: "/redaction",
    tab: "plaidoirie",
    key: "redaction" as const,
    labelFr: "Plaidoirie",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <path d="M12 1a4 4 0 0 0-4 4v6a4 4 0 0 0 8 0V5a4 4 0 0 0-4-4z" />
        <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
        <line x1="12" y1="18" x2="12" y2="22" />
      </svg>
    ),
  },
  {
    href: "/cases",
    tab: "dossiers",
    key: "cases" as const,
    labelFr: "Dossiers",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <path d="M20 7h-3l-2-2H9L7 7H4a1 1 0 0 0-1 1v11a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1V8a1 1 0 0 0-1-1z" />
      </svg>
    ),
  },
  {
    href: "/documents",
    tab: "documents",
    key: "documents" as const,
    labelFr: "Documents",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <path d="M14 2v6h6" />
      </svg>
    ),
  },
  {
    href: "/agenda",
    tab: "planning",
    key: "agenda" as const,
    labelFr: "Planning",
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
    href: "/dashboard",
    tab: "dashboard",
    key: "dashboard" as const,
    labelFr: "Tableau de bord",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <rect x="3" y="3" width="7" height="9" rx="1.5" />
        <rect x="14" y="3" width="7" height="5" rx="1.5" />
        <rect x="14" y="12" width="7" height="9" rx="1.5" />
        <rect x="3" y="16" width="7" height="5" rx="1.5" />
      </svg>
    ),
  },
];

function initials(name?: string | null) {
  if (!name) return "S";
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function DockNav({ compact }: { compact?: boolean }) {
  const pathname = usePathname();
  const nav = useTranslations().app.nav;
  const locale = useLocaleStore((s) => s.locale);

  return (
    <div className={cn("dock-nav", compact && "dock-nav--compact")}>
      {navConfig.map((item) => {
        const active = pathname.startsWith(item.href);
        const label =
          locale === "ar"
            ? (nav as Record<string, string>)[item.key] || item.labelFr
            : item.labelFr;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn("dock-item", active && "active")}
            data-tab={item.tab}
            data-label={label}
            aria-label={label}
            aria-current={active ? "page" : undefined}
          >
            <span className="pill" aria-hidden />
            {item.icon}
          </Link>
        );
      })}
    </div>
  );
}

function DockFoot() {
  const { user, logout } = useAuthStore();
  const t = useTranslations().app;
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const locale = useLocaleStore((s) => s.locale);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  return (
    <div className="dock-foot" ref={ref}>
      <button
        type="button"
        className="dock-avatar"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={user?.full_name || "Menu"}
      >
        {initials(user?.full_name)}
      </button>
      {open && (
        <div
          role="menu"
          style={{
            position: "absolute",
            bottom: 56,
            [locale === "ar" ? "left" : "right"]: 0,
            minWidth: 160,
            background: "rgba(255,255,255,0.95)",
            border: "1px solid var(--line)",
            borderRadius: 18,
            boxShadow: "var(--shadow)",
            padding: "4px 0",
            zIndex: 40,
          }}
        >
          <button
            type="button"
            role="menuitem"
            className="btn-ghost"
            style={{ width: "100%", justifyContent: "flex-start", border: "none", borderRadius: 0 }}
            onClick={() => {
              setOpen(false);
              router.push("/settings");
            }}
          >
            <Settings width={16} height={16} /> {t.nav.settings}
          </button>
          <button
            type="button"
            role="menuitem"
            className="btn-ghost"
            style={{
              width: "100%",
              justifyContent: "flex-start",
              border: "none",
              borderRadius: 0,
              color: "#b91c1c",
            }}
            onClick={() => {
              setOpen(false);
              logout();
            }}
          >
            <LogOut width={16} height={16} /> {t.logout}
          </button>
        </div>
      )}
    </div>
  );
}

/** Dock desktop — classes exactes `.dock` / `.dock-nav` / `.dock-item`. */
export function AppSidebar() {
  return (
    <nav className="dock">
      <Link href="/home" className="dock-brand" aria-label="Sanad">
        <Image
          src="/logo-sanad-cube.png?v=cube-1"
          alt=""
          width={40}
          height={40}
          className="h-10 w-10 object-contain"
          unoptimized
          priority
        />
      </Link>
      <DockNav />
      <DockFoot />
    </nav>
  );
}

/** Mobile : même `.dock` via media query CSS (brand/foot masqués). */
export function AppMobileDock() {
  return null;
}
