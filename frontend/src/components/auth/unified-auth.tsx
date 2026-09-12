"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { Check, KeyRound } from "lucide-react";
import { LexHubLogo } from "@/components/brand/lexhub-logo";
import { LanguageSwitch } from "@/components/layout/language-switch";
import { PasswordInput } from "@/components/auth/password-input";
import { AuthSuccessModal } from "@/components/auth/auth-success-modal";
import { LexHubTurnstile } from "@/components/auth/lexhub-turnstile";
import { LegalDocLink } from "@/components/auth/legal-doc-link";
import { AuthParticles } from "@/components/auth/auth-particles";
import { AuthProductDemo } from "@/components/auth/auth-product-demo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";
import { isPasswordStrong, normalizeEmail, passwordRules, passwordStrength } from "@/lib/password";
import { useAuthStore } from "@/store/auth";
import { useClientLocale, useTranslations } from "@/store/locale";
import {
  clearRegisterDraft,
  emptyRegisterForm,
  loadRegisterDraft,
  saveRegisterDraft,
} from "@/lib/register-draft";
import { postAuthPath, readBillingIntent, saveBillingIntent } from "@/lib/billing-intent";
import { cn } from "@/lib/utils";
import "@/styles/auth-glass.css";

export type AuthTab = "login" | "register";

function readTabFromUrl(): AuthTab {
  if (typeof window === "undefined") return "login";
  const t = new URLSearchParams(window.location.search).get("tab");
  if (t === "register" || t === "create") return "register";
  return "login";
}

