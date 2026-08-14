"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { SanadLogo } from "@/components/brand/sanad-logo";
import { LanguageSwitch } from "@/components/layout/language-switch";
import { cn } from "@/lib/utils";
import { AnimatedButton } from "@/components/motion/animated-button";
import { useTranslations } from "@/store/locale";

export function PublicNavbar({ variant = "light" }: { variant?: "light" | "dark" }) {
  const isDark = variant === "dark";
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const t = useTranslations();

  const navLinks = [
    { href: "/about", label: t.nav.about },
    { href: "/#fonctionnalites", label: t.nav.features },
    { href: "/securite", label: t.nav.security },
  ];

  return (
    <header
      className={cn(
        "top-0 z-50 transition-all duration-300",
        isDark
          ? "fixed left-0 right-0 border-b border-[rgba(217,186,106,0.18)] bg-[rgba(10,18,32,0.88)] backdrop-blur-[10px]"
          : "sticky border-b border-sanad-stone bg-white/90 backdrop-blur-xl",
      )}
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex shrink-0 items-center gap-2">
          <SanadLogo size="md" dark={isDark} />
        </Link>

        <nav className="hidden items-center gap-1 lg:flex" aria-label="Navigation">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isDark
                  ? "text-white/80 hover:bg-white/10 hover:text-sanad-gold"
                  : "text-[#0B1F4A]/80 hover:bg-sanad-cream hover:text-[#0B1F4A]",
                pathname === link.href && (isDark ? "text-sanad-gold" : "text-[#0B1F4A]"),
              )}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-1.5 sm:gap-2">
          <LanguageSwitch variant={variant} />
          <div className="hidden sm:block">
            <AnimatedButton href="/login" variant="ghost" size="default">
              {t.nav.login}
            </AnimatedButton>
          </div>
          <AnimatedButton
            href="/login?tab=join"
            variant="outline"
            size="default"
            className={cn(
              !isDark && "border-[#0B1F4A]/25 bg-[#0B1F4A]/5 text-[#0B1F4A] hover:bg-[#0B1F4A]/10",
            )}
          >
            {t.nav.join}
          </AnimatedButton>
          <AnimatedButton href="/login?tab=register" variant="gold" size="default">
            {t.nav.register}
          </AnimatedButton>
          <button
            type="button"
            className={cn(
              "rounded-lg p-2 lg:hidden",
              isDark ? "text-white hover:bg-white/10" : "text-[#0B1F4A] hover:bg-sanad-cream",
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
            "border-t px-4 py-3 lg:hidden",
            isDark ? "border-white/10 bg-[#0B1F4A]/95" : "border-sanad-stone bg-white",
          )}
        >
          <div className="flex flex-col gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "rounded-lg px-3 py-2.5 text-sm font-medium",
                  isDark ? "text-white hover:bg-white/10" : "text-[#0B1F4A] hover:bg-sanad-cream",
                )}
              >
                {link.label}
              </Link>
            ))}
            <Link href="/login" onClick={() => setMobileOpen(false)} className="mt-2">
              <Button variant="outline" className="w-full">
                {t.nav.login}
              </Button>
            </Link>
            <Link href="/login?tab=join" onClick={() => setMobileOpen(false)}>
              <Button variant="outline" className="w-full">
                {t.nav.join}
              </Button>
            </Link>
            <Link href="/login?tab=register" onClick={() => setMobileOpen(false)}>
              <Button className="w-full bg-sanad-gold text-sanad-navy hover:bg-sanad-gold/90">
                {t.nav.register}
              </Button>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
