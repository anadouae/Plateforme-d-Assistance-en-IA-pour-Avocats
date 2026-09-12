"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ArrowLeftRight,
  Building2,
  Check,
  Lock,
  MapPin,
  Sparkles,
} from "lucide-react";
import { LexHubLogo } from "@/components/brand/sanad-logo";
import { CardBrandBadges } from "@/components/billing/card-brand-badges";
import { PaymentSuccessModal } from "@/components/billing/payment-success-modal";
import { BillingOwnerGate } from "@/components/billing/ask-admin-billing";
import { ConfirmActionModal } from "@/components/billing/confirm-action-modal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ApiError, type BillingPlan, type CabinetSettings } from "@/lib/api";
import { FALLBACK_BILLING_PLANS } from "@/lib/billing-plans-fallback";
import { clearBillingIntent, saveBillingIntent, commercialHref, needsCommercialQualification } from "@/lib/billing-intent";
import {
  clearCheckoutDraft,
  readCheckoutDraft,
  saveCheckoutDraft,
} from "@/lib/checkout-draft";
import { planTrialBadge } from "@/lib/plan-cta";
import { useAuthStore } from "@/store/auth";
import { useClientLocale } from "@/store/locale";
import { canManageTeam } from "@/lib/roles";

function formatCardNumber(raw: string): string {
  const digits = raw.replace(/\D/g, "").slice(0, 16);
  return digits.replace(/(.{4})/g, "$1 ").trim();
}

function luhnOk(num: string): boolean {
  const digits = num.replace(/\D/g, "");
  if (digits.length < 13) return false;
  let sum = 0;
  let alt = false;
  for (let i = digits.length - 1; i >= 0; i--) {
    let n = parseInt(digits[i]!, 10);
    if (alt) {
      n *= 2;
      if (n > 9) n -= 9;
    }
    sum += n;
    alt = !alt;
  }
  return sum % 10 === 0;
}

