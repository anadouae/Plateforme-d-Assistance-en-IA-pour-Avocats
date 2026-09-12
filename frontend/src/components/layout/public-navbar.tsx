"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronDown, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LexHubLogo } from "@/components/brand/sanad-logo";
import { LanguageSwitch } from "@/components/layout/language-switch";
import { cn } from "@/lib/utils";
import { AnimatedButton } from "@/components/motion/animated-button";
import { useTranslations, useLocaleStore } from "@/store/locale";
import { useAuthStore } from "@/store/auth";

type NavGroup = {
  label: string;
  items: { href: string; label: string; desc?: string }[];
};

/** Navbar marketing — menus déroulants au survol (desktop). */
export function PublicNavbar({ variant = "light" }: { variant?: "light" | "dark" }) {
  const isDark = variant === "dark";
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [hoverKey, setHoverKey] = useState<string | null>(null);
  const t = useTranslations();
  const ar = useLocaleStore((s) => s.locale) === "ar";
  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.token);
  const hydrated = useAuthStore((s) => s._hasHydrated);
  // Après hydratation seulement — évite mismatch SSR / client (overlay Next.js).
  const loggedIn = hydrated && !!(user || token);

  const groups: NavGroup[] = [
    {
      label: t.nav.features || "Produit",
      items: [
        { href: "/#fonctionnalites", label: t.nav.features, desc: "Dictée → plaidoirie" },
        { href: "/#parrainage", label: ar ? "الإحالة" : "Parrainage", desc: ar ? "+14 يوم / +1 شهر" : "+14 j / +1 mois" },
        { href: "/#faq", label: "FAQ", desc: "Questions d’avocat" },
        { href: "/fonctionnalites", label: t.footer?.features || "Fonctionnalités" },
      ],
    },
    {
      label: t.nav.pricing,
      items: [
        { href: "/tarifs", label: t.nav.pricing, desc: "Solo · Cabinet · Entreprise" },
        { href: "/#parrainage", label: ar ? "الإحالة" : "Parrainage", desc: ar ? "شهر إضافي" : "Mois offert" },
        { href: "/login?tab=register", label: t.nav.register, desc: "Créer un cabinet" },
      ],
    },
    {
      label: t.nav.security,
      items: [
        { href: "/securite", label: t.nav.security, desc: "Secret professionnel" },
        { href: "/confidentialite", label: t.footer?.privacy || "Confidentialité" },
        { href: "/mentions-legales", label: t.footer?.mentions || "Mentions" },
      ],
    },
    {
      label: t.nav.about,
      items: [
        { href: "/about", label: t.nav.about },
        { href: "/aide", label: t.nav.help || "Aide" },
        { href: "/contact", label: t.footer?.contact || "Contact" },
      ],
    },
  ];

  return (
    <header
      className={cn(
        "sanad-public-nav top-0 z-[200] transition-all duration-300 fixed inset-x-0",
        isDark ? "sanad-public-nav--dark" : "sanad-public-nav--light",
      )}
    >      <div className="sanad-public-nav__glow" aria-hidden />
      <div className="relative z-10 mx-auto flex h-16 max-w-7xl items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
        <Link href={loggedIn ? "/dashboard" : "/"} className="flex shrink-0 items-center gap-2">
          <LexHubLogo size="md" dark={isDark} />
        </Link>

        <nav className="hidden items-center gap-0.5 lg:flex" aria-label="Navigation">
          {groups.map((g) => (
            <div
              key={g.label}
              className="relative"
              onMouseEnter={() => setHoverKey(g.label)}
              onMouseLeave={() => setHoverKey(null)}
            >
              <button
                type="button"
                className={cn(
                  "inline-flex items-center gap-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isDark
                    ? "text-white/80 hover:bg-white/10 hover:text-[#A8C0FF]"
                    : "text-[var(--ink)]/80 hover:bg-[rgba(76,124,255,0.08)] hover:text-[var(--ink)]",
                  hoverKey === g.label && (isDark ? "text-[#A8C0FF]" : "text-[var(--royal-800)]"),
                )}
                aria-expanded={hoverKey === g.label}
              >
                {g.label}
                <ChevronDown
                  className={cn(
                    "h-3.5 w-3.5 opacity-70 transition-transform",
                    hoverKey === g.label && "rotate-180",
                  )}
                />
              </button>
              <div
                className={cn(
                  "absolute start-0 top-full z-[220] min-w-[240px] pt-2 transition",
                  hoverKey === g.label
                    ? "pointer-events-auto visible opacity-100"
                    : "pointer-events-none invisible opacity-0",
                )}
              >
                <div
                  className={cn(
                    "overflow-hidden rounded-xl border shadow-xl",
                    isDark
                      ? "border-white/10 bg-[#0B1A4D]"
                      : "border-[var(--line)] bg-white",
                  )}
                >
                  {g.items.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={cn(
                        "block px-4 py-2.5 transition",
                        isDark
                          ? "hover:bg-white/10"
                          : "hover:bg-[rgba(76,124,255,0.06)]",
                        pathname === item.href && "bg-[rgba(76,124,255,0.08)]",
                      )}
                      onClick={() => setHoverKey(null)}
                    >
                      <span
                        className={cn(
                          "block text-sm font-semibold",
                          isDark ? "text-white" : "text-[var(--ink)]",
                        )}
                      >
                        {item.label}
                      </span>
                      {item.desc ? (
                        <span
                          className={cn(
                            "mt-0.5 block text-[11px]",
                            isDark ? "text-white/50" : "text-slate-500",
                          )}
                        >
                          {item.desc}
                        </span>
                      ) : null}
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </nav>

        <div className="flex items-center gap-1.5 sm:gap-2">
          <LanguageSwitch variant={variant} />
          {loggedIn ? (
            <AnimatedButton href="/dashboard" variant="gold" size="default">
              {ar ? "مساحتي" : "Mon espace"}
            </AnimatedButton>
          ) : (
            <>
              <div className="hidden sm:block">
                <AnimatedButton href="/login" variant="ghost" size="default">
                  {t.nav.login}
                </AnimatedButton>
              </div>
              <AnimatedButton href="/login?tab=register" variant="gold" size="default">
                {t.nav.register}
              </AnimatedButton>
            </>
          )}
          <button
            type="button"
            className={cn(
              "rounded-lg p-2 lg:hidden",
              isDark
                ? "text-white hover:bg-white/10"
                : "text-[var(--ink)] hover:bg-[rgba(76,124,255,0.08)]",
            )}
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Menu"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div
          className={cn(
            "relative z-10 border-t px-4 py-3 lg:hidden",
            isDark
              ? "border-white/10 bg-[rgba(7,16,51,0.96)]"
              : "border-[var(--line)] bg-[var(--card)]",
          )}
        >
          <div className="flex flex-col gap-1">
            {groups.flatMap((g) =>
              g.items.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className={cn(
                    "rounded-lg px-3 py-2.5 text-sm font-medium",
                    isDark
                      ? "text-white hover:bg-white/10"
                      : "text-[var(--ink)] hover:bg-[rgba(76,124,255,0.08)]",
                  )}
                >
                  {link.label}
                </Link>
              )),
            )}
            {loggedIn ? (
              <Link href="/dashboard" onClick={() => setMobileOpen(false)} className="mt-2">
                <Button className="w-full bg-sanad-gold text-sanad-navy hover:bg-sanad-gold/90">
                  {ar ? "مساحتي" : "Mon espace"}
                </Button>
              </Link>
            ) : (
              <>
                <Link href="/login" onClick={() => setMobileOpen(false)} className="mt-2">
                  <Button variant="outline" className="w-full">
                    {t.nav.login}
                  </Button>
                </Link>
                <Link href="/login?tab=register" onClick={() => setMobileOpen(false)}>
                  <Button className="w-full bg-sanad-gold text-sanad-navy hover:bg-sanad-gold/90">
                    {t.nav.register}
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
