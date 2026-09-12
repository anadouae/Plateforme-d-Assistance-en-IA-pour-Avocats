"use client";

import { useState } from "react";
import Link from "next/link";
import { authHrefForPlan, saveBillingIntent } from "@/lib/billing-intent";
import { LexProductModal } from "@/components/billing/lex-product-modal";

type Props = {
  open: boolean;
  onClose: () => void;
  planSlug: string;
  cycle: "monthly" | "yearly";
  ar: boolean;
};

export function AuthGateModal({ open, onClose, planSlug, cycle, ar }: Props) {
  const [email, setEmail] = useState("");

  function continueRegister() {
    saveBillingIntent({ plan: planSlug, cycle, intent: planSlug === "free" ? "free" : "trial" });
    const base = authHrefForPlan(planSlug, cycle, "register");
    const url = email.trim()
      ? `${base}&email=${encodeURIComponent(email.trim())}`
      : base;
    window.location.assign(url);
  }

  function continueLogin() {
    saveBillingIntent({ plan: planSlug, cycle, intent: planSlug === "free" ? "free" : "trial" });
    window.location.assign(authHrefForPlan(planSlug, cycle, "login"));
  }

  return (
    <LexProductModal
      open={open}
      onClose={onClose}
      zIndexClass="z-[85]"
      tag={ar ? "حساب" : "Compte"}
      title={ar ? "تسجيل الدخول أو إنشاء حساب" : "Connexion ou création de compte"}
      points={
        ar
          ? [
              "أسّسوا مكتبكم على LexHub وتابعوا حسب وتيرتكم",
              "التجربة تبدأ اليوم — بدون خصم فوري على الخطط المدفوعة",
            ]
          : [
              "Créez l’espace de votre cabinet sur LexHub",
              "L’essai commence aujourd’hui — aucun débit immédiat sur les plans payants",
            ]
      }
      primaryLabel={ar ? "متابعة" : "Continuer"}
      onPrimary={continueRegister}
      secondaryLabel={ar ? "لدي حساب — تسجيل الدخول" : "J’ai déjà un compte — Se connecter"}
      onSecondary={continueLogin}
      closeLabel={ar ? "إغلاق" : "Fermer"}
    >
      <div className="font-[system-ui,sans-serif]">
        <label className="block text-[11px] font-semibold uppercase tracking-wide text-[#8b93b0]">
          Email <span className="text-[#ff8a2d]">*</span>
        </label>
        <input
          type="email"
          className="mt-1.5 w-full rounded-[3px] border border-white/15 bg-[#12182a] px-3 py-2.5 text-sm text-[#f4efe6] outline-none placeholder:text-[#8b93b0] focus:border-[#3b5cde]"
          placeholder="name@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
        />
        <p className="mt-3 text-[11px] leading-relaxed text-[#8b93b0]">
          {ar ? "بالمتابعة، أوافق على " : "En continuant, j’accepte les "}
          <Link href="/mentions-legales" className="text-[#5a8bff] underline">
            {ar ? "شروط الاستخدام" : "Conditions d’utilisation"}
          </Link>
          {", "}
          <Link href="/remboursement" className="text-[#5a8bff] underline">
            {ar ? "سياسة الاسترداد" : "Politique de remboursement"}
          </Link>
          {ar ? " و" : " et la "}
          <Link href="/confidentialite" className="text-[#5a8bff] underline">
            {ar ? "سياسة الخصوصية" : "Politique de confidentialité"}
          </Link>
          .
        </p>
      </div>
    </LexProductModal>
  );
}
