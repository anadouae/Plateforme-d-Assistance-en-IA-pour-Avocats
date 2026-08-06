"use client";

import Link from "next/link";
import { SanadLogo } from "@/components/brand/sanad-logo";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  Briefcase,
  CalendarDays,
  FileText,
  LayoutDashboard,
  LogOut,
  Mic,
  Settings,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";
import { useTranslations } from "@/store/locale";

const navConfig = [
  { href: "/dashboard", key: "dashboard" as const, icon: LayoutDashboard },
  { href: "/agenda", key: "agenda" as const, icon: CalendarDays },
  { href: "/redaction", key: "redaction" as const, icon: Mic },
  { href: "/cases", key: "cases" as const, icon: Briefcase },
  { href: "/documents", key: "documents" as const, icon: FileText },
  { href: "/team", key: "team" as const, icon: Users, roles: ["admin_cabinet"] },
  { href: "/settings", key: "settings" as const, icon: Settings },
];

const NAV_FALLBACK: Record<string, string> = {
  dashboard: "Tableau de bord",
  agenda: "Planning",
  redaction: "Plaidoirie",
  cases: "Dossiers",
  documents: "Documents",
  team: "Équipe",
  settings: "Paramètres",
};

export function AppSidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const nav = useTranslations().app.nav;
  const t = useTranslations().app;

  const filteredNav = navConfig.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role)),
  );

  return (
    <aside className="flex h-full w-64 flex-col border-r border-sanad-stone bg-sanad-ivory shadow-[8px_0_24px_-12px_rgba(15,23,42,0.18)]">
      <div className="flex flex-col gap-2 border-b border-sanad-stone px-5 py-4">
        <SanadLogo size="sm" withWordmark />
        <p className="truncate text-xs text-sanad-muted">{user?.cabinet_name}</p>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-3 [perspective:900px]">
        {filteredNav.map((item, index) => {
          const Icon = item.icon;
          const active = pathname.startsWith(item.href);
          return (
            <motion.div
              key={item.href}
              initial={{ opacity: 0, x: -12, rotateY: -12 }}
              animate={{ opacity: 1, x: 0, rotateY: 0 }}
              transition={{ delay: index * 0.04, type: "spring", stiffness: 260, damping: 22 }}
              style={{ transformStyle: "preserve-3d" }}
            >
              <Link
                href={item.href}
                onClick={onNavigate}
                className={cn(
                  "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-300",
                  "hover:-translate-y-0.5 hover:shadow-md",
                  active
                    ? "border-l-2 border-sanad-gold bg-sanad-gold/15 text-sanad-navy shadow-sm"
                    : "text-sanad-navy/70 hover:bg-sanad-cream hover:text-sanad-navy",
                )}
              >
                <Icon className="h-4 w-4 shrink-0 transition-transform duration-300 group-hover:scale-110" />
                {(nav as Record<string, string>)[item.key] || NAV_FALLBACK[item.key] || item.key}
              </Link>
            </motion.div>
          );
        })}
      </nav>

      <div className="border-t border-sanad-stone p-4">
        <div className="mb-3 truncate text-sm">
          <p className="font-medium text-sanad-navy">{user?.full_name}</p>
          <p className="text-xs text-sanad-muted">{user?.email}</p>
          {user?.role && (
            <p className="mt-1 inline-flex rounded-md bg-sanad-gold/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-sanad-navy">
              {user.role === "assistant_juridique"
                ? "Assistant"
                : user.role === "admin_cabinet"
                  ? "Admin cabinet"
                  : user.role === "avocat"
                    ? "Avocat"
                    : user.role}
            </p>
          )}
        </div>
        <button
          onClick={logout}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-sanad-navy/70 transition hover:bg-red-50 hover:text-red-600"
        >
          <LogOut className="h-4 w-4" />
          {t.logout}
        </button>
      </div>
    </aside>
  );
}
