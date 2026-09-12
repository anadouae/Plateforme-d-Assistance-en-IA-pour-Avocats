"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Building2, Check, Copy, Mail, MessageSquare } from "lucide-react";
import { PublicNavbar } from "@/components/layout/public-navbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useClientLocale } from "@/store/locale";

const CONTACT_EMAIL = "contact@lexhub.space";

export default function ContactPageInner() {
  const ar = useClientLocale() === "ar";
  const searchParams = useSearchParams();
  const plan = searchParams.get("plan") || "enterprise";

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [cabinet, setCabinet] = useState("");
  const [message, setMessage] = useState("");
  const [sent, setSent] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (plan === "enterprise") {
      setMessage(
        ar
          ? "أرغب في خطة Entreprise LexHub لمكتبي."
          : "Je souhaite le plan Entreprise LexHub pour mon cabinet.",
      );
    }
  }, [plan, ar]);

  function buildMailto() {
    const subject = encodeURIComponent(`LexHub ${plan === "enterprise" ? "Entreprise" : "Contact"}`);
    const body = encodeURIComponent(
      [`Nom : ${name}`, `E-mail : ${email}`, `Cabinet : ${cabinet}`, "", message].join("\n"),
    );
    return `mailto:${CONTACT_EMAIL}?subject=${subject}&body=${body}`;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !email.trim()) return;
    window.location.href = buildMailto();
    setSent(true);
  }

  async function copyEmail() {
    try {
      await navigator.clipboard.writeText(CONTACT_EMAIL);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="min-h-screen bg-[#F4F6FA]" dir={ar ? "rtl" : "ltr"}>
      <PublicNavbar />
      <main className="mx-auto max-w-2xl px-4 py-14 sm:px-6">
        <div className="text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#0A1228]/5 text-[#0A1228]">
            <Building2 className="h-7 w-7" strokeWidth={1.6} />
          </div>
          <h1 className="mt-4 font-display text-3xl font-semibold text-[#0A1228]">
            {ar ? "تواصل معنا" : "Nous contacter"}
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            {ar
              ? "خطة Entreprise — استمارة تأهيل قبل التفعيل. Solo و Cabinet يبقيان مباشرة."
              : "Plan Entreprise — formulaire de qualification avant activation. Solo et Cabinet restent en libre-service."}
          </p>
          <p className="mt-3">
            <Link href="/commercial?intent=enterprise" className="text-sm font-semibold text-[#0A1228] underline">
              {ar ? "استمارة Entreprise / حسب الطلب" : "Formulaire Entreprise / Sur mesure"}
            </Link>
          </p>
        </div>

        <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-xl bg-[#F4F6FA] px-4 py-3">
            <div className="flex items-center gap-2 text-sm text-[#0A1228]">
              <Mail className="h-4 w-4" />
              <a href={`mailto:${CONTACT_EMAIL}`} className="font-medium underline">
                {CONTACT_EMAIL}
              </a>
            </div>
            <Button type="button" size="sm" variant="outline" onClick={() => void copyEmail()}>
              <Copy className="h-3.5 w-3.5" />
              {copied ? (ar ? "تم النسخ" : "Copié") : ar ? "نسخ" : "Copier"}
            </Button>
          </div>

          {sent ? (
            <div className="space-y-4 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100 text-green-700">
                <Check className="h-6 w-6" />
              </div>
              <p className="text-sm text-slate-700">
                {ar
                  ? "تم فتح بريدك الإلكتروني. أرسل الرسالة — نرد خلال 24–48 ساعة."
                  : "Votre client mail s'est ouvert. Envoyez le message — réponse sous 24–48 h."}
              </p>
              <Link href="/tarifs">
                <Button variant="outline">{ar ? "العودة للأسعار" : "Retour aux tarifs"}</Button>
              </Link>
            </div>
          ) : (
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">
                  {ar ? "الاسم الكامل" : "Nom complet"}
                </label>
                <Input value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">
                  {ar ? "البريد الإلكتروني" : "E-mail professionnel"}
                </label>
                <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">
                  {ar ? "اسم المكتب" : "Nom du cabinet"}
                </label>
                <Input value={cabinet} onChange={(e) => setCabinet(e.target.value)} />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">
                  {ar ? "رسالتك" : "Votre message"}
                </label>
                <textarea
                  className="min-h-[120px] w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                />
              </div>
              <Button type="submit" className="w-full gap-2">
                <MessageSquare className="h-4 w-4" />
                {ar ? "إرسال الطلب" : "Envoyer ma demande"}
              </Button>
              <p className="text-center text-[11px] text-slate-500">
                {ar
                  ? "أو راسلنا مباشرة على contact@lexhub.space"
                  : "Ou écrivez directement à contact@lexhub.space"}
              </p>
            </form>
          )}
        </div>

        <p className="mt-6 text-center text-sm text-slate-500">
          {ar ? "للخطط Solo و Cabinet — " : "Pour Solo et Cabinet — "}
          <Link href="/tarifs" className="font-medium text-[#0A1228] underline">
            {ar ? "ابدأ التجربة من صفحة الأسعار" : "démarrez depuis la page tarifs"}
          </Link>
        </p>
      </main>
    </div>
  );
}