export function UnifiedAuth({ initialTab = "login" }: { initialTab?: AuthTab }) {
  const router = useRouter();
  const auth = useTranslations().auth;
  const locale = useClientLocale();
  const ar = locale === "ar";
  const [tab, setTab] = useState<AuthTab>(initialTab);
  /** Après hydratation uniquement — sinon Framer Motion `initial` casse le SSR. */
  const [motionReady, setMotionReady] = useState(false);
  const [successKind, setSuccessKind] = useState<null | "activated" | "reset" | "invite">(null);

  const tabs: { id: AuthTab; label: string }[] = [
    { id: "login", label: auth.tabLogin },
    { id: "register", label: auth.tabRegister },
  ];

  useEffect(() => {
    setMotionReady(true);
    setTab(readTabFromUrl());
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    if (params.get("reset") === "1") setSuccessKind("reset");
    else if (params.get("activated") === "1") setSuccessKind("activated");
    else if (params.get("invite") === "1") setSuccessKind("invite");
  }, []);

  function clearSuccessQuery() {
    setSuccessKind(null);
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    params.delete("activated");
    params.delete("reset");
    params.delete("invite");
    const q = params.toString();
    router.replace(q ? `/login?${q}` : "/login", { scroll: false });
  }

  function go(next: AuthTab) {
    setTab(next);
    const params = new URLSearchParams(typeof window !== "undefined" ? window.location.search : "");
    params.delete("tab");
    if (next !== "login") params.set("tab", next);
    const q = params.toString();
    router.replace(q ? `/login?${q}` : "/login", { scroll: false });
  }

  useEffect(() => {
    const intent = readBillingIntent();
    if (intent?.plan) saveBillingIntent(intent);
  }, []);

  return (
    <div
      className="auth-glass-page relative min-h-screen overflow-hidden"
      dir={ar ? "rtl" : "ltr"}
      suppressHydrationWarning
    >
      <div className="absolute inset-0 z-0" aria-hidden>
        <AuthParticles />
      </div>
      <div
        className="pointer-events-none absolute inset-0 z-[1]"
        style={{
          background:
            "linear-gradient(120deg, rgba(7,16,51,0.22) 0%, rgba(11,26,77,0.08) 48%, rgba(42,18,8,0.18) 100%)",
        }}
        aria-hidden
      />

      <header className="auth-glass-nav relative z-10">
        <Link href="/" className="inline-flex shrink-0">
          <LexHubLogo size="sm" dark withWordmark className="scale-95" />
        </Link>
        <div className="flex flex-wrap items-center justify-end gap-2">
          <div className="auth-seg" role="tablist" aria-label="Auth panels">
            {tabs.map((t) => (
              <button
                key={t.id}
                type="button"
                role="tab"
                data-active={tab === t.id}
                aria-selected={tab === t.id}
                onClick={() => go(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>
          <LanguageSwitch variant="dark" />
        </div>
      </header>

      <div className="relative z-10 mx-auto grid max-w-6xl gap-6 px-4 py-6 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:px-8">
        <AuthProductDemo />

        <div className="order-2 lg:order-1">
          <div className="auth-glass-card border border-[rgba(140,170,255,0.28)] p-5 shadow-xl sm:p-7">
            <AnimatePresence mode="wait">
              <motion.div
                key={tab}
                initial={motionReady ? { opacity: 0.4, y: 8 } : false}
                animate={{ opacity: 1, y: 0 }}
                exit={motionReady ? { opacity: 0, y: -4 } : undefined}
                transition={{ duration: 0.22 }}
              >
                {tab === "login" && <LoginPanel onGo={go} />}
                {tab === "register" && <RegisterStepper onGo={go} />}
              </motion.div>
            </AnimatePresence>
          </div>
          <footer className="mt-4 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 px-2 text-xs text-white/70">
            <span className="inline-flex items-center gap-1">
              <KeyRound className="h-3.5 w-3.5 text-[#A8C0FF]" />
              {auth.lockNote}
            </span>
            <Link href="/mentions-legales" className="hover:text-white hover:underline">
              {auth.authFooterLegal}
            </Link>
            <Link href="/confidentialite" className="hover:text-white hover:underline">
              {auth.authFooterPrivacy}
            </Link>
          </footer>
        </div>
      </div>
      <AuthSuccessModal
        open={!!successKind}
        kind={successKind || "activated"}
        ar={ar}
        onClose={clearSuccessQuery}
      />
    </div>
  );
}

function LoginPanel({ onGo }: { onGo: (t: AuthTab) => void }) {
  const setAuth = useAuthStore((s) => s.setAuth);
  const existingUser = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const hydrated = useAuthStore((s) => s._hasHydrated);
  const auth = useTranslations().auth;
  const ar = useClientLocale() === "ar";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [needs2fa, setNeeds2fa] = useState(false);
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionExpired, setSessionExpired] = useState(false);
  const [failCount, setFailCount] = useState(0);
  const [captchaEnabled, setCaptchaEnabled] = useState(false);
  const [captchaSiteKey, setCaptchaSiteKey] = useState("");
  const [captchaAfter, setCaptchaAfter] = useState(3);
  const [captchaToken, setCaptchaToken] = useState<string | null>(null);
  const [forceCaptcha, setForceCaptcha] = useState(false);
  const [captchaBypass, setCaptchaBypass] = useState(false);
  const [captchaReset, setCaptchaReset] = useState(0);
  const [sessionLive, setSessionLive] = useState(false);
  const [sessionCheckDone, setSessionCheckDone] = useState(false);
  const [wantsOtherLogin, setWantsOtherLogin] = useState(false);

  const showCaptcha =
    captchaEnabled && !captchaBypass && (forceCaptcha || failCount >= captchaAfter);

  useEffect(() => {
    const expired = new URLSearchParams(window.location.search).get("expired") === "1";
    setSessionExpired(expired);
    if (expired) useAuthStore.getState().logout();
    const intent = readBillingIntent();
    if (intent?.plan) saveBillingIntent(intent);
    const emailQ = new URLSearchParams(window.location.search).get("email");
    if (emailQ) setEmail(emailQ);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    let cancelled = false;
    (async () => {
      const token = useAuthStore.getState().token;
      if (!token && !existingUser) {
        if (!cancelled) {
          setSessionLive(false);
          setSessionCheckDone(true);
        }
        return;
      }
      try {
        await api.getMe();
        if (!cancelled) setSessionLive(true);
      } catch {
        useAuthStore.getState().logout();
        if (!cancelled) setSessionLive(false);
      } finally {
        if (!cancelled) setSessionCheckDone(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [hydrated, existingUser]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const cfg = await api.getCaptchaConfig();
        if (cancelled) return;
        setCaptchaEnabled(Boolean(cfg.enabled && cfg.site_key));
        setCaptchaSiteKey(cfg.site_key || "");
        setCaptchaAfter(Math.max(1, cfg.after_failures || 3));
      } catch {
        /* captcha optionnel */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function completeLogin(data: Awaited<ReturnType<typeof api.login>>) {
    setAuth(data, { remember });
    window.location.assign(postAuthPath(data.user.role));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const cleaned = normalizeEmail(email);
    if (!cleaned || !password) {
      setError(auth.loginError);
      return;
    }
    if (showCaptcha && !captchaToken) {
      setError(auth.captchaRequired);
      return;
    }
    setLoading(true);
    try {
      await completeLogin(
        await api.login({
          email: cleaned,
          password,
          totp_code: needs2fa ? totpCode : undefined,
          captcha_token: captchaToken || undefined,
        }),
      );
    } catch (err) {
      if (err instanceof ApiError && err.message === "2FA_REQUIRED") {
        setNeeds2fa(true);
        setError(auth.totpRequired);
      } else if (err instanceof ApiError && err.message === "CAPTCHA_REQUIRED") {
        setCaptchaBypass(false);
        setForceCaptcha(true);
        setFailCount((n) => Math.max(n + 1, captchaAfter));
        setCaptchaToken(null);
        setCaptchaReset((n) => n + 1);
        setPassword("");
        setError(auth.captchaRequired);
      } else if (
        err instanceof ApiError &&
        (err.message === "JOIN_PENDING" || /قيد المراجعة/.test(err.message))
      ) {
        setFailCount((n) => n + 1);
        setPassword("");
        setError(`${auth.joinPendingTitle} — ${auth.joinPendingDesc}`);
      } else {
        setFailCount((n) => n + 1);
        setCaptchaToken(null);
        setCaptchaReset((n) => n + 1);
        setPassword("");
        setError(err instanceof ApiError ? err.message : auth.loginError);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      {sessionCheckDone && sessionLive && existingUser && !wantsOtherLogin ? (
        <div className="mb-5 rounded-xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm text-[#0B1A4D]">
          <p className="font-semibold">
            {ar ? "حساب محفوظ على هذا الجهاز" : "Compte mémorisé sur cet appareil"}
          </p>
          <p className="mt-1 text-[13px] leading-relaxed">
            {ar
              ? `وُجد حساب ${existingUser.full_name} من زيارة سابقة (حتى بعد إعادة تشغيل الحاسوب). هذا ليس قفلاً: يمكنكم المتابعة أو الدخول بحساب آخر.`
              : `Le navigateur a retrouvé ${existingUser.full_name} depuis une visite précédente (même après redémarrage). Ce n’est pas un blocage : continuez, ou connectez-vous avec un autre compte.`}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button
              type="button"
              className="h-10"
              onClick={() => {
                const intent = readBillingIntent();
                window.location.href = postAuthPath(existingUser.role);
              }}
            >
              {ar ? "متابعة" : "Continuer vers mon espace"}
            </Button>
            <Button
              type="button"
              variant="outline"
              className="h-10"
              onClick={() => {
                logout();
                setEmail("");
                setPassword("");
                setSessionLive(false);
                setWantsOtherLogin(true);
              }}
            >
              {ar ? "دخول بحساب آخر" : "Se connecter avec un autre compte"}
            </Button>
          </div>
        </div>
      ) : null}
      <h2 className="text-center font-serif text-2xl text-[#0B1A4D]">
        {auth.loginTitle}
      </h2>
      <p className="mt-1 text-center text-sm text-[#2C3B5C]/80">{auth.loginSubtitle}</p>
      <form onSubmit={(e) => void handleSubmit(e)} className="mt-6 space-y-4" noValidate>
        <Input
          label={auth.email}
          type="email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            if (e.target.value.trim()) setWantsOtherLogin(true);
          }}
          required
          autoFocus
          autoComplete="email"
          placeholder={auth.emailPlaceholder}
          className="h-11 rounded-xl bg-white"
          disabled={loading}
        />
        <PasswordInput
          label={auth.password}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
          disabled={loading}
        />
        {needs2fa && (
          <Input
            label={auth.totpCode}
            inputMode="numeric"
            maxLength={6}
            value={totpCode}
            onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
            required
            className="h-11 rounded-xl tracking-[0.3em] bg-white"
          />
        )}
        {showCaptcha && captchaSiteKey ? (
          <LexHubTurnstile
            siteKey={captchaSiteKey}
            onToken={setCaptchaToken}
            onLoadError={() => {
              setError(auth.captchaRequired);
            }}
            label={auth.captchaTitle}
            hint={auth.captchaHint}
            resetKey={captchaReset}
          />
        ) : null}
        <div className="flex items-center justify-end text-sm">
            <Link href="/forgot-password" className="text-[#0B1A4D]/80 hover:underline">
              {auth.forgot}
            </Link>
        </div>
        {sessionExpired && (
          <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
            {auth.sessionExpired}
          </p>
        )}
        {error && (
          <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}
        <Button
          type="submit"
          className="h-11 w-full rounded-xl bg-[#0B1A4D] font-serif text-white hover:bg-[#12307A]"
          disabled={loading || (showCaptcha && !captchaToken)}
        >
          {loading ? auth.loginLoading : auth.loginSubmit}
        </Button>
        <p className="text-center text-[11px] text-[#2C3B5C]/70">{auth.secureSession}</p>
      </form>

      <div className="mt-6 space-y-2 text-center text-sm text-[#2C3B5C]">
        <p>
          {auth.noAccount}{" "}
          <button
            type="button"
            className="font-medium text-[#0B1A4D] hover:underline"
            onClick={() => onGo("register")}
          >
            {auth.createFirm}
          </button>
        </p>
        <p className="text-xs text-slate-500">
          {ar
            ? "للانضمام إلى مكتب موجود، اطلبوا دعوة بالبريد من مسؤول المكتب."
            : "Pour rejoindre un cabinet existant, demandez une invitation par email à l’administrateur."}
        </p>
      </div>
    </div>
  );
}

function RegisterStepper({ onGo }: { onGo: (t: AuthTab) => void }) {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const auth = useTranslations().auth;
  const locale = useClientLocale();
  const ar = locale === "ar";
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [emailVerified, setEmailVerified] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [emailOtp, setEmailOtp] = useState("");
  const [form, setForm] = useState(emptyRegisterForm);
  const [draftLoaded, setDraftLoaded] = useState(false);

  useEffect(() => {
    const draft = loadRegisterDraft();
    const q = new URLSearchParams(window.location.search);
    const plan = (q.get("plan") || "").trim();
    const cycle = q.get("cycle") === "yearly" ? "yearly" : "monthly";
    const intent = q.get("intent") || undefined;
    const emailQ = (q.get("email") || "").trim();
    const refQ = (q.get("ref") || "").trim().toUpperCase();
    if (plan) {
      saveBillingIntent({ plan, cycle, intent: intent || (plan === "free" ? "free" : "trial") });
    }
    if (draft) {
      setStep(draft.step);
      setForm({
        ...draft.form,
        email: emailQ || draft.form.email,
        referral_code: refQ || draft.form.referral_code || "",
      });
      setEmailVerified(draft.emailVerified);
      setOtpSent(draft.otpSent);
      setEmailOtp(draft.emailOtp);
    } else if (emailQ || refQ) {
      setForm((prev) => ({
        ...prev,
        ...(emailQ ? { email: emailQ } : {}),
        ...(refQ ? { referral_code: refQ } : {}),
      }));
    }
    setDraftLoaded(true);
  }, []);

  useEffect(() => {
    if (!draftLoaded) return;
    saveRegisterDraft({ step, form, emailVerified, otpSent, emailOtp });
  }, [step, form, emailVerified, otpSent, emailOtp, draftLoaded]);

  function update(field: string, value: string | boolean) {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (field === "email") {
      setEmailVerified(false);
      setOtpSent(false);
      setEmailOtp("");
    }
  }

  const strength = passwordStrength(form.password);
  const rules = passwordRules(form.password);
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
      setError(auth.emailInvalid);
      return;
    }
    setLoading(true);
    try {
      const res = await api.requestRegisterOtp(email);
      setOtpSent(true);
      setInfo(res.message);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : auth.registerError);
    } finally {
      setLoading(false);
    }
  }

  async function confirmEmailCode() {
    setError("");
    if (emailOtp.length !== 6) {
      setError(auth.otpRequired);
      return false;
    }
    setLoading(true);
    try {
      await api.verifyRegisterOtp(normalizeEmail(form.email), emailOtp);
      setEmailVerified(true);
      setInfo(auth.emailVerifiedOk);
      return true;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : auth.otpInvalid);
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function nextStep() {
    setError("");
    if (step === 1) {
      if (!emailVerified) {
        if (!otpSent) {
          await sendEmailCode();
          return;
        }
        const ok = await confirmEmailCode();
        if (!ok) return;
      }
      setStep(2);
      return;
    }
    if (step === 2) {
      if (form.cabinet_name.trim().length < 2) return setError(auth.fieldRequired);
      if (form.city.trim().length < 2) return setError(auth.fieldRequired);
      if (form.barreau.trim().length < 2) return setError(auth.fieldRequired);
      if (form.address.trim().length < 5) return setError(auth.fieldRequired);
      // Téléphone optionnel — compléter plus tard dans Paramètres
      setStep(3);
      return;
    }
    if (step === 3) {
      if (form.manager_name.trim().length < 2) return setError(auth.fieldRequired);
      setStep(4);
    }
  }

  async function submit() {
    setError("");
    if (!emailVerified) return setError(auth.verifyEmailFirst);
    if (!isPasswordStrong(form.password)) return setError(auth.pwdWeak);
    if (form.password !== form.confirm_password) return setError(auth.pwdMismatch);
    if (!form.accept_terms) return setError(auth.termsRequired);
    setLoading(true);
    try {
      const email = normalizeEmail(form.email);
      await api.register({
        cabinet_name: form.cabinet_name.trim(),
        city: form.city.trim(),
        address: form.address.trim(),
        barreau: form.barreau.trim(),
        ice: form.ice.trim() || undefined,
        manager_name: form.manager_name.trim(),
        email,
        phone: form.phone.trim() || undefined,
        password: form.password,
        email_otp: emailOtp,
        referral_code: form.referral_code.trim() || undefined,
      });
      const loginData = await api.login({ email, password: form.password });
      clearRegisterDraft();
      setAuth(loginData, { remember: true });
      window.location.assign(postAuthPath(loginData.user.role));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : auth.registerError);
    } finally {
      setLoading(false);
    }
  }

  const primaryLabel =
    step === 1
      ? emailVerified
        ? auth.continue
        : otpSent
          ? auth.confirmOtp
          : auth.sendOtp
      : step === 4
        ? auth.registerSubmit
        : auth.continue;

  const regSteps = [
    { key: 1, label: auth.stepEmail },
    { key: 2, label: auth.stepCabinet },
    { key: 3, label: auth.stepManager },
    { key: 4, label: auth.stepSecurity },
  ];

  return (
    <div>
      <h2 className="text-center font-serif text-2xl text-[#0B1A4D]">{auth.registerTitle}</h2>
      <p className="mt-1 text-center text-sm text-slate-500">{auth.registerSubtitle}</p>

      <div className="auth-stepper mt-5">
        {regSteps.map((s) => (
          <div
            key={s.key}
            className="auth-step"
            data-active={step === s.key}
            data-done={step > s.key}
          >
            <span className="auth-step-dot">
              {step > s.key ? <Check className="h-3.5 w-3.5" /> : s.key}
            </span>
            <span className="auth-step-label">{s.label}</span>
          </div>
        ))}
      </div>

      <div className="space-y-4">
        {step === 1 && (
          <>
            <Input
              label={auth.email}
              type="email"
              value={form.email}
              onChange={(e) => update("email", e.target.value)}
              disabled={emailVerified || loading}
              className="h-11 rounded-xl bg-white"
            />
            {otpSent && !emailVerified && (
              <Input
                label={auth.otpLabel}
                inputMode="numeric"
                maxLength={6}
                value={emailOtp}
                onChange={(e) => setEmailOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
                placeholder="000000"
                className="h-11 rounded-xl tracking-[0.35em] bg-white"
              />
            )}
            {emailVerified && (
              <p className="text-sm font-medium text-emerald-700">{auth.emailVerifiedLabel}</p>
            )}
          </>
        )}

        {step === 2 && (
          <div className="space-y-3">
            <p className="text-xs leading-relaxed text-slate-500">{auth.stepCabinetHint}</p>
            <div className="grid gap-3 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <Input
                label={auth.cabinetName}
                hint={auth.cabinetNameHint}
                placeholder={auth.cabinetNamePlaceholder}
                value={form.cabinet_name}
                onChange={(e) => update("cabinet_name", e.target.value)}
                className="h-11 rounded-xl bg-white"
              />
            </div>
            <Input
              label={auth.city}
              hint={auth.cityHint}
              placeholder={auth.cityPlaceholder}
              value={form.city}
              onChange={(e) => update("city", e.target.value)}
              className="h-11 rounded-xl bg-white"
            />
            <Input
              label={auth.barreau}
              hint={auth.barreauHint}
              placeholder={auth.barreauPlaceholder}
              value={form.barreau}
              onChange={(e) => update("barreau", e.target.value)}
              className="h-11 rounded-xl bg-white"
            />
            <div className="sm:col-span-2">
              <Input
                label={auth.address}
                hint={auth.addressHint}
                placeholder={auth.addressPlaceholder}
                value={form.address}
                onChange={(e) => update("address", e.target.value)}
                className="h-11 rounded-xl bg-white"
              />
            </div>
            <Input
              label={`${auth.phone} (${auth.optional})`}
              hint={
                ar
                  ? "اختياري — يمكن إضافته لاحقاً من الإعدادات"
                  : "Optionnel — vous pourrez le compléter dans Paramètres"
              }
              placeholder={auth.phonePlaceholder}
              type="tel"
              value={form.phone}
              onChange={(e) => update("phone", e.target.value)}
              className="h-11 rounded-xl bg-white"
            />
            <Input
              label={`${auth.ice} (${auth.optional})`}
              hint={auth.iceHint}
              placeholder={auth.icePlaceholder}
              value={form.ice}
              onChange={(e) => update("ice", e.target.value)}
              className="h-11 rounded-xl bg-white"
            />
            <div className="sm:col-span-2">
              <Input
                label={ar ? "رمز الإحالة (اختياري)" : "Code de parrainage (optionnel)"}
                hint={
                  ar
                    ? "إذا دعاكم مكتب آخر — +14 يوماً عند بدء Solo/Cabinet"
                    : "Si un cabinet vous a invité — +14 jours d’essai en démarrant Solo/Cabinet"
                }
                placeholder="LH-XXXX-XXXX"
                value={form.referral_code}
                onChange={(e) => update("referral_code", e.target.value.toUpperCase())}
                className="h-11 rounded-xl bg-white font-mono tracking-wide"
              />
            </div>
            </div>
          </div>
        )}

        {step === 3 && (
          <Input
            label={auth.managerName}
            hint={auth.managerNameHint}
            placeholder={auth.managerNamePlaceholder}
            value={form.manager_name}
            onChange={(e) => update("manager_name", e.target.value)}
            className="h-11 rounded-xl bg-white"
          />
        )}

        {step === 4 && (
          <>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <PasswordInput
                  label={auth.password}
                  value={form.password}
                  onChange={(e) => update("password", e.target.value)}
                />
                {form.password && (
                  <div className="mt-2 space-y-2">
                    <div className="flex gap-1">
                      {[0, 1, 2, 3].map((i) => (
                        <div
                          key={i}
                          className={cn(
                            "h-1 flex-1 rounded",
                            i < strength
                              ? strengthColors[Math.max(0, strength - 1)]
                              : "bg-slate-200",
                          )}
                        />
                      ))}
                    </div>
                    <ul className="grid gap-1 text-[11px] text-[#2C3B5C] sm:col-span-2">
                      {(
                        [
                          ["length", auth.pwdRuleLength, rules.length],
                          ["upperLower", auth.pwdRuleCase, rules.upperLower],
                          ["digit", auth.pwdRuleDigit, rules.digit],
                          ["symbol", auth.pwdRuleSymbol, rules.symbol],
                        ] as const
                      ).map(([key, label, ok]) => (
                        <li key={key} className="flex items-center gap-1.5">
                          <Check
                            className={cn(
                              "h-3.5 w-3.5",
                              ok ? "text-emerald-600" : "text-slate-300",
                            )}
                          />
                          <span className={ok ? "text-emerald-800" : undefined}>{label}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              <PasswordInput
                label={auth.confirmPassword}
                value={form.confirm_password}
                onChange={(e) => update("confirm_password", e.target.value)}
                error={!passwordsMatch ? auth.pwdMismatch : undefined}
              />
            </div>
            <label className="flex items-start gap-2.5 text-sm text-[#2C3B5C]">
              <input
                type="checkbox"
                checked={form.accept_terms}
                onChange={(e) => update("accept_terms", e.target.checked)}
                className="mt-1 h-4 w-4 rounded accent-[#0B1A4D]"
              />
              <span>
                {auth.acceptTerms}{" "}
                <LegalDocLink
                  doc="terms"
                  label={auth.termsLink}
                  locale={locale}
                  previewHint={auth.legalPreviewHint}
                  backLabel={auth.legalBackRegister}
                />{" "}
                {auth.andPrivacy.replace(/\.$/, "")}{" "}
                <LegalDocLink
                  doc="privacy"
                  label={auth.authFooterPrivacy}
                  locale={locale}
                  previewHint={auth.legalPreviewHint}
                  backLabel={auth.legalBackRegister}
                />
                .
              </span>
            </label>
          </>
        )}

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

        <div className="flex flex-wrap gap-2 pt-1">
          {step > 1 && (
            <Button
              type="button"
              variant="outline"
              className="flex-1"
              onClick={() => {
                setError("");
                setStep((s) => Math.max(1, s - 1));
              }}
            >
              {auth.previous}
            </Button>
          )}
          <Button
            type="button"
            className="h-11 flex-[1.4] rounded-xl bg-[#0B1A4D] font-serif text-white hover:bg-[#12307A]"
            disabled={loading}
            onClick={() => void (step === 4 ? submit() : nextStep())}
          >
            {loading ? "…" : primaryLabel}
          </Button>
        </div>
      </div>

      <p className="mt-5 text-center text-sm text-[#2C3B5C]">
        {auth.hasAccount}{" "}
        <button
          type="button"
          className="font-medium text-[#0B1A4D] hover:underline"
          onClick={() => onGo("login")}
        >
          {auth.signIn}
        </button>
      </p>
    </div>
  );
}

