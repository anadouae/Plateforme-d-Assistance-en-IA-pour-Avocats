"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, Shield, X } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { useTranslations } from "@/store/locale";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { LanguageSwitch } from "@/components/layout/language-switch";
import { SanadLogo } from "@/components/brand/sanad-logo";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const t = useTranslations().app;
  const hasHydrated = useAuthStore((s) => s._hasHydrated);
  const token = useAuthStore((s) => s.token);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Si persist a déjà fini avant le mount, force hydrated
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

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  if (!mounted || !hasHydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-sanad-cream">
        <p className="text-sanad-muted">{t.loading}</p>
      </div>
    );
  }

  const ok =
    !!token ||
    (typeof window !== "undefined" && !!localStorage.getItem("sanad_token"));
  if (!ok) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-sanad-cream">
        <p className="text-sanad-muted">{t.loading}</p>
      </div>
    );
  }

  return (
    <div className="flex h-dvh overflow-hidden bg-sanad-cream">
      <AnimatePresence>
        {sidebarOpen && (
          <motion.button
            type="button"
            aria-label="Fermer le menu"
            className="fixed inset-0 z-40 bg-black/40 lg:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 transition-transform duration-300 ease-out lg:static lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
        )}
      >
        <AppSidebar onNavigate={() => setSidebarOpen(false)} />
      </aside>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-sanad-stone bg-sanad-ivory/95 px-4 backdrop-blur-sm sm:px-6">
          <div className="flex min-w-0 items-center gap-2">
            <button
              type="button"
              className="rounded-lg p-2 text-sanad-navy transition hover:bg-sanad-cream lg:hidden"
              onClick={() => setSidebarOpen((v) => !v)}
              aria-label="Menu"
            >
              {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
            <SanadLogo size="sm" withWordmark glow={false} className="scale-90" />
          </div>
          <div className="flex shrink-0 items-center gap-3">
            <LanguageSwitch />
            <div className="hidden items-center gap-2 text-xs text-sanad-muted sm:flex">
              <Shield className="h-3.5 w-3.5 text-sanad-gold" />
              <span className="max-w-[200px] truncate md:max-w-none">{t.secureBanner}</span>
            </div>
          </div>
        </header>
        <main className="flex min-h-0 flex-1 flex-col overflow-y-auto p-4 sm:p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
              className="flex min-h-0 flex-1 flex-col"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
