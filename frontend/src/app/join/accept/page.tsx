"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { AuthLayout } from "@/components/auth/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/auth/password-input";
import { api, ApiError } from "@/lib/api";
import { isPasswordStrong } from "@/lib/password";
import { roleLabel } from "@/lib/roles";
import { useClientLocale } from "@/store/locale";

function AcceptInviteForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const locale = useClientLocale();
  const ar = locale === "ar";
  const code = (searchParams.get("code") || "").trim();

  const [loading, setLoading] = useState(true);
  const [valid, setValid] = useState(false);
  const [cabinetName, setCabinetName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("avocat");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [emailExists, setEmailExists] = useState(false);
  const [emailSameCabinet, setEmailSameCabinet] = useState(false);

  useEffect(() => {
    if (!code) {
      setLoading(false);
      setValid(false);
      return;
    }
    void api
      .getInvitePreview(code)
      .then((p) => {
        setValid(p.valid);
        setCabinetName(p.cabinet_name);
        setEmail(p.email);
        setRole(p.role || "avocat");
        setEmailExists(!!p.email_already_registered);
        setEmailSameCabinet(!!p.email_same_cabinet);
        if (p.recipient_name) setFullName(p.recipient_name);
      })
      .catch(() => setValid(false))
      .finally(() => setLoading(false));
  }, [code]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!code || !valid) return;
    if (fullName.trim().length < 2) {
      setError(ar ? "الاسم الكامل مطلوب." : "Le nom complet est requis.");
      return;
    }
    if (!isPasswordStrong(password)) {
      setError(ar ? "كلمة مرور ضعيفة." : "Mot de passe trop faible (12+ caractères, complexité).");
      return;
    }
    if (password !== confirm) {
      setError(ar ? "كلمتا المرور غير متطابقتين." : "Les mots de passe ne correspondent pas.");
      return;
    }
    setBusy(true);
    try {
      await api.acceptInvite({ code, full_name: fullName.trim(), password });
      router.push("/login?activated=1");
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "";
      if (msg === "EMAIL_EXISTS_SAME_CABINET" || msg === "EMAIL_EXISTS") {
        setError(
          ar
            ? "هذا البريد عضو بالفعل في هذا المكتب — سجّل الدخول."
            : "Cet email est déjà membre de ce cabinet — connectez-vous.",
        );
        setEmailExists(true);
        setEmailSameCabinet(msg === "EMAIL_EXISTS_SAME_CABINET" || msg === "EMAIL_EXISTS");
      } else if (msg === "EMAIL_EXISTS_OTHER_CABINET") {
        setError(
          ar
            ? "هذا البريد لديه حساب LexHub في مكتب آخر. لا يمكن إنشاء حساب ثانٍ — سجّل الدخول واتصل بمسؤول مكتبك الحالي لنقل الحساب."
            : "Cet email a déjà un compte LexHub dans un autre cabinet. Pas de second compte : connectez-vous, puis demandez un transfert à votre admin actuel.",
        );
        setEmailExists(true);
        setEmailSameCabinet(false);
      } else if (msg === "INVITE_INVALID" || msg === "INVITE_USE_LINK") {
        setError(ar ? "الدعوة غير صالحة أو منتهية." : "Invitation invalide ou expirée.");
      } else {
        setError(msg || (ar ? "تعذر التفعيل." : "Activation impossible."));
      }
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-2 text-slate-500">
        <Loader2 className="h-5 w-5 animate-spin" />
        …
      </div>
    );
  }

  if (!code || !valid) {
    return (
      <AuthLayout>
        <div className="mx-auto max-w-md rounded-2xl border border-red-200 bg-white p-8 text-center shadow-lg">
          <h1 className="font-serif text-xl text-[#0B1A4D]">
            {ar ? "دعوة غير صالحة" : "Invitation invalide"}
          </h1>
          <p className="mt-3 text-sm text-slate-600">
            {ar
              ? "الدعوة غير صالحة أو منتهية. استخدموا آخر رابط وصل بالبريد، أو سجّلوا الدخول."
              : "Invitation invalide ou expirée. Utilisez le dernier lien reçu par e-mail, ou reconnectez-vous."}
          </p>
          <Link href="/login" className="mt-6 inline-block text-sm font-semibold text-[#0B1A4D] underline">
            {ar ? "العودة للدخول" : "Retour à la connexion"}
          </Link>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <div className="mx-auto max-w-md rounded-2xl border border-[#E85A00]/20 bg-white p-8 shadow-xl">
        <h1 className="text-center font-serif text-2xl text-[#0B1A4D]">
          {ar ? "تفعيل حساب LexHub" : "Activer mon compte LexHub"}
        </h1>
        <p className="mt-2 text-center text-sm text-slate-600">
          {ar ? "دعوة من" : "Invitation de"} <strong>{cabinetName}</strong>
          {" · "}
          {roleLabel(role, ar ? "ar" : "fr")}
        </p>
        <form onSubmit={(e) => void submit(e)} className="mt-6 space-y-4">
          <Input label="Email" type="email" value={email} readOnly dir="ltr" className="bg-slate-50" />
          {emailExists ? (
            <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-3 text-sm text-amber-950">
              <p>
                {emailSameCabinet
                  ? ar
                    ? "هذا البريد عضو في هذا المكتب بالفعل."
                    : "Cet email est déjà membre de ce cabinet."
                  : ar
                    ? "هذا البريد لديه حساب LexHub مسبقاً (مكتب آخر أو حساب قائم)."
                    : "Cet email a déjà un compte LexHub (autre cabinet ou compte existant)."}
              </p>
              <p className="mt-2 text-xs opacity-90">
                {ar
                  ? "لا يمكن إنشاء حساب ثانٍ بنفس البريد. سجّل الدخول، أو اطلب من مسؤول المكتب نقل الحساب."
                  : "Un seul compte par email. Connectez-vous, ou demandez un transfert de cabinet à l’admin."}
              </p>
              <Link
                href={`/login?email=${encodeURIComponent(email)}`}
                className="mt-3 inline-block font-semibold text-[#0B1A4D] underline"
              >
                {ar ? "تسجيل الدخول" : "Se connecter"}
              </Link>
            </div>
          ) : null}
          <Input
            label={ar ? "الاسم الكامل" : "Nom complet"}
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            disabled={emailExists && !emailSameCabinet}
          />
          <PasswordInput
            label={ar ? "كلمة المرور" : "Mot de passe"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="new-password"
            disabled={emailExists && !emailSameCabinet}
          />
          <PasswordInput
            label={ar ? "تأكيد كلمة المرور" : "Confirmer le mot de passe"}
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            required
            autoComplete="new-password"
            disabled={emailExists && !emailSameCabinet}
          />
          {error ? (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
          ) : null}
          {!emailExists || emailSameCabinet ? (
            <Button type="submit" className="w-full" disabled={busy || (emailExists && emailSameCabinet)}>
              {emailExists && emailSameCabinet
                ? ar
                  ? "سجّل الدخول للمتابعة"
                  : "Connectez-vous pour continuer"
                : busy
                  ? ar
                    ? "جاري التفعيل…"
                    : "Activation…"
                  : ar
                    ? "تفعيل والدخول"
                    : "Activer mon compte"}
            </Button>
          ) : null}
        </form>
        <p className="mt-4 text-center text-xs text-slate-500">
          {ar ? "الوصول فوري — بدون انتظار موافقة." : "Accès immédiat — sans attente d’approbation."}
        </p>
      </div>
    </AuthLayout>
  );
}

export default function AcceptInvitePage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">…</div>}>
      <AcceptInviteForm />
    </Suspense>
  );
}
