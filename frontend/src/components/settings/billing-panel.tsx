"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Check, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrialPitchModal } from "@/components/billing/trial-pitch-modal";
import { ConfirmActionModal } from "@/components/billing/confirm-action-modal";
import { InvoicesList } from "@/components/billing/invoices-list";
import {
  PackCheckoutModal,
  type PackCheckoutInfo,
} from "@/components/billing/pack-checkout-modal";
import {
  api,
  ApiError,
  type BillingEntitlements,
  type BillingPlan,
  type PaymentEnv,
} from "@/lib/api";
import { canManageTeam } from "@/lib/roles";
import { checkoutHref } from "@/lib/billing-intent";
import { useAuthStore } from "@/store/auth";
import { useClientLocale } from "@/store/locale";

export function BillingPanel() {
  const user = useAuthStore((s) => s.user);
  const ar = useClientLocale() === "ar";
  const isAdmin = canManageTeam(user?.role);
  const searchParams = useSearchParams();
  const [ent, setEnt] = useState<BillingEntitlements | null>(null);
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [methods, setMethods] = useState<
    { id: string; name: string; name_ar?: string; status: string; blurb: string }[]
  >([]);
  const [reasons, setReasons] = useState<{ code: string; label: string }[]>([]);
  const [cycle, setCycle] = useState<"monthly" | "yearly">("monthly");
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [cancelCode, setCancelCode] = useState("other");
  const [cancelText, setCancelText] = useState("");
  const [showCancel, setShowCancel] = useState(false);
  const [pitchPlan, setPitchPlan] = useState<BillingPlan | null>(null);
  const [confirmKind, setConfirmKind] = useState<null | "cancel">(null);
  const [paymentEnv, setPaymentEnv] = useState<PaymentEnv | null>(null);
  const [history, setHistory] = useState<{
    events: { event_type: string; plan_slug?: string; detail?: string; created_at?: string }[];
    invoices: {
      id: string;
      number: string;
      plan_name: string;
      amount_mad: number;
      status: string;
      issued_at?: string;
      kind?: string;
    }[];
  } | null>(null);
  const [onDemandDraft, setOnDemandDraft] = useState<"disabled" | "enabled" | "capped">("disabled");
  const [madCapDraft, setMadCapDraft] = useState("100");
  const [extraSeatsDraft, setExtraSeatsDraft] = useState("0");
  const [packCheckout, setPackCheckout] = useState<PackCheckoutInfo | null>(null);
  const [addons, setAddons] = useState<{
    credit_packs_available?: boolean;
    show_pack_banner?: boolean;
    nudge_upgrade_before_pack?: boolean;
    pack_lots?: { id: string; credits_remaining: number; expires_at?: string | null }[];
    credit_packs?: BillingEntitlements["credit_packs"];
  } | null>(null);
  const [invBusy, setInvBusy] = useState<string | null>(null);
  const [referral, setReferral] = useState<{
    available: boolean;
    code: string | null;
    share_path?: string;
    rules_fr?: string;
    rules_ar?: string;
    stats?: { invites: number; pending: number; rewarded: number };
  } | null>(null);
  const [copied, setCopied] = useState<"code" | "link" | null>(null);

  function reload() {
    return Promise.all([
      api.getBillingEntitlements(),
      api.getBillingPlans(),
      api.getPaymentMethods().catch(() => ({ methods: [] })),
      api.getCancelReasons().catch(() => [] as { code: string; label: string }[]),
      isAdmin ? api.getBillingHistory().catch(() => null) : Promise.resolve(null),
      isAdmin ? api.getPaymentEnv().catch(() => null) : Promise.resolve(null),
      api.getReferral().catch(() => null),
      isAdmin ? api.getBillingAddons().catch(() => null) : Promise.resolve(null),
    ]).then(([e, p, pay, r, h, env, ref, ad]) => {
      setEnt(e);
      setPlans(p);
      setMethods(pay.methods || []);
      setReasons(r);
      if (h) setHistory(h);
      if (env) setPaymentEnv(env);
      if (ref) setReferral(ref);
      if (ad) setAddons(ad);
      if (e.on_demand_enabled) {
        if (e.on_demand_mad_limit != null && e.on_demand_mad_limit >= 0) {
          setOnDemandDraft("capped");
          setMadCapDraft(String(e.on_demand_mad_limit));
        } else {
          setOnDemandDraft("enabled");
        }
      } else {
        setOnDemandDraft("disabled");
      }
      setExtraSeatsDraft(String(e.extra_avocat_seats ?? 0));
    });
  }

  useEffect(() => {
    void reload().catch(() => {});
    const onFocus = () => void reload().catch(() => {});
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [isAdmin]);

  useEffect(() => {
    if (ent?.billing_cycle === "yearly" || ent?.billing_cycle === "monthly") {
      setCycle(ent.billing_cycle);
    }
  }, [ent?.billing_cycle]);

  useEffect(() => {
    const slug = searchParams.get("checkout");
    const urlCycle = searchParams.get("cycle");
    if (urlCycle === "yearly" || urlCycle === "monthly") setCycle(urlCycle);
    if (!slug || !isAdmin || !plans.length) return;
    const match = plans.find((p) => p.slug === slug);
    if (match && match.slug !== "free") {
      setPitchPlan(match);
    }
  }, [searchParams, plans, isAdmin]);

  function openCheckout(slug: string) {
    if (user?.must_set_password && !user?.auth_via_google) {
      setError(
        ar
          ? "أنشئوا كلمة مرور أولاً (شريط أصفر أعلى الصفحة) قبل الاشتراك."
          : "Créez d’abord un mot de passe (bandeau jaune) avant un abonnement.",
      );
      return;
    }
    const match = plans.find((p) => p.slug === slug);
    if (match) setPitchPlan(match);
  }

  function goToCheckout(plan: BillingPlan) {
    if (user?.must_set_password && !user?.auth_via_google) {
      setError(
        ar
          ? "أنشئوا كلمة مرور أولاً قبل الاشتراك."
          : "Créez d’abord un mot de passe avant un abonnement.",
      );
      return;
    }
    window.location.assign(checkoutHref(plan.slug, cycle));
  }

  async function choose(slug: string) {
    if (!isAdmin) {
      setError(ar ? "فقط مدير المكتب يمكنه تغيير الخطة." : "Seul l'admin cabinet peut changer de plan.");
      return;
    }
    if (slug === "free") {
      setBusy(slug);
      setError("");
      setMessage("");
      try {
        const res = await api.selectBillingPlan(slug, cycle);
        setMessage(res.message);
        await reload();
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Erreur");
      } finally {
        setBusy(null);
      }
      return;
    }
    const plan = plans.find((p) => p.slug === slug);
    const isPaid = plan && (cycle === "yearly" ? plan.price_mad_yearly : plan.price_mad_monthly) > 0;
    if (isPaid) {
      openCheckout(slug);
      return;
    }
    setBusy(slug);
    setError("");
    setMessage("");
    try {
      const res = await api.selectBillingPlan(slug, cycle);
      setMessage(res.message);
      await reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur");
    } finally {
      setBusy(null);
    }
  }

  async function submitCancel() {
    setBusy("cancel");
    setError("");
    try {
      const res = await api.cancelSubscription(cancelCode, cancelText);
      setMessage(res.message);
      setShowCancel(false);
      await reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur");
    } finally {
      setBusy(null);
    }
  }

  async function makeInvoice() {
    setBusy("invoice");
    try {
      const inv = await api.generateInvoice();
      const w = window.open("", "_blank");
      if (w && inv.html) {
        w.document.write(inv.html);
        w.document.close();
      }
      setMessage(ar ? `فاتورة ${inv.number}` : `Facture ${inv.number}`);
      await reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur facture");
    } finally {
      setBusy(null);
    }
  }

  async function saveOnDemand() {
    if (!isAdmin) return;
    setBusy("on-demand");
    setError("");
    setMessage("");
    try {
      const enabled = onDemandDraft !== "disabled";
      const mad_limit =
        onDemandDraft === "disabled"
          ? undefined
          : onDemandDraft === "enabled"
            ? -1
            : Math.max(0, Math.round(Number(madCapDraft) || 0));
      const res = await api.updateOnDemandSettings(enabled, mad_limit);
      setMessage(
        res.message ||
          (enabled
            ? ar
              ? "تم تفعيل الاستخدام عند الطلب — الزائد يُضاف للفاتورة."
              : "Usage à la demande activé — le surplus ira sur la facture."
            : ar
              ? "تم تعطيل الاستخدام عند الطلب."
              : "Usage à la demande désactivé."),
      );
      await reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur");
    } finally {
      setBusy(null);
    }
  }

  async function buyPack(packId: string) {
    if (!isAdmin) return;
    setBusy(`pack:${packId}`);
    setError("");
    setMessage("");
    try {
      const checkout = await api.checkoutCreditPack(packId);
      setPackCheckout({
        purchase_id: checkout.purchase_id,
        pack_id: checkout.pack_id,
        credits: checkout.credits,
        amount_mad: checkout.amount_mad,
        unit_mad: checkout.unit_mad,
        label: checkout.label,
        expires_hint: checkout.expires_hint,
        expires_after_months: checkout.expires_after_months,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur");
    } finally {
      setBusy(null);
    }
  }

  async function saveExtraSeats() {
    if (!isAdmin) return;
    setBusy("extra-seats");
    setError("");
    setMessage("");
    try {
      const qty = Math.max(0, Math.min(5, Math.round(Number(extraSeatsDraft) || 0)));
      const res = await api.updateExtraSeats(qty);
      setMessage(res.message || (ar ? "تم تحديث المقاعد." : "Sièges mis à jour."));
      await reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur");
    } finally {
      setBusy(null);
    }
  }

  if (!ent?.plan) {
    return (
      <Card id="abonnement">
        <CardHeader>
          <CardTitle>{ar ? "الاشتراك" : "Abonnement"}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">…</p>
        </CardContent>
      </Card>
    );
  }

  const u = ent.usage || {};
  function priceOf(p: BillingPlan) {
    return cycle === "yearly" ? p.price_mad_yearly : p.price_mad_monthly;
  }
  function planLabel(p: BillingPlan) {
    return ar && p.name_ar ? p.name_ar : p.name;
  }
  const currentSlug = ent.plan && "slug" in ent.plan ? String(ent.plan.slug || "free") : "free";
  const onDemandAvailable = ent.on_demand_available !== false && currentSlug !== "free";
  const madPerCredit = ent.on_demand_mad_per_credit ?? 0.25;
  const overageMad = u.ai_overage_mad_estimate ?? 0;
  const creditsUsed = u.ai_credits_used ?? 0;
  const creditsLim = u.ai_credits_limit ?? -1;
  const creditsPct =
    creditsLim < 0 ? 0 : Math.min(100, Math.round((creditsUsed / Math.max(creditsLim, 1)) * 100));
  const dailyLim = ent.ai_daily_limit ?? 0;
  const dailyUsed = ent.ai_daily_used ?? 0;
  const dailyPct =
    dailyLim > 0 ? Math.min(100, Math.round((dailyUsed / Math.max(dailyLim, 1)) * 100)) : 0;
  const upgradePlan = plans.find((p) => p.slug !== currentSlug && priceOf(p) > 0 && p.is_recommended)
    || plans.find((p) => p.slug !== currentSlug && priceOf(p) > 0);
  const inTrial = ent.status === "trial";

  return (
    <div id="abonnement" className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold tracking-tight text-[#0B1A4D]">
          {ar ? "الخطة والاستخدام" : isAdmin ? "Plan & usage" : "Usage du cabinet"}
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          {ar
            ? isAdmin
              ? inTrial
                ? "التجربة مجانية بسقف استخدام أقل من الاشتراك المدفوع. الدفع يبدأ بعد نهاية التجربة."
                : "إدارة الاشتراك، الحصص، والاستخدام الإضافي على الفاتورة."
              : "عرض حصص المكتب هذا الشهر (بدون إدارة الاشتراك)."
            : isAdmin
              ? inTrial
                ? "Essai gratuit avec plafond d’usage (inférieur au forfait payant). Aucun paiement tant que l’essai n’est pas terminé."
                : "Gérez votre abonnement, vos quotas, et le surplus facturé."
              : "Consommation du mois pour votre cabinet (sans gérer l’abonnement)."}
        </p>
      </div>

      {/* Plan cards — style Cursor */}
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            {ar ? "خطتكم" : "Votre plan"}
          </p>
          <p className="mt-2 text-2xl font-semibold text-[#0B1A4D]">
            {"name" in ent.plan ? (ar && (ent.plan as BillingPlan).name_ar) || ent.plan.name : ""}
            {ent.plan && "price_mad_monthly" in ent.plan && (ent.plan as BillingPlan).price_mad_monthly > 0
              ? ` · ${(ent.plan as BillingPlan).price_mad_monthly} MAD/mois`
              : null}
          </p>
          <p className="mt-1 text-sm text-slate-600">
            {ent.status === "trial"
              ? ar
                ? "تجربة"
                : "Essai"
              : ar
                ? "نشط"
                : "Actif"}
            {ent.trial_days_left != null
              ? ` · ${ent.trial_days_left} ${ar ? "يوم متبقٍ" : "j. restants"}`
              : null}
            {ent.current_period_end
              ? ar
                ? ent.status === "trial"
                  ? ` · نهاية التجربة ${new Date(ent.current_period_end).toLocaleDateString("fr-MA")}`
                  : ` · التجديد ${new Date(ent.current_period_end).toLocaleDateString("fr-MA")}`
                : ent.status === "trial"
                  ? ` · Fin d’essai ${new Date(ent.current_period_end).toLocaleDateString("fr-FR")}`
                  : ` · Renouvellement ${new Date(ent.current_period_end).toLocaleDateString("fr-FR")}`
              : null}
          </p>
          {isAdmin ? (
            <div className="mt-4 flex flex-wrap gap-2">
              <Link href="/tarifs">
                <Button type="button" size="sm" variant="outline">
                  {ar ? "تعديل الخطة" : "Ajuster le plan"}
                </Button>
              </Link>
            </div>
          ) : null}
        </div>

        {isAdmin && upgradePlan && currentSlug !== upgradePlan.slug ? (
          <div className="rounded-2xl border border-[#1B3F9C]/25 bg-gradient-to-br from-[#F7F8FC] to-white p-5 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-[#1B3F9C]">
              {ar ? "ترقية" : "Upgrade"}
            </p>
            <p className="mt-2 text-2xl font-semibold text-[#0B1A4D]">
              {planLabel(upgradePlan)} · {priceOf(upgradePlan)} MAD
              <span className="text-sm font-normal text-slate-500">
                /{cycle === "yearly" ? (ar ? "سنة" : "an") : (ar ? "شهر" : "mois")}
              </span>
            </p>
            <p className="mt-1 text-sm text-slate-600">
              {ar ? "حصص أعلى ومزيد من الاعتمادات للذكاء الاصطناعي." : "Plus de quotas et de crédits IA inclus."}
            </p>
            <Button
              type="button"
              className="mt-4"
              size="sm"
              disabled={!!busy}
              onClick={() => void choose(upgradePlan.slug)}
            >
              {ar ? "ترقية" : "Upgrade"}
            </Button>
          </div>
        ) : isAdmin ? (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/60 p-5">
            <p className="text-sm text-slate-600">
              {ar
                ? "أنتم على أفضل خطة متاحة لهذا المكتب، أو خطتكم الحالية كافية."
                : "Vous êtes sur une offre adaptée — ajustez ci-dessous si besoin."}
            </p>
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/60 p-5">
            <p className="text-sm text-slate-600">
              {ar
                ? "إدارة الاشتراك متاحة لمسؤول المكتب فقط."
                : "La gestion de l’abonnement est réservée à l’avocat admin du cabinet."}
            </p>
          </div>
        )}
      </div>

      {/* Usage — Cursor-like bars + clear notes */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-[#0B1A4D]">
          {inTrial
            ? ar
              ? "الحصص أثناء التجربة (هذا الشهر)"
              : "Quotas pendant l’essai (ce mois)"
            : ar
              ? "الاستخدام هذا الشهر"
              : "Utilisation ce mois"}
        </h3>
        {inTrial ? (
          <p className="mt-1 text-xs leading-relaxed text-slate-500">
            {ar
              ? ent.trial_usage_capped
                ? `التجربة بسقف أقل من الاشتراك المدفوع (مثلاً ${u.ai_credits_limit ?? "—"} رصيد الآن مقابل ${u.paid_ai_credits_limit ?? "—"} بعد التحويل). 0 درهم حتى نهاية التجربة.`
                : "التجربة مجانية: الحصص تُحسب الآن. الدفع يبدأ بعد نهاية التجربة."
              : ent.trial_usage_capped
                ? `Essai plafonné (stratégie coût) : ${u.ai_credits_limit ?? "—"} crédits IA et ${u.plaidoiries_limit ?? "—"} plaidoiries pendant l’essai — le forfait payant remonte à ${u.paid_ai_credits_limit ?? "—"} crédits / ${u.paid_plaidoiries_limit ?? "—"} plaidoiries après conversion. 0 MAD tant que l’essai dure.`
                : "Essai gratuit : quotas du plan, sans facture tant que l’essai n’est pas terminé."}
          </p>
        ) : null}

        <div className="mt-5 space-y-5">
          <UsageBar
            label={ar ? "أرصدة الذكاء الاصطناعي" : "Crédits IA inclus"}
            used={creditsUsed}
            limit={creditsLim}
            pct={creditsPct}
            note={
              onDemandAvailable
                ? ar
                  ? ent.on_demand_enabled
                    ? `تجاوز الحصة يُحسب على الفاتورة (~${madPerCredit} درهم / رصيد).`
                    : `تجاوز الحصة لا يُفوتر إلا إذا فعّلتم « الاستخدام عند الطلب » أدناه (~${madPerCredit} درهم / رصيد).`
                  : ent.on_demand_enabled
                    ? `Au-delà du forfait, le surplus est ajouté à la facture (~${madPerCredit} MAD / crédit).`
                    : `Au-delà du forfait, rien n’est facturé tant que « Usage à la demande » est désactivé. Activez-le ci-dessous (~${madPerCredit} MAD / crédit).`
                : ar
                  ? "خطة الاكتشاف: عند نفاد الحصة، رقّوا إلى Solo أو Cabinet — لا فاتورة إضافية."
                  : "Plan Découverte : quota atteint → upgrade Solo / Cabinet. Pas de surplus facturé."
            }
          />
          {dailyLim > 0 ? (
            <UsageBar
              label={
                ar
                  ? inTrial
                    ? "ذكاء اصطناعي اليوم (خلال التجربة)"
                    : "ذكاء اصطناعي اليوم (اشتراك)"
                  : inTrial
                    ? "IA aujourd’hui (pendant l’essai)"
                    : "IA aujourd’hui (abonnement)"
              }
              used={dailyUsed}
              limit={dailyLim}
              pct={dailyPct}
              note={
                ar
                  ? "نفس المنطق لكل الخطط: مؤشر يومي للإعلام. عند الحد: متابعة أو الانتظار حتى الغد. ليس فاتورة."
                  : inTrial
                    ? `Pendant l’essai « ${ent.plan?.name || currentSlug} » : repère du jour ${dailyLim} crédits (plus bas qu’en payant). Au plafond → popup : continuer ou attendre demain. Pas un impayé.`
                    : `Abonnement « ${ent.plan?.name || currentSlug} » : repère du jour ${dailyLim} crédits. Au plafond → popup : continuer ou attendre demain. Même logique pour Solo / Cabinet / Entreprise. Pas un impayé.`
              }
            />
          ) : null}
          <UsageBar
            label={ar ? "مرافعات" : "Plaidoiries"}
            used={u.plaidoiries_used ?? 0}
            limit={u.plaidoiries_limit ?? -1}
            note={
              ar
                ? "كل صياغة مرافعة تستهلك أرصدة وخانة من حصة المرافعات."
                : "Chaque rédaction consomme des crédits et une unité du quota plaidoiries."
            }
          />
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <Meter label={ar ? "تلخيصات" : "Synthèses"} used={u.synthesis_used ?? 0} limit={u.synthesis_limit ?? -1} />
            <Meter label={ar ? "تعديلات" : "Révisions"} used={u.revise_used ?? 0} limit={u.revise_limit ?? -1} />
            <Meter label={ar ? "تحليل" : "Analyses"} used={u.analyse_used ?? 0} limit={u.analyse_limit ?? -1} />
            <Meter label={ar ? "أسئلة" : "Questions"} used={u.ask_used ?? 0} limit={u.ask_limit ?? -1} />
            <Meter label={ar ? "محامون" : "Avocats"} used={u.avocats_used ?? 0} limit={u.avocats_limit ?? 1} />
            <Meter label={ar ? "مساعدون" : "Assistants"} used={u.assistants_used ?? 0} limit={u.assistants_limit ?? 0} />
          </div>
        </div>

        <p className="mt-4 text-[11px] leading-relaxed text-slate-500">
          {isAdmin
            ? ar
              ? "وزن الأرصدة: صياغة 10، تعديل 5، تحليل 8، تلخيص 4، سؤال 2."
              : "Pondération crédits : rédaction 10, révision 5, analyse 8, synthèse 4, question 2."
            : ar
              ? "الأرصدة تُحسب تلقائياً حسب استخدام المحامين للذكاء الاصطناعي."
              : "Les crédits sont comptés automatiquement selon l’usage IA des avocats."}
        </p>
      </div>

      {/* On-demand — admin cabinet only */}
      {isAdmin ? (
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-[#0B1A4D]">
              {ar ? "الاستخدام عند الطلب" : "Usage à la demande"}
            </h3>
            <p className="mt-1 max-w-xl text-sm leading-relaxed text-slate-600">
              {onDemandAvailable
                ? ar
                  ? `عند تفعيله: كل رصيد يتجاوز حصة الخطة يُضاف بوضوح إلى فاتورتكم (~${madPerCredit} درهم / رصيد). عند التعطيل: التوقف عند الحد — بدون مفاجآت على الفاتورة.`
                  : `Quand c’est activé : chaque crédit au-delà du forfait est ajouté clairement à votre facture (~${madPerCredit} MAD / crédit). Quand c’est désactivé : arrêt net au plafond — aucun surplus sur la facture.`
                : ar
                  ? "غير متاح على خطة الاكتشاف. رقّوا إلى Solo أو Cabinet أولاً."
                  : "Indisponible sur Découverte. Passez d’abord à Solo ou Cabinet."}
            </p>
          </div>
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              ent.on_demand_enabled
                ? "bg-emerald-50 text-emerald-800"
                : "bg-slate-100 text-slate-700"
            }`}
          >
            {ent.on_demand_enabled
              ? ar
                ? "مفعّل"
                : "Activé"
              : ar
                ? "معطّل"
                : "Désactivé"}
          </span>
        </div>

        {overageMad > 0 ? (
          <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50/80 px-4 py-3 text-sm text-amber-950">
            {ar
              ? `فائض هذا الشهر ≈ ${overageMad} درهم (${u.ai_overage_credits ?? 0} رصيد) — سيُدرج في الفاتورة.`
              : `Surplus ce mois ≈ ${overageMad} MAD (${u.ai_overage_credits ?? 0} crédits) — sera ajouté à la facture.`}
          </div>
        ) : null}

        {isAdmin && onDemandAvailable ? (
          <div className="mt-5 space-y-3 border-t border-slate-100 pt-4">
            <div className="flex flex-wrap items-end gap-3">
              <div className="min-w-[200px] flex-1">
                <label className="mb-1 block text-xs font-medium text-slate-500">
                  {ar ? "الحد الشهري" : "Plafond mensuel"}
                </label>
                <p className="mb-2 text-[11px] text-slate-500">
                  {ar
                    ? "عطّلوا لتجنب أي مبلغ إضافي، أو حدّدوا سقفًا بالدرهم."
                    : "Désactivez pour zéro surplus, ou fixez un plafond en MAD."}
                </p>
                <select
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
                  value={onDemandDraft}
                  onChange={(e) =>
                    setOnDemandDraft(e.target.value as "disabled" | "enabled" | "capped")
                  }
                >
                  <option value="disabled">{ar ? "معطّل" : "Désactivé"}</option>
                  <option value="enabled">{ar ? "مفعّل · بلا سقف" : "Activé · sans plafond"}</option>
                  <option value="capped">{ar ? "مفعّل · بسقف درهم" : "Activé · plafond MAD"}</option>
                </select>
              </div>
              {onDemandDraft === "capped" ? (
                <div className="w-32">
                  <label className="mb-1 block text-xs font-medium text-slate-500">MAD</label>
                  <input
                    type="number"
                    min={0}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    value={madCapDraft}
                    onChange={(e) => setMadCapDraft(e.target.value)}
                  />
                </div>
              ) : null}
              <Button type="button" disabled={!!busy} onClick={() => void saveOnDemand()}>
                {busy === "on-demand" ? "…" : ar ? "حفظ" : "Enregistrer"}
              </Button>
            </div>
            <p className="rounded-lg bg-[#F7F8FC] px-3 py-2 text-xs leading-relaxed text-slate-600">
              {ar
                ? "مهم: الفائض لا يُخصم صامتًا — يظهر هنا وفي الفاتورة. عطّلوا الخيار إذا أردتم التوقف عند حد الخطة."
                : "Important : le surplus n’est jamais silencieux — il apparaît ici et sur la facture. Gardez l’option désactivée si vous voulez un arrêt net au plafond du plan."}
            </p>
          </div>
        ) : !isAdmin ? (
          <p className="mt-4 text-xs text-slate-500">
            {ar
              ? "فقط مسؤول المكتب يمكنه تفعيل أو تعطيل الاستخدام عند الطلب."
              : "Seul l’admin cabinet peut activer ou désactiver l’usage à la demande."}
          </p>
        ) : null}
      </div>
      ) : null}

      {/* Packs — catalogue visible ; achat seulement après conversion payante */}
      {isAdmin && ((addons?.credit_packs || ent.credit_packs || []).length > 0) ? (
        <div id="packs-credits" className="scroll-mt-24 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          {inTrial && !ent.is_active_paying ? (
            <div className="mb-4 rounded-xl border border-sky-200 bg-sky-50/90 px-4 py-3 text-sm text-sky-950">
              {ar
                ? "الحزم ظاهرة للمعاينة أثناء التجربة. الشراء يُفعَّل بعد التحويل إلى اشتراك مدفوع — أثناء التجربة تُستخدم فقط حصص التجربة."
                : "Les packs sont visibles pendant l’essai (aperçu). L’achat s’active après conversion en abonnement payant — pendant l’essai, seuls les quotas d’essai s’appliquent."}
            </div>
          ) : null}

          {addons?.show_pack_banner ? (
            <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50/90 px-4 py-3 text-sm text-amber-950">
              {ar
                ? "تحتاجون مزيدًا من الأرصدة هذا الشهر؟ يمكنكم شراء حزمة أو تفعيل الاستخدام عند الطلب."
                : "Besoin de plus de crédits ce mois-ci ? Achetez un pack ou activez l’usage à la demande."}
            </div>
          ) : null}

          {addons?.nudge_upgrade_before_pack ? (
            <div className="mb-4 rounded-xl border border-[#1B3F9C]/25 bg-[#F7F9FF] px-4 py-3 text-sm text-[#0B1A4D]">
              <p className="font-semibold">
                {ar ? "اقتراح: الترقية قبل شراء حزم متكررة" : "Conseil : upgrade avant d’enchaîner les packs"}
              </p>
              <p className="mt-1 text-slate-600">
                {ar
                  ? "3 حزم بـ 110 درهم = 330 درهم. خطة Cabinet ★ بـ 699 درهم تشمل 2000 رصيد/شهر."
                  : "3 packs à 110 MAD = 330 MAD. L’upgrade Cabinet ★ à 699 MAD inclut 2 000 crédits / mois."}
              </p>
              <Link href="/tarifs" className="mt-2 inline-block text-sm font-medium text-[#1B3F9C] underline">
                {ar ? "مقارنة الخطط" : "Comparer les plans"}
              </Link>
            </div>
          ) : null}

          <h3 className="text-sm font-semibold text-[#0B1A4D]">
            {ar ? "حزم أرصدة مسبقة الدفع" : "Packs de crédits prépayés"}
          </h3>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-slate-600">
            {ar
              ? `شراء منفصل عن الاشتراك. الدفع عبر نافذة البطاقة — لا تُضاف الأرصدة قبل التأكيد. صلاحية كل حزمة: 12 شهرًا.`
              : `Achat séparé de l’abonnement. Paiement via fenêtre carte — aucun crédit avant confirmation. Chaque pack expire après 12 mois.`}
          </p>
          <p className="mt-3 text-sm font-medium text-[#0B1A4D]">
            {ar ? "رصيد الحزم" : "Solde packs"} :{" "}
            <strong>{ent.prepaid_ai_credits ?? u.prepaid_ai_credits ?? 0}</strong>{" "}
            {ar ? "رصيد" : "crédits"}
          </p>
          {(addons?.pack_lots || []).length > 0 ? (
            <ul className="mt-2 space-y-1 text-xs text-slate-500">
              {(addons?.pack_lots || []).map((lot) => (
                <li key={lot.id}>
                  {lot.credits_remaining} {ar ? "متبقٍ" : "restants"}
                  {lot.expires_at
                    ? ` · ${ar ? "ينتهي" : "expire"} ${new Date(lot.expires_at).toLocaleDateString("fr-FR")}`
                    : ""}
                </li>
              ))}
            </ul>
          ) : null}
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {(addons?.credit_packs || ent.credit_packs || []).map((pack) => (
              <div
                key={pack.id}
                className="rounded-xl border border-slate-200 bg-[#F7F8FC]/80 p-4"
              >
                <p className="text-sm font-semibold text-[#0B1A4D]">
                  {ar ? pack.label_ar || pack.label : pack.label}
                </p>
                <p className="mt-1 text-lg font-semibold text-[#0B1A4D]">
                  {pack.price_mad} MAD
                </p>
                <p className="text-xs text-slate-500">
                  ~{pack.unit_mad} MAD/{ar ? "رصيد" : "crédit"} · 12 {ar ? "شهرًا" : "mois"}
                </p>
                <Button
                  type="button"
                  size="sm"
                  className="mt-3 w-full"
                  disabled={!!busy || inTrial || !ent.is_active_paying || !(addons?.credit_packs_available ?? ent.is_active_paying)}
                  onClick={() => void buyPack(pack.id)}
                >
                  {busy === `pack:${pack.id}`
                    ? "…"
                    : inTrial || !ent.is_active_paying
                      ? ar
                        ? "متاح بعد الاشتراك"
                        : "Après abonnement"
                      : ar
                        ? "شراء"
                        : "Acheter"}
                </Button>
              </div>
            ))}
          </div>

          {ent.seats_addon_available ? (
            <div className="mt-6 border-t border-slate-100 pt-5">
              <h3 className="text-sm font-semibold text-[#0B1A4D]">
                {ar ? "مقاعد محامين إضافية (Cabinet)" : "Sièges avocats à la carte (Cabinet)"}
              </h3>
              <p className="mt-1 max-w-2xl text-sm leading-relaxed text-slate-600">
                {ar
                  ? `الخطة تشمل 5 محامين. أضيفوا مقاعد إضافية بـ ${ent.extra_seat_mad_monthly ?? 99} درهم/شهر للمقعد.`
                  : `Le plan inclut 5 avocats. Ajoutez des sièges à ${ent.extra_seat_mad_monthly ?? 99} MAD/mois / siège.`}
              </p>
              <div className="mt-4 flex flex-wrap items-end gap-3">
                <div className="w-36">
                  <label className="mb-1 block text-xs font-medium text-slate-500">
                    {ar ? "مقاعد إضافية" : "Sièges extra"}
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={5}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    value={extraSeatsDraft}
                    onChange={(e) => setExtraSeatsDraft(e.target.value)}
                  />
                </div>
                <Button type="button" disabled={!!busy} onClick={() => void saveExtraSeats()}>
                  {busy === "extra-seats" ? "…" : ar ? "حفظ" : "Enregistrer"}
                </Button>
              </div>
            </div>
          ) : null}
        </div>
      ) : null}

      <PackCheckoutModal
        open={!!packCheckout}
        pack={packCheckout}
        ar={ar}
        onClose={() => setPackCheckout(null)}
        onSuccess={(msg) => {
          setMessage(msg);
          setPackCheckout(null);
          void reload();
        }}
      />

      {isAdmin && referral?.available && referral.code ? (
        <div
          id="parrainage"
          className="scroll-mt-24 rounded-2xl border border-[#1B3F9C]/20 bg-gradient-to-br from-[#F7F9FF] to-white p-5 shadow-sm"
        >
          <h3 className="text-sm font-semibold text-[#0B1A4D]">
            {ar ? "برنامج الإحالة بين المكاتب" : "Parrainage entre cabinets"}
          </h3>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-slate-600">
            {ar ? referral.rules_ar : referral.rules_fr}
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <code className="rounded-lg border border-slate-200 bg-white px-3 py-2 font-mono text-sm tracking-wide text-[#0B1A4D]">
              {referral.code}
            </code>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                void navigator.clipboard.writeText(referral.code || "").then(() => {
                  setCopied("code");
                  window.setTimeout(() => setCopied(null), 2000);
                });
              }}
            >
              {copied === "code" ? (ar ? "تم النسخ" : "Copié") : ar ? "نسخ الرمز" : "Copier le code"}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                const path = referral.share_path || `/login?tab=register&ref=${referral.code}`;
                const url =
                  typeof window !== "undefined" ? `${window.location.origin}${path}` : path;
                void navigator.clipboard.writeText(url).then(() => {
                  setCopied("link");
                  window.setTimeout(() => setCopied(null), 2000);
                });
              }}
            >
              {copied === "link" ? (ar ? "تم النسخ" : "Copié") : ar ? "نسخ الرابط" : "Copier le lien"}
            </Button>
          </div>
          {referral.stats ? (
            <p className="mt-3 text-xs text-slate-500">
              {ar
                ? `دعوات: ${referral.stats.invites} · قيد الانتظار: ${referral.stats.pending} · مكافآت: ${referral.stats.rewarded}`
                : `Invitations : ${referral.stats.invites} · en cours : ${referral.stats.pending} · récompensées : ${referral.stats.rewarded}`}
            </p>
          ) : null}
        </div>
      ) : null}

      <Card className="overflow-hidden border-[#0B1A4D]/10 shadow-sm">
        <CardContent className="space-y-4 pt-5">
          {!isAdmin ? (
            <div className="space-y-3">
              <div className="rounded-xl border border-[#1B3F9C]/20 bg-[#1B3F9C]/5 px-4 py-3 text-sm text-[#0B1A4D]">
                {ar
                  ? "أنتم عضو في المكتب (محامٍ أو مساعد). الاشتراك والدفع يخصّان فقط مسؤول المكتب. هنا ترون الحصص فقط — بدون بطاقة ولا ترقية من هذا الحساب."
                  : "Vous êtes membre du cabinet (avocat ou assistant). L’abonnement et le paiement sont gérés uniquement par l’admin cabinet. Ici : quotas en lecture seule — pas de carte ni d’upgrade depuis ce compte."}
              </div>
            </div>
          ) : null}

          {isAdmin &&
          ((u.avocats_used ?? 0) > (u.avocats_limit ?? 1) ||
            (u.assistants_used ?? 0) > (u.assistants_limit ?? 0)) ? (
            <div className="rounded-xl border border-amber-200 bg-amber-50/80 px-4 py-3 text-sm text-amber-950">
              {ar
                ? "المقاعد تتجاوز حدود الخطة. لا يمكن دعوة أعضاء جدد حتى ترفعوا الخطة أو تزيلوا وصول عضو (فريق ← إزالة). لاستبدال مساعد: أزيلوا القديم ثم ادعوا البديل."
                : "Sièges au-delà du plan. Impossible d’inviter tant que vous n’upgraderez pas ou ne retirerez pas un accès (Équipe → Retirer). Pour remplacer un assistant : retirez l’ancien siège, puis invitez le nouveau."}
            </div>
          ) : null}

          {isAdmin ? (
            <div className="rounded-xl border border-dashed border-[#C9A227]/50 bg-[#F7F5F0] px-4 py-3 text-xs text-slate-700">
              {ar
                ? "الدفع الإلكتروني (CMI / PayZone) قيد التجهيز. التجربة تبدأ بالفعل ببطاقة مسجّلة."
                : "Paiement réel (CMI cartes marocaines, PayZone cartes + mobile) pas encore branché. Pendant l’essai : 0 MAD. L’abonnement payant commence seulement à la fin de l’essai, sauf si vous résiliez."}
            </div>
          ) : null}

          {isAdmin &&
          (paymentEnv?.cmi_ready ||
            paymentEnv?.payzone_ready ||
            paymentEnv?.card_status === "ready") ? (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 px-4 py-3 text-xs text-emerald-950">
              {ar
                ? "بيئة CMI / PayZone جاهزة — تفعيل المشغّل مطلوب."
                : "Environnement CMI / PayZone prêt — activation opérateur requise."}
            </div>
          ) : null}

          {isAdmin && ent.status === "trial" && ent.trial_days_left != null ? (
            <div className="rounded-xl border border-orange-200 bg-orange-50/70 px-4 py-3 text-sm text-[#0B1A4D]">
              {ar ? (
                <>تجربتك تنتهي خلال <strong>{ent.trial_days_left}</strong> يومًا. اختر Solo أو Cabinet للحفاظ على الحصص والفريق.</>
              ) : (
                <>
                  Votre essai se termine dans <strong>{ent.trial_days_left}</strong> jour
                  {ent.trial_days_left === 1 ? "" : "s"}. L’abonnement payant ne commence
                  qu’après cette date (carte déjà enregistrée), sauf résiliation avant.
                </>
              )}
            </div>
          ) : null}

          {!isAdmin && ent.status === "trial" && ent.trial_days_left != null ? (
            <div className="rounded-xl border border-orange-200 bg-orange-50/70 px-4 py-3 text-sm text-[#0B1A4D]">
              {ar ? (
                <>التجربة تنتهي خلال <strong>{ent.trial_days_left}</strong> يومًا — أخبر مدير المكتب.</>
              ) : (
                <>
                  L&apos;essai se termine dans <strong>{ent.trial_days_left}</strong> jour
                  {ent.trial_days_left === 1 ? "" : "s"} — prévenez l&apos;admin cabinet.
                </>
              )}
            </div>
          ) : null}

          {isAdmin && (ent.plan as BillingPlan)?.slug === "free" && ent.status === "active" ? (
            <div className="rounded-xl border border-[#C9A227]/40 bg-white px-4 py-3 text-sm text-[#0B1A4D]">
              {ar
                ? "أنت على خطة الاكتشاف. الترقية إلى Solo (299) أو Cabinet (699) تستعيد القوة الكاملة."
                : "Vous êtes sur Découverte. Un passage à Solo (299 MAD) ou Cabinet (699 MAD) restaure toute la puissance."}
            </div>
          ) : null}

          {isAdmin && methods.filter((m) => m.id !== "virement" && m.id !== "bank_transfer").length ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {methods
                .filter((m) => m.id !== "virement" && m.id !== "bank_transfer")
                .map((m) => (
                <div key={m.id} className="rounded-lg border border-slate-100 px-3 py-2 text-xs">
                  <p className="font-semibold text-[#0B1A4D]">{ar && m.name_ar ? m.name_ar : m.name}</p>
                  <p className="text-slate-500">{m.blurb}</p>
                </div>
              ))}
            </div>
          ) : null}

          {message ? <p className="text-sm text-green-700">{message}</p> : null}
          {error ? <p className="text-sm text-red-600">{error}</p> : null}

          {isAdmin ? (
            <div className="border-t border-slate-100 pt-4">
              {!showCancel ? (
                <Button type="button" variant="outline" onClick={() => setConfirmKind("cancel")}>
                  {ar ? "إنهاء الاشتراك" : "Résilier l'abonnement"}
                </Button>
              ) : (
                <div className="space-y-3 rounded-xl border border-red-100 bg-red-50/40 p-4">
                  <p className="text-sm font-medium text-[#0B1A4D]">
                    {ar ? "لماذا تريد الإنهاء؟" : "Pourquoi souhaitez-vous résilier ?"}
                  </p>
                  <select
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    value={cancelCode}
                    onChange={(e) => setCancelCode(e.target.value)}
                  >
                    {reasons.map((r) => (
                      <option key={r.code} value={r.code}>
                        {r.label}
                      </option>
                    ))}
                  </select>
                  <textarea
                    className="min-h-[80px] w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    placeholder={ar ? "تفاصيل اختيارية…" : "Précision optionnelle…"}
                    value={cancelText}
                    onChange={(e) => setCancelText(e.target.value)}
                  />
                  <div className="flex flex-wrap gap-2">
                    <Button type="button" disabled={!!busy} onClick={() => setConfirmKind("cancel")}>
                      {ar ? "تأكيد" : "Confirmer"}
                    </Button>
                    <Button type="button" variant="outline" onClick={() => setShowCancel(false)}>
                      {ar ? "إلغاء" : "Retour"}
                    </Button>
                    {ent.cancel_at_period_end ? (
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() =>
                          void api.undoCancelSubscription().then((r) => {
                            setMessage(r.message);
                            return reload();
                          })
                        }
                      >
                        {ar ? "التراجع عن الإنهاء" : "Annuler la résiliation"}
                      </Button>
                    ) : null}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </CardContent>
      </Card>

      {isAdmin ? (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle>{ar ? "تغيير الخطة" : "Changer de plan"}</CardTitle>
              <div className="flex rounded-lg border border-slate-200 p-0.5 text-xs">
                <button
                  type="button"
                  className={`rounded-md px-3 py-1.5 ${cycle === "monthly" ? "bg-[#0B1A4D] text-white" : ""}`}
                  onClick={() => setCycle("monthly")}
                >
                  {ar ? "شهري" : "Mensuel"}
                </button>
                <button
                  type="button"
                  className={`rounded-md px-3 py-1.5 ${cycle === "yearly" ? "bg-[#0B1A4D] text-white" : ""}`}
                  onClick={() => setCycle("yearly")}
                >
                  {ar ? "سنوي" : "Annuel"}
                </button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {plans.map((p) => {
                const isCurrent = p.slug === currentSlug;
                const isTrial = isCurrent && ent.status === "trial";
                const isDefaultFree = isCurrent && p.slug === "free";
                const canUpgrade = !isCurrent && priceOf(p) > 0;
                return (
                  <div
                    key={p.id}
                    className={`relative flex flex-col rounded-2xl border p-4 transition ${
                      isCurrent
                        ? "border-emerald-400 bg-emerald-50/60 ring-2 ring-emerald-400/30"
                        : p.is_recommended
                          ? "border-[#C9A227] bg-[#F7F5F0]/80"
                          : "border-slate-200 bg-white"
                    }`}
                  >
                    {isCurrent ? (
                      <span className="absolute -top-2.5 start-3 inline-flex animate-pulse items-center gap-1 rounded-full bg-emerald-600 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                        <Check className="h-3 w-3" />
                        {isTrial
                          ? ar
                            ? "تجربتكم"
                            : "Essai en cours"
                          : isDefaultFree
                            ? ar
                              ? "افتراضي"
                              : "Plan par défaut"
                            : ar
                              ? "خطتكم"
                              : "Votre plan"}
                      </span>
                    ) : p.is_recommended ? (
                      <span className="absolute -top-2.5 start-3 inline-flex items-center gap-1 rounded-full bg-[#FF6A00] px-2.5 py-0.5 text-[10px] font-bold uppercase text-white">
                        <Sparkles className="h-3 w-3" />
                        {ar ? "موصى به" : "Populaire"}
                      </span>
                    ) : null}
                    <p className="mt-1 font-semibold text-[#0B1A4D]">{planLabel(p)}</p>
                    <p className="mt-1 text-2xl font-bold text-[#0B1A4D]">
                      {priceOf(p) === 0 ? "0" : priceOf(p)}{" "}
                      <span className="text-xs font-normal text-slate-500">MAD</span>
                    </p>
                    <p className="mt-2 line-clamp-2 text-xs text-slate-600">{p.description}</p>
                    <ul className="mt-3 flex-1 space-y-1 text-xs text-slate-700">
                      {(ar && p.highlights_ar?.length ? p.highlights_ar : p.highlights || [])
                        .slice(0, 6)
                        .map((h) => (
                          <li key={h}>· {h}</li>
                        ))}
                    </ul>
                    <Button
                      className="mt-4 w-full min-h-[44px] text-sm"
                      variant={canUpgrade && p.is_recommended ? "default" : "outline"}
                      disabled={!!busy || isCurrent}
                      onClick={() => void choose(p.slug)}
                    >
                      {busy === p.slug
                        ? "…"
                        : isCurrent
                          ? isTrial
                            ? ar
                              ? "تجربة نشطة"
                              : "Essai actif"
                            : isDefaultFree
                              ? ar
                                ? "مشمول"
                                : "Inclus"
                              : ar
                                ? "خطتكم الحالية"
                                : "Plan actuel"
                          : canUpgrade
                            ? ar
                              ? `ترقية · ${p.trial_days || 30} يومًا`
                              : `Upgrader · ${p.trial_days || 30} j`
                            : ar
                              ? "اختيار"
                              : "Choisir"}
                    </Button>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      ) : null}

      {isAdmin ? (
      <Card id="factures" className="scroll-mt-24">
        <CardHeader>
          <CardTitle>{ar ? "فواتيري" : "Mes factures"}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="rounded-xl border border-dashed border-slate-200 bg-[#F7F8FC] px-4 py-3 text-xs text-slate-600">
            {ar
              ? "تظهر هنا فقط الفواتير المدفوعة (أشهر مدفوعة، أكثر من 0 درهم). معاينة أو PDF (طباعة ← حفظ كـ PDF)."
              : "Seules les factures payantes (> 0 MAD) apparaissent ici. Aperçu, ou PDF (Imprimer → Enregistrer en PDF)."}
          </div>
          {inTrial ? (
            <p className="text-xs text-amber-800">
              {ar
                ? "أثناء التجربة: لا فاتورة بـ 0 درهم في هذه القائمة. الفواتير تظهر بعد الدفع الحقيقي."
                : "Pendant l’essai : aucun reçu à 0 MAD dans cette liste. Les factures apparaissent après un paiement réel."}
            </p>
          ) : null}
          <InvoicesList
            invoices={history?.invoices || []}
            ar={ar}
            busyId={invBusy || (typeof busy === "string" ? busy : null)}
            onBusy={setInvBusy}
            onError={setError}
          />
          {history && history.events.length > 0 ? (
            <div className="border-t border-slate-100 pt-3">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                {ar ? "سجل الاشتراك" : "Historique abonnement"}
              </p>
              {history.events.slice(0, 6).map((e, i) => (
                <p key={`${e.event_type}-${i}`} className="text-xs text-slate-500">
                  {e.created_at ? new Date(e.created_at).toLocaleString() : ""} — {e.event_type}
                  {e.detail ? ` · ${e.detail}` : ""}
                </p>
              ))}
            </div>
          ) : null}
        </CardContent>
      </Card>
      ) : null}

      <TrialPitchModal
        open={!!pitchPlan}
        onClose={() => setPitchPlan(null)}
        onContinue={() => {
          const p = pitchPlan;
          setPitchPlan(null);
          if (p) goToCheckout(p);
        }}
        plan={pitchPlan}
        cycle={cycle}
        ar={ar}
      />
      <ConfirmActionModal
        open={confirmKind === "cancel"}
        onClose={() => setConfirmKind(null)}
        ar={ar}
        busy={busy === "cancel"}
        tag={ar ? "إنهاء" : "Résiliation"}
        title={ar ? "تأكيد إنهاء الاشتراك؟" : "Confirmer la résiliation ?"}
        points={
          ar
            ? [
                "يبقى الوصول حتى نهاية الفترة الجارية",
                "يمكن التراجع قبل نهاية الفترة",
                "لن تُخصم البطاقة بعد ذلك إذا ألغيتم قبل نهاية التجربة",
              ]
            : [
                "L’accès reste jusqu’à la fin de la période en cours",
                "Vous pouvez annuler la résiliation avant cette date",
                "Aucune débite si vous résiliez pendant l’essai",
              ]
        }
        primaryLabel={ar ? "نعم، إنهاء" : "Oui, résilier"}
        onConfirm={() => {
          setConfirmKind(null);
          void submitCancel();
        }}
      />
    </div>
  );
}

function UsageBar({
  label,
  used,
  limit,
  pct,
  note,
}: {
  label: string;
  used: number;
  limit: number;
  pct?: number;
  note?: string;
}) {
  const unlimited = limit < 0;
  const bar = pct ?? (unlimited ? 8 : Math.min(100, Math.round((used / Math.max(limit, 1)) * 100)));
  const full = !unlimited && bar >= 100;
  return (
    <div>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-sm font-medium text-[#0B1A4D]">{label}</p>
        <p className={`text-sm font-semibold ${full ? "text-red-700" : "text-slate-700"}`}>
          {unlimited ? `${used} / ∞` : `${used} / ${limit}`}
          {!unlimited ? (
            <span className="ms-2 text-xs font-normal text-slate-500">{bar}% used</span>
          ) : null}
        </p>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full transition-all ${full ? "bg-red-500" : "bg-[#1B3F9C]"}`}
          style={{ width: `${unlimited ? 8 : bar}%` }}
        />
      </div>
      {note ? <p className="mt-2 text-xs leading-relaxed text-slate-500">{note}</p> : null}
    </div>
  );
}

function Meter({ label, used, limit }: { label: string; used: number; limit: number }) {
  const unlimited = limit < 0;
  const pct = unlimited ? 8 : Math.min(100, (used / Math.max(limit, 1)) * 100);
  return (
    <div className="rounded-xl border border-slate-100 bg-[#F7F5F0]/50 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-lg font-semibold text-[#0B1A4D]">
        {used}
        {unlimited ? " / ∞" : ` / ${limit}`}
      </p>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white">
        <div className="h-full rounded-full bg-[#0B1A4D]/80" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
