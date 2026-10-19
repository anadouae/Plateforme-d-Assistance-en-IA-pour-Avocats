"use client";



import Link from "next/link";

import { useEffect, useMemo, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";

import {

  Building2,

  Check,

  CreditCard,

  FilePenLine,

  Headphones,

  Landmark,

  Lock,

  Scale,

  Server,

  Smartphone,

  Sparkles,

  User,

  Users,

} from "lucide-react";

import { PublicNavbar } from "@/components/layout/public-navbar";
import { VisitorConvertNudge } from "@/components/billing/visitor-convert-nudge";

import { TrialPitchModal } from "@/components/billing/trial-pitch-modal";
import { AuthGateModal } from "@/components/billing/auth-gate-modal";
import { AskAdminBillingModal } from "@/components/billing/ask-admin-billing";
import { Button } from "@/components/ui/button";

import { api, type BillingPlan } from "@/lib/api";

import {

  FALLBACK_BILLING_PLANS,

} from "@/lib/billing-plans-fallback";
import { saveBillingIntent, checkoutHref } from "@/lib/billing-intent";
import { planCtaLabel, planCtaSub, planTrialBadge } from "@/lib/plan-cta";

import { canManageTeam } from "@/lib/roles";

import { useAuthStore } from "@/store/auth";

import { useClientLocale, useTranslations } from "@/store/locale";



/** Icônes type maquette : 1 personne = Solo, groupe = Cabinet */

function PlanIcon({ slug }: { slug: string }) {

  const cls = "h-7 w-7";

  if (slug === "free") return <FilePenLine className={cls} strokeWidth={1.6} />;

  if (slug === "solo") return <User className={cls} strokeWidth={1.6} />;

  if (slug === "pro" || slug === "cabinet") return <Users className={cls} strokeWidth={1.6} />;

  if (slug === "enterprise") return <Building2 className={cls} strokeWidth={1.6} />;

  return <Scale className={cls} strokeWidth={1.6} />;

}



export default function TarifsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#F4F6FA]" />}>
      <TarifsPageInner />
    </Suspense>
  );
}

