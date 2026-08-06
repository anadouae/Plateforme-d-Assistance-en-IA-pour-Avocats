"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Building2, Mail, ShieldCheck, UserRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AuthLayout } from "@/components/auth/auth-layout";
import { PasswordInput } from "@/components/auth/password-input";
import { api, ApiError } from "@/lib/api";
import { isPasswordStrong, normalizeEmail, passwordStrength } from "@/lib/password";
import { useTranslations } from "@/store/locale";

type FieldKey =
  | "cabinet_name"
  | "city"
  | "address"
  | "barreau"
  | "manager_name"
  | "email"
  | "phone"
  | "password"
  | "confirm_password"
  | "accept_terms"
  | "email_otp";

export default function RegisterPage() {
  const router = useRouter();
  const auth = useTranslations().auth;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [emailVerified, setEmailVerified] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [emailOtp, setEmailOtp] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<FieldKey, string>>>({});
  const [form, setForm] = useState({
    cabinet_name: "",
    city: "",
    address: "",
    barreau: "",
    ice: "",
    manager_name: "",
    email: "",
    phone: "",
    password: "",
    confirm_password: "",
    accept_terms: false,
  });

  function update(field: string, value: string | boolean) {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (field in fieldErrors) {
      setFieldErrors((prev) => ({ ...prev, [field]: undefined }));
    }
    if (field === "email") {
      setEmailVerified(false);
      setOtpSent(false);
      setEmailOtp("");
    }
  }

  const strength = passwordStrength(form.password);
  const strengthLabels = [
    auth.strengthWeak,
    auth.strengthMedium,
    auth.strengthGood,
    auth.strengthStrong,
  ];
  const strengthColors = ["bg-red-500", "bg-orange-400", "bg-amber-400", "bg-emerald-500"];

  const passwordsMatch = useMemo(
    () => !form.confirm_password || form.password === form.confirm_password,
    [form.password, form.confirm_password],
  );

  async function sendEmailCode() {
    setError("");
    setInfo("");
    const email = normalizeEmail(form.email);
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setFieldErrors({ email: auth.emailInvalid });
      return;
    }
    setLoading(true);
    try {
      const res = await api.requestRegisterOtp(email);
      setOtpSent(true);
      setInfo(res.message + " — Dev : http://localhost:8025");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : auth.registerError);
    } finally {
      setLoading(false);
    }
  }

  async function confirmEmailCode() {
    setError("");
    const email = normalizeEmail(form.email);
    if (emailOtp.length !== 6) {
      setFieldErrors({ email_otp: "Code à 6 chiffres requis." });
      return;
    }
    setLoading(true);
    try {
      await api.verifyRegisterOtp(email, emailOtp);
      setEmailVerified(true);
      setInfo("Email vérifié — complétez les informations du cabinet.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Code invalide.");
    } finally {
      setLoading(false);
    }
  }

  function validate(): boolean {
    const next: Partial<Record<FieldKey, string>> = {};
    if (!emailVerified) next.email_otp = "Vérifiez d'abord votre email.";
    if (form.cabinet_name.trim().length < 2) next.cabinet_name = auth.fieldRequired;
    if (form.city.trim().length < 2) next.city = auth.fieldRequired;
    if (form.address.trim().length < 5) next.address = auth.fieldRequired;
    if (form.barreau.trim().length < 2) next.barreau = auth.fieldRequired;
    if (form.manager_name.trim().length < 2) next.manager_name = auth.fieldRequired;
    const phoneDigits = form.phone.replace(/\D/g, "");
    if (phoneDigits.length < 8) next.phone = auth.phoneInvalid;
    if (!isPasswordStrong(form.password)) next.password = auth.pwdWeak;
    if (form.password !== form.confirm_password) next.confirm_password = auth.pwdMismatch;
    if (!form.accept_terms) next.accept_terms = auth.termsRequired;
    setFieldErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!validate()) return;

    setLoading(true);
    try {
      await api.register({
        cabinet_name: form.cabinet_name.trim(),
        city: form.city.trim(),
        address: form.address.trim(),
        barreau: form.barreau.trim(),
        ice: form.ice.trim() || undefined,
        manager_name: form.manager_name.trim(),
        email: normalizeEmail(form.email),
        phone: form.phone.trim(),
        password: form.password,
        email_otp: emailOtp,
      });
      router.push(`/verify-email?email=${encodeURIComponent(normalizeEmail(form.email))}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : auth.registerError);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout wide>
      <div className="mb-5 text-center lg:text-start">
        <h1 className="font-serif text-2xl font-semibold text-white sm:text-3xl drop-shadow-sm">
          {auth.registerTitle}
        </h1>
        <p className="mt-2 font-serif text-sm text-white/80">{auth.registerSubtitle}</p>
      </div>

      <div className="rounded-3xl border border-white/50 bg-white/92 p-5 shadow-royal backdrop-blur-xl sm:p-7">
        <form onSubmit={handleSubmit} className="space-y-6" noValidate>
          {/* Étape 1 — email + OTP */}
          <section className="space-y-3">
            <div className="flex items-center gap-2 text-sanad-navy">
              <Mail className="h-4 w-4 text-sanad-gold" />
              <h2 className="font-serif text-sm font-semibold tracking-wide">
                1. Vérifier votre email
              </h2>
            </div>
            <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
              <Input
                label={auth.email}
                name="email"
                type="email"
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                required
                disabled={emailVerified || loading}
                error={fieldErrors.email}
                className="h-11 rounded-xl"
              />
              <div className="flex items-end">
                <Button
                  type="button"
                  variant="outline"
                  className="h-11 w-full sm:w-auto"
                  disabled={loading || emailVerified}
                  onClick={() => void sendEmailCode()}
                >
                  {otpSent ? "Renvoyer le code" : "Envoyer le code"}
                </Button>
              </div>
            </div>
            {otpSent && !emailVerified && (
              <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
                <Input
                  label="Code reçu par email"
                  name="email_otp"
                  inputMode="numeric"
                  maxLength={6}
                  value={emailOtp}
                  onChange={(e) => setEmailOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  placeholder="000000"
                  error={fieldErrors.email_otp}
                  className="h-11 rounded-xl tracking-[0.35em]"
                  disabled={loading}
                />
                <div className="flex items-end">
                  <Button
                    type="button"
                    className="h-11 w-full bg-[#0B1F4A] text-white sm:w-auto"
                    disabled={loading || emailOtp.length !== 6}
                    onClick={() => void confirmEmailCode()}
                  >
                    Valider
                  </Button>
                </div>
              </div>
            )}
            {emailVerified && (
              <p className="text-sm font-medium text-emerald-700">Email vérifié ✓</p>
            )}
          </section>

          {/* Étapes suivantes — débloquées après OTP */}
          <fieldset disabled={!emailVerified} className="space-y-6 disabled:opacity-45">
            <section className="space-y-3 border-t border-sanad-navy/8 pt-5">
              <div className="flex items-center gap-2 text-sanad-navy">
                <Building2 className="h-4 w-4 text-sanad-gold" />
                <h2 className="font-serif text-sm font-semibold tracking-wide">
                  {auth.sectionCabinet}
                </h2>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <Input
                    label={auth.cabinetName}
                    name="cabinet_name"
                    value={form.cabinet_name}
                    onChange={(e) => update("cabinet_name", e.target.value)}
                    required
                    error={fieldErrors.cabinet_name}
                    className="h-11 rounded-xl"
                  />
                </div>
                <Input
                  label={auth.city}
                  name="city"
                  value={form.city}
                  onChange={(e) => update("city", e.target.value)}
                  required
                  error={fieldErrors.city}
                  className="h-11 rounded-xl"
                />
                <Input
                  label={auth.barreau}
                  name="barreau"
                  value={form.barreau}
                  onChange={(e) => update("barreau", e.target.value)}
                  required
                  error={fieldErrors.barreau}
                  className="h-11 rounded-xl"
                />
                <div className="sm:col-span-2">
                  <Input
                    label={auth.address}
                    name="address"
                    value={form.address}
                    onChange={(e) => update("address", e.target.value)}
                    required
                    error={fieldErrors.address}
                    className="h-11 rounded-xl"
                  />
                </div>
                <Input
                  label={`${auth.ice} (${auth.optional})`}
                  name="ice"
                  value={form.ice}
                  onChange={(e) => update("ice", e.target.value)}
                  className="h-11 rounded-xl"
                />
                <Input
                  label={auth.phone}
                  name="phone"
                  type="tel"
                  value={form.phone}
                  onChange={(e) => update("phone", e.target.value)}
                  required
                  error={fieldErrors.phone}
                  className="h-11 rounded-xl"
                />
              </div>
            </section>

            <section className="space-y-3 border-t border-sanad-navy/8 pt-5">
              <div className="flex items-center gap-2 text-sanad-navy">
                <UserRound className="h-4 w-4 text-sanad-gold" />
                <h2 className="font-serif text-sm font-semibold tracking-wide">
                  {auth.sectionAccount}
                </h2>
              </div>
              <Input
                label={auth.managerName}
                name="manager_name"
                value={form.manager_name}
                onChange={(e) => update("manager_name", e.target.value)}
                required
                error={fieldErrors.manager_name}
                className="h-11 rounded-xl"
              />
            </section>

            <section className="space-y-3 border-t border-sanad-navy/8 pt-5">
              <div className="flex items-center gap-2 text-sanad-navy">
                <ShieldCheck className="h-4 w-4 text-sanad-gold" />
                <h2 className="font-serif text-sm font-semibold tracking-wide">
                  {auth.sectionSecurity}
                </h2>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <PasswordInput
                    label={auth.password}
                    name="password"
                    value={form.password}
                    onChange={(e) => update("password", e.target.value)}
                    required
                    error={fieldErrors.password}
                  />
                  {form.password && (
                    <div className="mt-2 flex gap-1">
                      {[0, 1, 2, 3].map((i) => (
                        <div
                          key={i}
                          className={`h-1 flex-1 rounded ${
                            i < strength
                              ? strengthColors[Math.max(0, strength - 1)]
                              : "bg-slate-200"
                          }`}
                        />
                      ))}
                    </div>
                  )}
                  {form.password && (
                    <p className="mt-1 text-xs text-sanad-muted">
                      {auth.strengthLabel} :{" "}
                      {strengthLabels[Math.max(0, strength - 1)] || auth.strengthWeak}
                    </p>
                  )}
                </div>
                <PasswordInput
                  label={auth.confirmPassword}
                  name="confirm_password"
                  value={form.confirm_password}
                  onChange={(e) => update("confirm_password", e.target.value)}
                  required
                  error={
                    fieldErrors.confirm_password ||
                    (!passwordsMatch ? auth.pwdMismatch : undefined)
                  }
                />
              </div>
            </section>

            <label className="flex items-start gap-2.5 text-sm text-sanad-muted">
              <input
                type="checkbox"
                checked={form.accept_terms}
                onChange={(e) => update("accept_terms", e.target.checked)}
                className="mt-1 h-4 w-4 rounded accent-sanad-navy"
                required
              />
              <span>
                {auth.acceptTerms}{" "}
                <Link href="/confidentialite" className="text-sanad-navy hover:underline">
                  {auth.termsLink}
                </Link>{" "}
                {auth.andPrivacy}
              </span>
            </label>
          </fieldset>

          {info && (
            <p className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
              {info}
            </p>
          )}
          {error && (
            <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          )}

          <Button
            type="submit"
            className="h-11 w-full rounded-xl bg-[#0B1F4A] font-serif text-white hover:bg-[#14306B]"
            disabled={loading || !emailVerified}
          >
            {loading ? auth.registerLoading : auth.registerSubmit}
          </Button>
        </form>

        <p className="mt-5 text-center text-sm text-sanad-muted">
          {auth.hasAccount}{" "}
          <Link href="/login" className="font-medium text-sanad-navy hover:underline">
            {auth.signIn}
          </Link>
        </p>
      </div>
    </AuthLayout>
  );
}