function CheckoutInner() {
  const ar = useClientLocale() === "ar";
  const router = useRouter();
  const search = useSearchParams();
  const user = useAuthStore((s) => s.user);
  const hydrated = useAuthStore((s) => s._hasHydrated);
  const planSlug = (search.get("plan") || "pro").trim();
  const cycle = search.get("cycle") === "yearly" ? "yearly" : "monthly";

  useEffect(() => {
    if (needsCommercialQualification(planSlug)) {
      router.replace(commercialHref("enterprise"));
    }
  }, [planSlug, router]);

  const [plans, setPlans] = useState<BillingPlan[]>(FALLBACK_BILLING_PLANS);
  const [cabinet, setCabinet] = useState<CabinetSettings | null>(null);
  const [logoUrl, setLogoUrl] = useState<string | null>(null);

  const [cardholderName, setCardholderName] = useState("");
  const [cardNumber, setCardNumber] = useState("");
  const [expiry, setExpiry] = useState("");
  const [cvc, setCvc] = useState("");
  const [billingAddress, setBillingAddress] = useState("");
  const [billingCity, setBillingCity] = useState("");
  const [billingEmail, setBillingEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [agreed, setAgreed] = useState(false);

  const [successOpen, setSuccessOpen] = useState(false);
  const [confirmPay, setConfirmPay] = useState(false);
  const [successData, setSuccessData] = useState<{
    invoiceNumber?: string;
    invoiceHtml?: string;
  }>({});

  const persistDraft = useCallback(() => {
    saveCheckoutDraft({
      cardholderName,
      cardNumber,
      expiry,
      cvc,
      billingAddress,
      billingCity,
      billingEmail,
      agreed,
    });
  }, [cardholderName, cardNumber, expiry, cvc, billingAddress, billingCity, billingEmail, agreed]);

  useEffect(() => {
    saveBillingIntent({ plan: planSlug, cycle, intent: "trial" });
    api
      .getBillingPlans()
      .then((list) => setPlans(list.length ? list : FALLBACK_BILLING_PLANS))
      .catch(() => setPlans(FALLBACK_BILLING_PLANS));
    api
      .getCabinetSettings()
      .then((c) => {
        setCabinet(c);
        if (c.address) setBillingAddress((v) => v || c.address);
        if (c.city) setBillingCity((v) => v || c.city);
      })
      .catch(() => undefined);
    api.getCabinetLogoDataUrl().then(setLogoUrl).catch(() => null);

    const draft = readCheckoutDraft();
    if (draft) {
      setCardholderName(draft.cardholderName);
      setCardNumber(draft.cardNumber);
      setExpiry(draft.expiry);
      setCvc(draft.cvc);
      setBillingAddress(draft.billingAddress);
      setBillingCity(draft.billingCity);
      setBillingEmail(draft.billingEmail);
      setAgreed(draft.agreed);
    } else if (user?.full_name) {
      setCardholderName(user.full_name);
    }
    if (user?.email) setBillingEmail((v) => v || user.email);
  }, [planSlug, cycle, user?.full_name, user?.email]);

  useEffect(() => {
    persistDraft();
  }, [persistDraft]);

  const plan = useMemo(
    () => plans.find((p) => p.slug === planSlug) || plans.find((p) => p.slug === "pro") || null,
    [plans, planSlug],
  );

  const paidPlans = useMemo(
    () => plans.filter((p) => p.price_mad_monthly > 0).sort((a, b) => a.sort_order - b.sort_order),
    [plans],
  );

  const price = plan ? (cycle === "yearly" ? plan.price_mad_yearly : plan.price_mad_monthly) : 0;
  const trialDays = plan && plan.trial_days > 0 ? plan.trial_days : 30;
  const planName = plan ? (ar && plan.name_ar ? plan.name_ar : plan.name) : "";
  const isAdmin = canManageTeam(user?.role);
  const highlights = plan
    ? (ar && plan.highlights_ar?.length ? plan.highlights_ar : plan.highlights || []).slice(0, 4)
    : [];
  const returnPath = `/checkout?plan=${planSlug}&cycle=${cycle}`;
  const legalHref = (path: string) => `${path}?return=${encodeURIComponent(returnPath)}`;
  const yearlySave =
    plan && plan.price_mad_monthly > 0
      ? Math.max(0, plan.price_mad_monthly * 12 - plan.price_mad_yearly)
      : 0;

  function switchPlan(slug: string, nextCycle?: "monthly" | "yearly") {
    persistDraft();
    const c = nextCycle || cycle;
    router.replace(`/checkout?plan=${slug}&cycle=${c}`);
  }

  async function submit() {
    if (!plan || !isAdmin) {
      setError(ar ? "فقط مدير المكتب يمكنه تفعيل الخطة." : "Seul l'admin cabinet peut activer le plan.");
      return;
    }
    if (!agreed) {
      setError(ar ? "يجب الموافقة على الشروط." : "Veuillez accepter les conditions.");
      return;
    }
    if (!cardholderName.trim()) {
      setError(ar ? "اسم حامل البطاقة مطلوب" : "Nom du porteur de carte requis");
      return;
    }
    const digits = cardNumber.replace(/\D/g, "");
    if (digits.length < 16 || !luhnOk(digits)) {
      setError(ar ? "رقم البطاقة غير صالح" : "Numéro de carte invalide");
      return;
    }
    const m = expiry.match(/^(\d{2})\/(\d{2})$/);
    if (!m) {
      setError(ar ? "تاريخ MM/AA غير صالح" : "Date MM/AA invalide");
      return;
    }
    if (cvc.replace(/\D/g, "").length < 3) {
      setError(ar ? "CVC غير صالح" : "CVC invalide");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const res = await api.selectBillingPlan(plan.slug, cycle, {
        name: cardholderName.trim(),
        number: digits,
        exp: expiry,
        cvc,
      });
      clearBillingIntent();
      clearCheckoutDraft();
      setSuccessData({
        invoiceNumber: res.invoice_number,
        invoiceHtml: res.invoice_html,
      });
      setSuccessOpen(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : ar ? "خطأ في الدفع" : "Erreur de paiement");
    } finally {
      setBusy(false);
    }
  }

  if (!hydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F7F8FC] p-6" dir={ar ? "rtl" : "ltr"}>
        <p className="text-sm text-slate-500">{ar ? "جاري التحميل…" : "Chargement de la session…"}</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F7F8FC] p-6" dir={ar ? "rtl" : "ltr"}>
        <div className="max-w-md rounded-2xl bg-white p-8 text-center shadow-lg">
          <LexHubLogo size="md" withWordmark />
          <p className="mt-4 text-sm text-slate-600">
            {ar ? "يلزم تسجيل الدخول لإتمام الدفع." : "Connexion requise pour finaliser le paiement."}
          </p>
          <Link
            href={`/login?tab=login&plan=${planSlug}&cycle=${cycle}&intent=checkout`}
            className="mt-5 inline-flex rounded-xl bg-[#1B3F9C] px-5 py-2.5 text-sm font-semibold text-white"
          >
            {ar ? "تسجيل الدخول" : "Se connecter"}
          </Link>
        </div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F7F8FC] p-6" dir={ar ? "rtl" : "ltr"}>
        <BillingOwnerGate ar={ar} />
      </div>
    );
  }

  const endDate = new Date();
  endDate.setDate(endDate.getDate() + trialDays);
  const endLabel = endDate.toLocaleDateString(ar ? "ar-MA" : "fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return (
    <div className="min-h-screen bg-[#F7F8FC]" dir={ar ? "rtl" : "ltr"}>
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <Link href="/">
            <LexHubLogo size="sm" withWordmark />
          </Link>
          <div className="flex items-center gap-3">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => router.push("/dashboard")}
            >
              {ar ? "إلغاء والعودة" : "Annuler · retour"}
            </Button>
            <div className="text-end text-xs text-slate-500">
              <p className="font-semibold text-[#0A1228]">{user.full_name}</p>
              <p>{ar ? "دفع آمن" : "Paiement sécurisé"}</p>
            </div>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="font-display text-2xl font-semibold text-[#0A1228]">
              {ar ? "إتمام الاشتراك" : "Finaliser votre abonnement"}
            </h1>
            <p className="text-sm text-slate-500">
              {ar
                ? "محاكاة جاهزة — الدفع الحقيقي قريبًا (CMI / PayZone). يمكنكم الإلغاء والعودة في أي وقت."
                : "Simulation prête — paiement réel bientôt (CMI / PayZone). Vous pouvez annuler et revenir à tout moment."}
            </p>
            <p className="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950">
              {ar
                ? "إذا كنتم بالفعل في فترة تجربة: لا يُخصم شيء اليوم. الاشتراك المدفوع يبدأ بعد نهاية التجربة (ما لم تُلغوا)."
                : "Si vous êtes déjà en essai : 0 MAD aujourd’hui. L’abonnement payant ne commence qu’après la fin de l’essai (sauf résiliation)."}
            </p>
          </div>
          <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">
            {ar ? "0 درهم اليوم" : "0 MAD aujourd'hui"}
          </span>
        </div>

        <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-4">
            {/* Cabinet */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <Building2 className="h-3.5 w-3.5" />
                {ar ? "المكتب" : "Cabinet"}
              </p>
              <div className="mt-3 flex items-center gap-3">
                {logoUrl ? (
                  <img
                    src={logoUrl}
                    alt=""
                    className="h-12 w-12 rounded-xl border border-slate-200 object-contain bg-white p-1"
                  />
                ) : (
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#1B3F9C]/10 text-sm font-bold text-[#1B3F9C]">
                    {(cabinet?.name || "LX").slice(0, 2).toUpperCase()}
                  </div>
                )}
                <div>
                  <p className="font-semibold text-[#0A1228]">{cabinet?.name || user.full_name}</p>
                  {cabinet?.name_ar ? (
                    <p className="text-xs text-slate-500" dir="rtl">
                      {cabinet.name_ar}
                    </p>
                  ) : null}
                  <p className="text-xs text-slate-500">
                    {[cabinet?.city, cabinet?.barreau].filter(Boolean).join(" · ") || "Maroc"}
                  </p>
                </div>
              </div>
            </div>

            {/* Billing + card */}
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                {ar ? "الفوترة" : "Facturation"}
              </h2>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <Input
                  placeholder={ar ? "بريد الفوترة (اختياري)" : "E-mail facturation (optionnel)"}
                  value={billingEmail}
                  onChange={(e) => setBillingEmail(e.target.value)}
                  type="email"
                  autoComplete="email"
                  className="sm:col-span-2"
                />
                <Input
                  placeholder={ar ? "العنوان" : "Adresse"}
                  value={billingAddress}
                  onChange={(e) => setBillingAddress(e.target.value)}
                  autoComplete="street-address"
                  className="sm:col-span-2"
                />
                <Input
                  placeholder={ar ? "المدينة" : "Ville"}
                  value={billingCity}
                  onChange={(e) => setBillingCity(e.target.value)}
                  autoComplete="address-level2"
                />
                <Input value={ar ? "المغرب" : "Maroc"} disabled />
              </div>

              <div className="mt-6 flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                  {ar ? "البطاقة البنكية" : "Carte bancaire"}
                </h2>
                <CardBrandBadges cardNumber={cardNumber} />
              </div>
              <div className="mt-3 space-y-3 rounded-xl border border-slate-200 p-4">
                <p className="flex items-center gap-2 text-xs text-slate-500">
                  <Lock className="h-3.5 w-3.5" />
                  {ar
                    ? "دفع محاكى — بيئة تجريبية آمنة"
                    : "Paiement simulé — environnement de test sécurisé"}
                </p>
                <Input
                  placeholder={ar ? "اسم حامل البطاقة" : "Nom du porteur de carte"}
                  value={cardholderName}
                  onChange={(e) => setCardholderName(e.target.value)}
                  autoComplete="cc-name"
                />
                <Input
                  placeholder="4242 4242 4242 4242"
                  value={cardNumber}
                  onChange={(e) => setCardNumber(formatCardNumber(e.target.value))}
                  inputMode="numeric"
                  autoComplete="cc-number"
                />
                <div className="grid grid-cols-2 gap-3">
                  <Input
                    placeholder="MM/AA"
                    value={expiry}
                    onChange={(e) => {
                      let v = e.target.value.replace(/\D/g, "").slice(0, 4);
                      if (v.length >= 3) v = `${v.slice(0, 2)}/${v.slice(2)}`;
                      setExpiry(v);
                    }}
                    inputMode="numeric"
                    autoComplete="cc-exp"
                  />
                  <Input
                    placeholder="CVC"
                    value={cvc}
                    onChange={(e) => setCvc(e.target.value.replace(/\D/g, "").slice(0, 4))}
                    inputMode="numeric"
                    autoComplete="cc-csc"
                  />
                </div>
              </div>

              {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}

              <div className="mt-6 flex flex-wrap items-center gap-3">
                <Button type="button" disabled={busy || !isAdmin} onClick={() => setConfirmPay(true)}>
                  {busy ? "…" : ar ? "تأكيد التجربة المجانية" : "Confirmer l'essai gratuit"}
                </Button>
                <strong className="text-sm text-[#0A1228]">
                  {ar ? "0 درهم اليوم" : "0 MAD débités aujourd'hui"}
                </strong>
              </div>
              <label className="mt-4 flex items-start gap-2 text-xs text-slate-600">
                <input
                  type="checkbox"
                  className="mt-0.5"
                  checked={agreed}
                  onChange={(e) => setAgreed(e.target.checked)}
                />
                <span>
                  {ar ? "أوافق على " : "J'accepte les "}
                  <a
                    href={legalHref("/mentions-legales")}
                    onClick={persistDraft}
                    className="text-[#1B3F9C] underline"
                  >
                    {ar ? "شروط الاستخدام" : "conditions d'utilisation"}
                  </a>
                  {", "}
                  <a
                    href={legalHref("/remboursement")}
                    onClick={persistDraft}
                    className="text-[#1B3F9C] underline"
                  >
                    {ar ? "سياسة الاسترداد" : "politique de remboursement"}
                  </a>
                  {ar ? " و" : " et la "}
                  <a
                    href={legalHref("/confidentialite")}
                    onClick={persistDraft}
                    className="text-[#1B3F9C] underline"
                  >
                    {ar ? "سياسة الخصوصية" : "politique de confidentialité"}
                  </a>
                  .
                </span>
              </label>
            </div>
          </div>

          <aside className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {ar ? "اختياركم" : "Votre sélection"}
              </p>
              <p className="mt-2 text-lg font-semibold text-[#0A1228]">{planName}</p>
              {plan && planTrialBadge(plan, ar) ? (
                <span className="mt-2 inline-flex rounded-full bg-emerald-50 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-800">
                  {planTrialBadge(plan, ar)}
                </span>
              ) : null}

              <div className="mt-4 flex flex-wrap gap-2">
                {paidPlans.map((p) => {
                  const active = p.slug === planSlug;
                  const lbl = ar && p.name_ar ? p.name_ar : p.name;
                  return (
                    <button
                      key={p.slug}
                      type="button"
                      onClick={() => switchPlan(p.slug)}
                      className={`rounded-lg border px-3 py-1.5 text-xs font-semibold transition ${
                        active
                          ? "border-[#1B3F9C] bg-[#1B3F9C] text-white"
                          : "border-slate-200 bg-white text-slate-600 hover:border-[#1B3F9C]/40"
                      }`}
                    >
                      {lbl}
                    </button>
                  );
                })}
              </div>

              <div className="mt-3 flex rounded-lg border border-slate-200 p-0.5 text-xs">
                <button
                  type="button"
                  className={`flex-1 rounded-md py-1.5 font-semibold ${cycle === "monthly" ? "bg-[#0A1228] text-white" : ""}`}
                  onClick={() => switchPlan(planSlug, "monthly")}
                >
                  {ar ? "شهري" : "Mensuel"}
                </button>
                <button
                  type="button"
                  className={`flex-1 rounded-md py-1.5 font-semibold ${cycle === "yearly" ? "bg-[#0A1228] text-white" : ""}`}
                  onClick={() => switchPlan(planSlug, "yearly")}
                >
                  {ar ? "سنوي" : "Annuel"}
                </button>
              </div>
              {yearlySave > 0 && cycle === "monthly" ? (
                <button
                  type="button"
                  onClick={() => switchPlan(planSlug, "yearly")}
                  className="mt-2 flex w-full items-center justify-center gap-1.5 rounded-lg bg-[#FF6A00]/10 px-3 py-2 text-xs font-semibold text-[#FF6A00] hover:bg-[#FF6A00]/15"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  {ar
                    ? `Économisez ${yearlySave} MAD/an`
                    : `Économisez ${yearlySave.toLocaleString("fr-FR")} MAD/an en passant annuel`}
                </button>
              ) : null}

              {highlights.length ? (
                <ul className="mt-4 space-y-1.5 border-t border-slate-100 pt-3">
                  {highlights.map((h) => (
                    <li key={h} className="flex gap-2 text-xs text-slate-600">
                      <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600" />
                      <span>{h}</span>
                    </li>
                  ))}
                </ul>
              ) : null}

              <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-4 text-sm">
                <span>{cycle === "yearly" ? (ar ? "اشتراك سنوي" : "Abonnement annuel") : ar ? "اشتراك شهري" : "Abonnement mensuel"}</span>
                <span className="font-semibold">
                  {ar ? `تجربة ${trialDays} يومًا` : `Essai ${trialDays} jours`}
                </span>
              </div>
              <p className="mt-1 text-end text-xs text-slate-500">
                {ar
                  ? `ثم ${price.toLocaleString("fr-FR")} درهم / ${cycle === "yearly" ? "سنة" : "شهر"}`
                  : `puis ${price.toLocaleString("fr-FR")} MAD / ${cycle === "yearly" ? "an" : "mois"}`}
              </p>
              <div className="mt-4 flex items-center justify-between text-base font-bold text-[#0A1228]">
                <span>{ar ? "المجموع اليوم" : "Total aujourd'hui"}</span>
                <span className="text-emerald-700">{ar ? "0 درهم" : "0 MAD"}</span>
              </div>
              <p className="mt-3 text-[11px] leading-relaxed text-slate-500">
                {ar
                  ? `ألغوا قبل ${endLabel} ولن تُخصم بطاقتكم.`
                  : `Annulez avant le ${endLabel} et votre carte ne sera pas débitée.`}
              </p>
              <Link
                href="/tarifs"
                className="mt-4 flex items-center justify-center gap-1.5 text-xs font-semibold text-[#1B3F9C] hover:underline"
              >
                <ArrowLeftRight className="h-3.5 w-3.5" />
                {ar ? "مقارنة كل الخطط" : "Comparer tous les plans"}
              </Link>
            </div>

            <div className="rounded-2xl border border-[#1B3F9C]/15 bg-[#1B3F9C]/5 p-5 text-sm">
              <p className="flex items-center gap-2 font-semibold text-[#0A1228]">
                <MapPin className="h-4 w-4 text-[#1B3F9C]" />
                {ar ? "لماذا الآن؟" : "Pourquoi maintenant ?"}
              </p>
              <ul className="mt-2 space-y-1.5 text-xs text-slate-600">
                <li>
                  ·{" "}
                  {ar
                    ? "تحليل إملائكم + قطع الملف — أفضل مرافعة ممكنة"
                    : "Analyse de votre dictée + pièces du dossier — la meilleure plaidoirie possible"}
                </li>
                <li>
                  ·{" "}
                  {ar
                    ? "إخفاء أسماء الأطراف قبل الذكاء الاصطناعي ثم استعادتها في الوثيقة"
                    : "Noms des parties masqués avant l’IA, puis restaurés dans le document"}
                </li>
                <li>
                  ·{" "}
                  {ar
                    ? "تلخيص، فريق وملفات مركزية — 0 درهم اليوم، الاشتراك بعد التجربة"
                    : "Synthèse, équipe et dossiers centralisés — 0 MAD aujourd’hui, abonnement après l’essai"}
                </li>
              </ul>
            </div>
          </aside>
        </div>
      </div>

      <ConfirmActionModal
        open={confirmPay}
        onClose={() => setConfirmPay(false)}
        ar={ar}
        busy={busy}
        tag={ar ? "دفع" : "Paiement"}
        title={ar ? `تأكيد تجربة ${planName}؟` : `Confirmer l’essai ${planName} ?`}
        points={
          ar
            ? [
                "0 درهم اليوم — البطاقة تُسجَّل فقط",
                `${trialDays} يومًا كاملة على الخطة`,
                "ألغوا قبل نهاية التجربة ولن يُخصم شيء",
              ]
            : [
                "0 MAD aujourd’hui — la carte est seulement enregistrée",
                `${trialDays} jours complets sur ce plan`,
                "Résiliez avant la fin : aucun débit",
              ]
        }
        primaryLabel={ar ? "نعم، بدء التجربة" : "Oui, démarrer l’essai"}
        onConfirm={() => {
          setConfirmPay(false);
          void submit();
        }}
      />
      <PaymentSuccessModal
        open={successOpen}
        ar={ar}
        planName={planName}
        trialDays={trialDays}
        invoiceNumber={successData.invoiceNumber}
        invoiceHtml={successData.invoiceHtml}
        onClose={() => router.push("/settings#abonnement")}
      />
    </div>
  );
}

export default function CheckoutPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">…</div>}>
      <CheckoutInner />
    </Suspense>
  );
}