function TarifsPageInner() {

  const locale = useClientLocale();

  const ar = locale === "ar";

  const t = useTranslations();

  const p = t.pricing;

  const user = useAuthStore((s) => s.user);

  const loggedIn = !!user;

  const isAdmin = canManageTeam(user?.role);
  const searchParams = useSearchParams();

  const [plans, setPlans] = useState<BillingPlan[]>([]);

  const [cycle, setCycle] = useState<"monthly" | "yearly">("monthly");
  const [pitchPlan, setPitchPlan] = useState<BillingPlan | null>(null);
  const [authPlan, setAuthPlan] = useState<BillingPlan | null>(null);
  const [askAdmin, setAskAdmin] = useState(false);

  const [methods, setMethods] = useState<

    { id: string; name: string; name_ar?: string; status: string; blurb: string }[]

  >([]);



  useEffect(() => {

    api

      .getBillingPlans()

      .then((list) => setPlans(list.length ? list : FALLBACK_BILLING_PLANS))

      .catch(() => setPlans(FALLBACK_BILLING_PLANS));

    api

      .getPaymentMethods()

      .then((r) => setMethods(r.methods || []))

      .catch(() => setMethods([]));

  }, []);



  useEffect(() => {
    const pick = searchParams.get("pick");
    const urlCycle = searchParams.get("cycle");
    if (urlCycle === "yearly" || urlCycle === "monthly") setCycle(urlCycle);
    if (!pick || !plans.length) return;
    const match = plans.find((p) => p.slug === pick);
    if (!match) return;
    const authed = useAuthStore.getState().isAuthenticated();
    const role = useAuthStore.getState().user?.role;
    if (authed && !canManageTeam(role) && match.slug !== "free") {
      setAskAdmin(true);
      return;
    }
    setPitchPlan(match);
  }, [searchParams, plans]);

  function choosePlan(plan: BillingPlan) {
    saveBillingIntent({ plan: plan.slug, cycle, intent: plan.slug === "free" ? "free" : "trial" });
    const authed = loggedIn || useAuthStore.getState().isAuthenticated();
    const role = useAuthStore.getState().user?.role;
    // Membre connecté (assistant / avocat) : pas d’essai ni checkout — prévenir l’admin
    if (authed && !canManageTeam(role) && plan.slug !== "free") {
      setAskAdmin(true);
      return;
    }
    if (plan.slug === "free" && authed) {
      window.location.assign("/dashboard");
      return;
    }
    setPitchPlan(plan);
  }

  function afterPitch() {
    const plan = pitchPlan;
    setPitchPlan(null);
    if (!plan) return;
    if (plan.slug === "free") {
      if (!loggedIn && !useAuthStore.getState().isAuthenticated()) setAuthPlan(plan);
      else window.location.assign("/dashboard");
      return;
    }
    // Token plat / store : évite AuthGate si l’hydratation Zustand n’est pas finie
    const authed = loggedIn || useAuthStore.getState().isAuthenticated();
    if (!authed) {
      setAuthPlan(plan);
      return;
    }
    const role = useAuthStore.getState().user?.role;
    if (canManageTeam(role)) {
      window.location.assign(checkoutHref(plan.slug, cycle));
    } else {
      setAskAdmin(true);
    }
  }



  const displayPlans = useMemo(

    () => (plans.length ? plans : FALLBACK_BILLING_PLANS),

    [plans],

  );



  const price = (plan: BillingPlan) =>

    cycle === "yearly" ? plan.price_mad_yearly : plan.price_mad_monthly;



  const planName = (plan: BillingPlan) =>

    ar && plan.name_ar ? plan.name_ar : plan.name;



  const statusLabel = (s: string) => {

    if (s === "manual") return p.payManual;

    if (s === "coming_soon") return p.paySoon;

    if (s === "env_ready") return p.payReady || (ar ? "جاهز تقنياً" : "Prêt — activation opérateur");

    return s;

  };



  return (

    <div className="min-h-screen bg-[#F4F6FA]" dir={ar ? "rtl" : "ltr"}>

      <PublicNavbar />
      <VisitorConvertNudge />

      <main className="relative overflow-hidden">

        <div

          className="pointer-events-none absolute inset-x-0 top-0 h-[380px] bg-[radial-gradient(ellipse_at_top,_rgba(255,106,0,0.12),_transparent_55%)]"

          aria-hidden

        />

        <div className="relative mx-auto max-w-6xl px-4 py-14 sm:px-6">

          <div className="mx-auto max-w-2xl text-center">

            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#FF6A00]">

              LexHub · LegalTech Maroc

            </p>

            <h1 className="mt-3 font-display text-3xl font-semibold tracking-tight text-[#0A1228] sm:text-4xl md:text-5xl">

              {ar

                ? "الباقة المناسبة لمكتبكم"

                : "La suite LegalTech pensée pour les cabinets au Maroc"}

            </h1>

            <p className="mt-4 text-base leading-relaxed text-slate-600">

              {ar

                ? "وفّروا الوقت. أمّنوا الملفات. طوّروا نشاطكم."

                : "Gagnez du temps. Sécurisez vos dossiers. Développez votre activité."}

            </p>

            <p className="mt-2 text-sm text-slate-500">{p.trialNote}</p>

            {loggedIn ? (

              <p className="mt-3 text-sm font-medium text-[#0A1228]">

                {isAdmin

                  ? ar

                    ? "أنت مسجّل — اختر خطة للانتقال إلى الدفع."

                    : "Vous êtes connecté — choisissez un plan pour accéder au paiement."

                  : ar

                    ? "أنت مسجّل — اطلب من مدير المكتب ترقية الاشتراك."

                    : "Vous êtes connecté — demandez à l'admin cabinet de gérer l'abonnement."}

              </p>

            ) : null}

            <div className="mt-7 inline-flex rounded-full border border-[#0A1228]/10 bg-white p-1 shadow-sm">

              <button

                type="button"

                className={`rounded-full px-5 py-2 text-sm font-medium transition ${

                  cycle === "monthly" ? "bg-[#0A1228] text-white" : "text-slate-600"

                }`}

                onClick={() => setCycle("monthly")}

              >

                {p.monthly}

              </button>

              <button

                type="button"

                className={`rounded-full px-5 py-2 text-sm font-medium transition ${

                  cycle === "yearly" ? "bg-[#0A1228] text-white" : "text-slate-600"

                }`}

                onClick={() => setCycle("yearly")}

              >

                {p.yearly}

              </button>

            </div>

          </div>



          <div className="mt-12 grid gap-5 md:grid-cols-2 xl:grid-cols-5">

            {displayPlans.map((plan) => {

              const amt = price(plan);

              const recommended = plan.is_recommended;

              const highlights =

                ar && plan.highlights_ar?.length

                  ? plan.highlights_ar

                  : plan.highlights?.length

                    ? plan.highlights

                    : [

                        `${plan.max_avocats} ${p.lawyers} · ${plan.max_assistants} ${p.assistants}`,

                        plan.max_cases < 0

                          ? ar

                            ? "ملفات غير محدودة"

                            : "Dossiers illimités"

                          : ar

                            ? `حتى ${plan.max_cases} ملفات`

                            : `Jusqu'à ${plan.max_cases} dossiers`,

                        plan.max_plaidoiries_month < 0

                          ? p.unlimitedPleas

                          : `${plan.max_plaidoiries_month} ${p.pleasMonth}`,

                      ];

              const label = planCtaLabel(plan, ar, { loggedIn });
              const sub = planCtaSub(plan, ar);
              const trialBadge = planTrialBadge(plan, ar);



              return (

                <div

                  key={plan.id}

                  className={`relative flex flex-col rounded-2xl border bg-white p-6 transition ${

                    recommended

                      ? "border-[#FF6A00] shadow-[0_16px_40px_-20px_rgba(255,106,0,0.55)] ring-1 ring-[#FF6A00]/25"

                      : "border-slate-200/90 shadow-[0_12px_32px_-24px_rgba(10,18,40,0.35)]"

                  }`}

                >

                  {recommended ? (

                    <span className="absolute -top-3 start-1/2 z-10 -translate-x-1/2 inline-flex items-center gap-1 rounded-full bg-[#FF6A00] px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-white">

                      <Sparkles className="h-3 w-3" />

                      {ar ? "الأكثر شعبية" : "Le plus populaire"}

                    </span>

                  ) : null}



                  <div

                    className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl ${

                      recommended

                        ? "bg-[#FF6A00]/10 text-[#FF6A00]"

                        : "bg-[#0A1228]/5 text-[#0A1228]"

                    }`}

                  >

                    <PlanIcon slug={plan.slug} />

                  </div>



                  <h2 className="text-lg font-semibold uppercase tracking-wide text-[#0A1228]">

                    {planName(plan)}

                  </h2>

                  <p className="mt-2 min-h-[3rem] text-sm leading-relaxed text-slate-600">

                    {plan.description}

                  </p>

                  <p className="mt-5 flex items-baseline gap-1">

                    <span className="text-4xl font-semibold tracking-tight text-[#0A1228]">

                      {amt === 0 ? "0" : amt.toLocaleString(ar ? "ar-MA" : "fr-FR")}

                    </span>

                    <span className="text-sm text-slate-500">

                      {amt === 0 ? p.madFree : `${p.mad}/${cycle === "yearly" ? p.year : p.month}`}

                    </span>

                  </p>

                  {trialBadge ? (
                    <span className="mt-2 inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">
                      {trialBadge}
                    </span>
                  ) : null}

                  <ul className="mt-5 flex-1 space-y-2.5">

                    {highlights.map((h) => (

                      <li key={h} className="flex items-start gap-2 text-sm text-slate-700">

                        <Check

                          className={`mt-0.5 h-4 w-4 shrink-0 ${

                            recommended ? "text-[#FF6A00]" : "text-[#0A1228]"

                          }`}

                        />

                        <span>{h}</span>

                      </li>

                    ))}

                  </ul>

                  <div className="mt-6">
                    <Button
                      type="button"
                      className={`w-full rounded-xl font-semibold ${
                        recommended
                          ? "bg-[#FF6A00] text-white hover:bg-[#E85A00]"
                          : "border-[#0A1228]/20 text-[#0A1228]"
                      }`}
                      variant={recommended ? "default" : "outline"}
                      onClick={() => choosePlan(plan)}
                    >
                      {label}
                    </Button>
                    {sub ? (
                      <p className="mt-2 text-center text-[11px] text-slate-500">{sub}</p>
                    ) : null}
                  </div>

                </div>

              );

            })}

          </div>



          <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

            {[
              {
                Icon: Lock,
                title: ar ? "حسابات مؤمّنة" : "Comptes sécurisés",
                body: ar
                  ? "كلمة مرور قوية، تحقق بالبريد، وإمكانية التفعيل الثنائي (2FA)"
                  : "Mot de passe fort, e-mail vérifié, double authentification (2FA) disponible",
              },
              {
                Icon: Server,
                title: ar ? "سرية المكتب" : "Confidentialité cabinet",
                body: ar
                  ? "كل مكتب معزول: ملفاته ومرافعاته غير مرئية للمكاتب الأخرى"
                  : "Chaque cabinet est isolé : dossiers et plaidoiries invisibles aux autres",
              },
              {
                Icon: Headphones,
                title: ar ? "دعم LexHub" : "Support LexHub",
                body: ar
                  ? "فريق جاهز عبر مركز المساعدة والاتصال"
                  : "Équipe joignable via le centre d’aide et le formulaire contact",
              },
              {
                Icon: Scale,
                title: ar ? "مخصص للمحامين" : "Fait pour les avocats",
                body: ar
                  ? "إملاء عربي، مرافعات، ملفات وفريق — في منصة واحدة"
                  : "Dictée arabe, plaidoiries, dossiers et équipe — une seule plateforme",
              },
            ].map(({ Icon, title, body }) => (

              <div

                key={title}

                className="flex gap-3 rounded-2xl border border-slate-200/80 bg-white px-4 py-4"

              >

                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#0A1228]/5 text-[#0A1228]">

                  <Icon className="h-5 w-5" strokeWidth={1.6} />

                </div>

                <div>

                  <p className="text-sm font-semibold text-[#0A1228]">{title}</p>

                  <p className="mt-0.5 text-xs text-slate-500">{body}</p>

                </div>

              </div>

            ))}

          </div>



          <section className="mt-14 rounded-2xl border border-slate-200/80 bg-white p-8">

            <h2 className="text-xl font-semibold text-[#0A1228]">{p.paymentsTitle}</h2>

            <p className="mt-2 max-w-2xl text-sm text-slate-600">{p.paymentsSubtitle}</p>

            <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {(methods.length
                ? methods.filter((m) => m.status !== "manual" && m.id !== "bank_transfer" && m.id !== "virement")
                : [
                    { id: "cmi", name: "CMI", status: "env_ready", blurb: "Cartes bancaires marocaines — environnement prêt, activation opérateur ensuite" },
                    { id: "payzone", name: "PayZone", status: "env_ready", blurb: "Passerelle locale (cartes + mobile) — environnement prêt, pas encore encaissé" },
                    { id: "stripe", name: "Carte internationale", status: "coming_soon", blurb: "Visa / Mastercard — phase suivante" },
                  ]
              ).map((m) => {
                const Icon =
                  m.id === "cmi" || m.id === "stripe"
                    ? CreditCard

                    : m.id === "payzone"

                      ? Smartphone

                      : Landmark;

                return (

                  <div key={m.id} className="rounded-xl border border-slate-100 bg-[#F4F6FA] p-4">

                    <Icon className="h-5 w-5 text-[#0A1228]" />

                    <p className="mt-3 font-semibold text-[#0A1228]">

                      {ar && "name_ar" in m && m.name_ar ? m.name_ar : m.name}

                    </p>

                    <p className="mt-1 text-xs text-slate-500">{m.blurb}</p>

                    <span className="mt-3 inline-block rounded-full bg-[#0A1228]/5 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-[#0A1228]">

                      {statusLabel(m.status)}

                    </span>

                  </div>

                );

              })}

            </div>

          </section>



          <p className="mx-auto mt-10 max-w-2xl text-center text-xs leading-relaxed text-slate-500">

            {p.footer}

          </p>

        </div>

      </main>

      <TrialPitchModal
        open={!!pitchPlan}
        onClose={() => setPitchPlan(null)}
        onContinue={afterPitch}
        plan={pitchPlan}
        cycle={cycle}
        ar={ar}
      />
      <AuthGateModal
        open={!!authPlan}
        onClose={() => setAuthPlan(null)}
        planSlug={authPlan?.slug || "pro"}
        cycle={cycle}
        ar={ar}
      />
      <AskAdminBillingModal open={askAdmin} onClose={() => setAskAdmin(false)} ar={ar} />
    </div>

  );

}


