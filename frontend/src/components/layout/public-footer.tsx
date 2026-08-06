"use client";

import Link from "next/link";
import { SanadLogo } from "@/components/brand/sanad-logo";
import { useTranslations } from "@/store/locale";

export function PublicFooter() {
  const t = useTranslations();

  return (
    <footer className="border-t border-sanad-gold/20 bg-[#0B1F4A] text-white/80">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-10 md:flex-row md:justify-between">
          <div>
            <SanadLogo size="lg" />
            <p className="mt-4 max-w-xs font-serif text-base leading-relaxed text-sanad-gold/90">
              {t.hero.title}.
              <br />
              {t.hero.subtitle}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-8 text-sm sm:grid-cols-4">
            <div>
              <p className="font-serif text-base text-sanad-gold">{t.footer.product}</p>
              <ul className="mt-3 space-y-2">
                <li>
                  <Link href="/about" className="hover:text-sanad-gold">
                    {t.footer.about}
                  </Link>
                </li>
                <li>
                  <Link href="/#fonctionnalites" className="hover:text-sanad-gold">
                    {t.footer.features}
                  </Link>
                </li>
                <li>
                  <Link href="/securite" className="hover:text-sanad-gold">
                    {t.footer.security}
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <p className="font-serif text-base text-sanad-gold">{t.footer.legal}</p>
              <ul className="mt-3 space-y-2">
                <li>
                  <Link href="/mentions-legales" className="hover:text-sanad-gold">
                    {t.footer.mentions}
                  </Link>
                </li>
                <li>
                  <Link href="/confidentialite" className="hover:text-sanad-gold">
                    {t.footer.privacy}
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <p className="font-serif text-base text-sanad-gold">{t.footer.contact}</p>
              <ul className="mt-3 space-y-2">
                <li>
                  <a href="mailto:contact@webvoice.ma" className="hover:text-sanad-gold">
                    contact@webvoice.ma
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <p className="font-serif text-base text-sanad-gold">{t.footer.account}</p>
              <ul className="mt-3 space-y-2">
                <li>
                  <Link href="/login" className="hover:text-sanad-gold">
                    {t.footer.login}
                  </Link>
                </li>
                <li>
                  <Link href="/register" className="hover:text-sanad-gold">
                    {t.footer.register}
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-10 border-t border-white/10 pt-6 text-center text-xs text-white/40">
          © {new Date().getFullYear()} WebVoice · {t.hero.title}
        </div>
      </div>
    </footer>
  );
}
