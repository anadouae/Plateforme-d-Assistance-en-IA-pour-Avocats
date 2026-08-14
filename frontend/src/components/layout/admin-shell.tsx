"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { SanadLogo } from "@/components/brand/sanad-logo";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Building2,
  LayoutDashboard,
  LogOut,
  ScrollText,
  Shield,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";

const adminNav = [
  { href: "/admin", label: "Dashboard", icon: LayoutDashboard },
  { href: "/admin/cabinets", label: "Cabinets", icon: Building2 },
  { href: "/admin/logs", label: "Logs & Audit", icon: ScrollText },
  { href: "/admin/benchmark", label: "Benchmark MA", icon: BarChart3 },
];

export function AdminShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout, isAuthenticated } = useAuthStore();

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
    return <div className="flex min-h-screen items-center justify-center"><p className="text-slate-500">…</p></div>;
  }

  return (
    <div className="flex min-h-screen bg-sanad-light">
      <aside className="flex w-64 flex-col border-r border-sanad-stone bg-sanad-navy text-sanad-ivory">
        <div className="flex items-center gap-3 border-b border-sanad-gold/20 px-5 py-4">
          <SanadLogo size="sm" />
          <div>
            <p className="font-serif font-bold">WebVoice</p>
            <p className="text-xs text-sanad-ivory/50">Back-office Sanad</p>
          </div>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {adminNav.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  active
                    ? "bg-sanad-gold/20 text-sanad-gold"
                    : "text-sanad-ivory/70 hover:bg-sanad-gold/10 hover:text-sanad-ivory",
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-sanad-gold/20 p-4">
          <p className="truncate text-sm font-medium">{user?.full_name}</p>
          <p className="truncate text-xs text-sanad-ivory/50">{user?.email}</p>
          <button
            onClick={logout}
            className="mt-3 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-sanad-ivory/70 hover:bg-red-900/30 hover:text-red-300"
          >
            <LogOut className="h-4 w-4" />
            Déconnexion
          </button>
        </div>
      </aside>
      <div className="flex flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-sanad-stone bg-sanad-ivory px-6">
          <p className="text-sm font-medium text-sanad-navy">Administration plateforme</p>
          <div className="flex items-center gap-2 text-xs text-sanad-muted">
            <Shield className="h-3.5 w-3.5 text-sanad-gold" />
            Accès technique uniquement — pas de contenu confidentiel
          </div>
        </header>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
