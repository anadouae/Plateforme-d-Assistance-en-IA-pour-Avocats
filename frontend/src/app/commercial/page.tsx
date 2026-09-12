"use client";

import { Suspense, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Building2, Check, Mail, Phone, Scale } from "lucide-react";
import { PublicNavbar } from "@/components/layout/public-navbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useClientLocale } from "@/store/locale";

function CommercialInner() {
  const ar = useClientLocale() === "ar";
  const search = useSearchParams();
  const user = useAuthStore((s) => s.user);
  const intent = search.get("intent") === "custom" ? "custom" : "enterprise";
  const kind = intent === "custom" ? "custom" : "enterprise_trial";

  const [fullName, setFullName] = useState(user?.full_name || "");
  const [email, setEmail] = useState(user?.email || "");
  const [phone, setPhone] = useState("");
  const [cabinet, setCabinet] = useState("");
  const [city, setCity] = useState("");
  const [lawyers, setLawyers] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);

  const copy = useMemo(() => {
    if (intent === "custom") {
      return ar
        ? {
            title: "عرض مخصص",
            lead: "مكاتب كبيرة (أكثر من 15 محامياً، عدة مدن، عقد خاص). لا سعر علني ولا دفع فوري — نعدّ عرضاً يدوياً.",
            cta: "طلب عرض سعر",
          }
        : {
            title: "Sur mesure",
            lead: "Très gros cabinets (plus de 15 avocats, plusieurs villes, contrat spécial). Pas de prix sur le site, pas de paiement immédiat — nous établissons un devis.",
            cta: "Demander un devis",
          };
    }
    return ar
      ? {
          title: "تجربة Entreprise",
          lead: "خطة Entreprise تفتح مقاعد كثيرة وحجماً كبيراً من الذكاء الاصطناعي. نطلب استمارة قصيرة أو مكالمة قبل التفعيل — لتفادي الحسابات الوهمية.",
          cta: "إرسال الطلب",
        }
      : {
          title: "Essai Entreprise",
          lead: "L’offre Entreprise ouvre beaucoup de sièges et beaucoup d’IA. Un court formulaire (ou un appel) précède l’activation — pour éviter les faux comptes. Solo et Cabinet restent en libre-service.",
          cta: "Envoyer la demande",
        };
  }, [ar, intent]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const n = Number(lawyers);
    setBusy(true);
    try {
      await api.submitCommercialLead({
        kind,
        full_name: fullName.trim(),
        email: email.trim(),
        phone: phone.trim() || undefined,
        cabinet_name: cabinet.trim() || undefined,
        city: city.trim() || undefined,
        lawyers_count: Number.isFinite(n) && n >= 1 ? Math.round(n) : undefined,
        message: message.trim() || undefined,
      });
      setSent(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : ar ? "تعذّر الإرسال" : "Envoi impossible");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#F4F6FA]" dir={ar ? "rtl" : "ltr"}>
      <PublicNavbar />
      <main className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
        <div className="text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#0A1228]/5 text-[#0A1228]">
            {intent === "custom" ? (
              <Scale className="h-7 w-7" strokeWidth={1.6} />
            ) : (
              <Building2 className="h-7 w-7" strokeWidth={1.6} />
            )}
          </div>
          <h1 className="mt-4 font-display text-3xl font-semibold text-[#0A1228]">{copy.title}</h1>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-relaxed text-slate-600">{copy.lead}</p>
        </div>

        <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          {sent ? (
            <div className="space-y-4 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
                <Check className="h-6 w-6" />
              </div>
              <p className="text-sm font-medium text-[#0A1228]">
                {ar
                  ? "وصل طلبكم. مستشار يتواصل معكم خلال 24–48 ساعة عمل."
                  : "Demande reçue. Un conseiller vous recontacte sous 24–48 h ouvrées."}
              </p>
              <p className="text-xs text-slate-500">
                {ar
                  ? "Solo و Cabinet ما زالا متاحين مباشرة من صفحة الأسعار."
                  : "Solo et Cabinet restent disponibles immédiatement depuis la page tarifs."}
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                <Link href="/tarifs">
                  <Button variant="outline">{ar ? "العودة للأسعار" : "Retour aux tarifs"}</Button>
                </Link>
                <a href="mailto:contact@lexhub.space">
                  <Button variant="outline">
                    <Mail className="h-4 w-4" />
                    contact@lexhub.space
                  </Button>
                </a>
              </div>
            </div>
          ) : (
            <form className="space-y-4" onSubmit={(e) => void onSubmit(e)}>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block text-xs font-medium text-slate-600">
                  {ar ? "الاسم الكامل" : "Nom complet"}
                  <Input
                    className="mt-1"
                    required
                    minLength={2}
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                  />
                </label>
                <label className="block text-xs font-medium text-slate-600">
                  {ar ? "البريد المهني" : "E-mail professionnel"}
                  <Input
                    className="mt-1"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </label>
                <label className="block text-xs font-medium text-slate-600">
                  {ar ? "الهاتف" : "Téléphone"}
                  <Input
                    className="mt-1"
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder={ar ? "06…" : "06 …"}
                  />
                </label>
                <label className="block text-xs font-medium text-slate-600">
                  {ar ? "اسم المكتب" : "Nom du cabinet"}
                  <Input className="mt-1" value={cabinet} onChange={(e) => setCabinet(e.target.value)} />
                </label>
                <label className="block text-xs font-medium text-slate-600">
                  {ar ? "المدينة" : "Ville"}
                  <Input className="mt-1" value={city} onChange={(e) => setCity(e.target.value)} />
                </label>
                <label className="block text-xs font-medium text-slate-600">
                  {ar ? "عدد المحامين" : "Nombre d’avocats"}
                  <Input
                    className="mt-1"
                    type="number"
                    min={1}
                    max={500}
                    value={lawyers}
                    onChange={(e) => setLawyers(e.target.value)}
                    placeholder={intent === "custom" ? "16+" : "6–15"}
                  />
                </label>
              </div>
              <label className="block text-xs font-medium text-slate-600">
                {ar ? "رسالتكم (اختياري)" : "Message (optionnel)"}
                <textarea
                  className="mt-1 min-h-[110px] w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  maxLength={4000}
                  placeholder={
                    ar
                      ? "حجم المكتب، المدن، احتياجات خاصة…"
                      : "Taille du cabinet, villes, besoins particuliers…"
                  }
                />
              </label>
              {error ? <p className="text-sm text-red-600">{error}</p> : null}
              <Button type="submit" className="w-full" disabled={busy}>
                <Phone className="h-4 w-4" />
                {busy ? (ar ? "جارٍ الإرسال…" : "Envoi…") : copy.cta}
              </Button>
              <p className="text-center text-[11px] leading-relaxed text-slate-500">
                {ar
                  ? "لا تفعيل فوري ولا دفع على هذه الصفحة. الدفع الإلكتروني (CMI / PayZone) جاهز تقنياً وينتظر تفعيل المشغّل."
                  : "Pas d’activation instantanée ni de paiement sur cette page. Le paiement électronique (CMI / PayZone) est prêt techniquement — activation opérateur ensuite."}
              </p>
            </form>
          )}
        </div>

        <p className="mt-6 text-center text-sm text-slate-500">
          {ar ? "Solo و Cabinet — " : "Solo et Cabinet — "}
          <Link href="/tarifs" className="font-medium text-[#0A1228] underline">
            {ar ? "ابدؤوا التجربة بأنفسكم" : "démarrez l’essai vous-mêmes"}
          </Link>
        </p>
      </main>
    </div>
  );
}

export default function CommercialPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#F4F6FA]" />}>
      <CommercialInner />
    </Suspense>
  );
}
