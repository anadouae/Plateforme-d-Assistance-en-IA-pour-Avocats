"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { PublicNavbar } from "@/components/layout/public-navbar";
import { PublicFooter } from "@/components/layout/public-footer";
import { FadeIn } from "@/components/motion/fade-in";
import { LexHubLogo } from "@/components/brand/sanad-logo";
import { useClientLocale } from "@/store/locale";

interface LegalPageLayoutProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}

function CheckoutReturnBar() {
  const ar = useClientLocale() === "ar";
  const sp = useSearchParams();
  const ret = sp.get("return");
  if (!ret || !ret.startsWith("/")) return null;
  const isCheckout = ret.startsWith("/checkout");
  return (
    <div className="sticky top-0 z-50 border-b border-[#152f75] bg-[#1B3F9C] px-4 py-2.5 text-center text-sm text-white shadow-md">
      <Link href={ret} className="font-semibold hover:underline">
        {isCheckout
          ? ar
            ? "→ العودة للدفع (تُحفظ معلوماتكم)"
            : "← Retour au paiement (vos informations sont conservées)"
          : ar
            ? "→ رجوع"
            : "← Retour"}
      </Link>
    </div>
  );
}

export function LegalPageLayout({ title, subtitle, children }: LegalPageLayoutProps) {
  const ar = useClientLocale() === "ar";
  return (
    <div className="min-h-screen bg-sanad-cream" dir={ar ? "rtl" : "ltr"}>
      <Suspense fallback={null}>
        <CheckoutReturnBar />
      </Suspense>
      <PublicNavbar variant="light" />
      <main className="relative overflow-hidden pb-16 pt-24">
        <div className="sanad-orb sanad-orb-1 opacity-20" />
        <div className="sanad-orb sanad-orb-2 opacity-15" />

        <div className="relative mx-auto max-w-3xl px-4 sm:px-6">
          <FadeIn>
            <div className="mb-10 flex items-center gap-4">
              <LexHubLogo size="lg" />
              <div>
                <h1 className="text-3xl font-bold text-sanad-navy">{title}</h1>
                {subtitle && <p className="mt-1 text-sanad-muted">{subtitle}</p>}
              </div>
            </div>
          </FadeIn>

          <FadeIn delay={0.1}>
            <article className="glass-card-light space-y-6 p-8 text-sanad-navy leading-relaxed">
              {children}
            </article>
          </FadeIn>

          <FadeIn delay={0.2} className="mt-8 text-center">
            <Link href="/" className="text-sm text-sanad-gold hover:text-sanad-gold hover:underline">
              {ar ? "العودة للرئيسية →" : "← Retour à l'accueil"}
            </Link>
          </FadeIn>
        </div>
      </main>
      <PublicFooter />
    </div>
  );
}
