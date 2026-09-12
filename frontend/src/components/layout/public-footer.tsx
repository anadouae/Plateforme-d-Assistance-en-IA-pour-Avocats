"use client";

import Link from "next/link";
import { LexHubLogo } from "@/components/brand/sanad-logo";
import { useTranslations } from "@/store/locale";

export function PublicFooter() {
  const t = useTranslations();

  return (
    <footer className="border-t border-[#FFB07A]/25 bg-[#12307A] text-white/85">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-10 md:flex-row md:justify-between">
          <div>
            <LexHubLogo size="lg" dark />
            <p className="mt-4 max-w-xs font-serif text-base leading-relaxed text-[#FFE6C2]">
              {t.hero.title}.
              <br />
              {t.hero.subtitle}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-8 text-sm sm:grid-cols-4">
            <div>
              <p className="font-serif text-base text-[#FFB07A]">{t.footer.product}</p>
              <ul className="mt-3 space-y-2 text-white/75">
                <li>
                  <Link href="/about" className="hover:text-[#FFE6C2]">
                    {t.footer.about}
                  </Link>
                </li>
                <li>
                  <Link href="/#fonctionnalites" className="hover:text-[#FFE6C2]">
                    {t.footer.features}
                  </Link>
                </li>
                <li>
                  <Link href="/securite" className="hover:text-[#FFE6C2]">
                    {t.footer.security}
                  </Link>
                </li>
                <li>
                  <Link href="/#faq" className="hover:text-[#FFE6C2]">
                    FAQ
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <p className="font-serif text-base text-[#FFB07A]">{t.footer.legal}</p>
              <ul className="mt-3 space-y-2 text-white/75">
                <li>
                  <Link href="/mentions-legales" className="hover:text-[#FFE6C2]">
                    {t.footer.mentions}
                  </Link>
                </li>
                <li>
                  <Link href="/confidentialite" className="hover:text-[#FFE6C2]">
                    {t.footer.privacy}
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <p className="font-serif text-base text-[#FFB07A]">{t.footer.contact}</p>
              <ul className="mt-3 space-y-2 text-white/75">
                <li>
                  <a href="mailto:contact@lexhub.space" className="hover:text-[#FFE6C2]">
                    contact@lexhub.space
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <p className="font-serif text-base text-[#FFB07A]">{t.footer.account}</p>
              <ul className="mt-3 space-y-2 text-white/75">
                <li>
                  <Link href="/login" className="hover:text-[#FFE6C2]">
                    {t.footer.login}
                  </Link>
                </li>
                <li>
                  <Link href="/register" className="hover:text-[#FFE6C2]">
                    {t.footer.register}
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-10 border-t border-white/10 pt-6 text-center text-xs text-white/40">
          © {new Date().getFullYear()} LexHub · {t.hero.title}
        </div>
      </div>
    </footer>
  );
}
