"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Clock3, KeyRound, Scale } from "lucide-react";
import { SanadLogo } from "@/components/brand/sanad-logo";
import { LanguageSwitch } from "@/components/layout/language-switch";
import { GoogleSignIn } from "@/components/auth/google-sign-in";
import { PasswordInput } from "@/components/auth/password-input";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";
import { isPasswordStrong, normalizeEmail, passwordStrength } from "@/lib/password";
import { useAuthStore } from "@/store/auth";
import { useLocaleStore, useTranslations } from "@/store/locale";
import { cn } from "@/lib/utils";
import "@/styles/auth-glass.css";

export type AuthTab = "login" | "register" | "join";

function readTabFromUrl(): AuthTab {
  if (typeof window === "undefined") return "login";
  const t = new URLSearchParams(window.location.search).get("tab");
  if (t === "register" || t === "create") return "register";
  if (t === "join") return "join";
  return "login";
}

export function UnifiedAuth({ initialTab = "login" }: { initialTab?: AuthTab }) {
  const router = useRouter();
  const auth = useTranslations().auth;
  const locale = useLocaleStore((s) => s.locale);
  const ar = locale === "ar";
  const [tab, setTab] = useState<AuthTab>(initialTab);

  const tabs: { id: AuthTab; label: string }[] = [
    { id: "login", label: auth.tabLogin },
    { id: "register", label: auth.tabRegister },
    { id: "join", label: auth.tabJoin },
  ];

  useEffect(() => {
    setTab(readTabFromUrl());
  }, []);

  function go(next: AuthTab) {
    setTab(next);
    const q = next === "login" ? "/login" : `/login?tab=${next}`;
    router.replace(q, { scroll: false });
  }

  return (
    <div
      className="auth-glass-page min-h-screen bg-[#F6EFDD]"
      dir={ar ? "rtl" : "ltr"}
      style={{ backgroundColor: "#F6EFDD" }}
    >
      <div className="auth-glass-bg" aria-hidden>
        <div className="auth-glass-blob auth-glass-blob--a" />
        <div className="auth-glass-blob auth-glass-blob--b" />
        <div className="auth-glass-blob auth-glass-blob--c" />
      </div>

      <header className="auth-glass-nav relative z-10">
        <Link href="/" className="inline-flex shrink-0">
          <SanadLogo size="sm" withWordmark className="scale-95" />
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
          <LanguageSwitch />
        </div>
      </header>

      <div className="relative z-10 mx-auto grid max-w-6xl gap-6 px-4 py-6 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:px-8">
        <aside className="order-1 rounded-3xl border border-white/50 bg-[#16233F] p-5 text-white shadow-xl sm:p-6 lg:order-2 lg:p-8">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl border border-[#E8C577]/40 bg-white/10 lg:mb-6 lg:h-14 lg:w-14">
            <Scale className="h-6 w-6 text-[#E8C577] lg:h-7 lg:w-7" />
          </div>
          <h1 className="font-serif text-2xl font-semibold leading-tight text-white sm:text-3xl lg:text-5xl">
            {auth.sideTitle}
          </h1>
          <p className="mt-2 font-serif text-base text-[#E8C577] lg:mt-4 lg:text-xl">
            {auth.sideDesc}
          </p>
          <p className="mt-3 hidden text-sm text-white/65 lg:mt-6 lg:block">
            {auth.sideSecure}
          </p>
        </aside>

        <div className="order-2 lg:order-1">
          <div
            className="auth-glass-card border border-[#B08D3F]/25 bg-white p-5 shadow-xl sm:p-7"
            style={{ background: "#ffffff" }}
          >
            <AnimatePresence mode="wait">
              <motion.div
                key={tab}
                initial={{ opacity: 0.4, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.22 }}
              >
                {tab === "login" && <LoginPanel onGo={go} />}
                {tab === "register" && <RegisterStepper onGo={go} />}
                {tab === "join" && <JoinPanel onGo={go} />}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}

function LoginPanel({ onGo }: { onGo: (t: AuthTab) => void }) {
  const setAuth = useAuthStore((s) => s.setAuth);
  const auth = useTranslations().auth;
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [needs2fa, setNeeds2fa] = useState(false);
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState("");
  const [magicSent, setMagicSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [sessionExpired, setSessionExpired] = useState(false);

  useEffect(() => {
    const expired = new URLSearchParams(window.location.search).get("expired") === "1";
    setSessionExpired(expired);
    if (expired) useAuthStore.getState().logout();
  }, []);

  async function completeLogin(data: Awaited<ReturnType<typeof api.login>>) {
    setAuth(data, { remember });
    window.location.assign(data.user.role === "admin_webvoice" ? "/admin" : "/home");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setMagicSent(false);
    const cleaned = normalizeEmail(email);
    if (!cleaned || !password) {
      setError(auth.loginError);
      return;
    }
    setLoading(true);
    try {
      await completeLogin(
        await api.login({
          email: cleaned,
          password,
          totp_code: needs2fa ? totpCode : undefined,
        }),
      );
    } catch (err) {
      if (err instanceof ApiError && err.message === "2FA_REQUIRED") {
        setNeeds2fa(true);
        setError(auth.totpRequired);
      } else {
        setPassword("");
        setError(err instanceof ApiError ? err.message : auth.loginError);
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleMagicLink() {
    setError("");
    setMagicSent(false);
    const cleaned = normalizeEmail(email);
    if (!cleaned) {
      setError(auth.emailInvalid);
      return;
    }
    setLoading(true);
    try {
      await api.requestMagicLink(cleaned);
      setMagicSent(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : auth.loginError);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2 className="text-center font-serif text-2xl text-[#0B1F4A]">
        {auth.loginTitle}
      </h2>
      <form onSubmit={(e) => void handleSubmit(e)} className="mt-6 space-y-4" noValidate>
        <Input
          label={auth.email}
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoComplete="email"
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
        <div className="flex items-center justify-between text-sm">
          <label className="flex items-center gap-2 text-[#2C3B5C]">
            <input
              type="checkbox"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
              className="h-4 w-4 rounded accent-[#0B1F4A]"
            />
            {auth.remember}
          </label>
          <Link href="/forgot-password" className="text-[#0B1F4A]/80 hover:underline">
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
        {magicSent && (
          <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
            {auth.magicLinkSent}
          </p>
        )}
        <Button
          type="submit"
          className="h-11 w-full rounded-xl bg-[#0B1F4A] font-serif text-white hover:bg-[#14306B]"
          disabled={loading}
        >
          {loading ? auth.loginLoading : auth.loginSubmit}
        </Button>
      </form>

      <button
        type="button"
        onClick={() => void handleMagicLink()}
        disabled={loading}
        className="mt-3 w-full text-center text-sm text-[#0B1F4A]/70 underline-offset-2 hover:underline"
      >
        {auth.magicLink}
      </button>

      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-[#0B1F4A]/10" />
        </div>
        <div className="relative flex justify-center text-xs">
          <span className="bg-white px-3 text-[#2C3B5C]">{auth.or}</span>
        </div>
      </div>

      <GoogleSignIn
        label={auth.google}
        onSuccess={async (idToken) => {
          setLoading(true);
          setError("");
          try {
            await completeLogin(await api.googleLogin(idToken));
          } catch (err) {
            setError(err instanceof ApiError ? err.message : auth.loginError);
          } finally {
            setLoading(false);
          }
        }}
        disabled={loading}
      />

      <div className="mt-6 space-y-2 text-center text-sm text-[#2C3B5C]">
        <p>
          {auth.noAccount}{" "}
          <button
            type="button"
            className="font-medium text-[#0B1F4A] hover:underline"
            onClick={() => onGo("register")}
          >
            {auth.createFirm}
          </button>
        </p>
        <p>
          <button
            type="button"
            className="font-medium text-[#0B1F4A] hover:underline"
            onClick={() => onGo("join")}
          >
            {auth.tabJoin}
          </button>
        </p>
      </div>
    </div>
  );
}

function RegisterStepper({ onGo }: { onGo: (t: AuthTab) => void }) {
  const router = useRouter();
  const auth = useTranslations().auth;
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [emailVerified, setEmailVerified] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [emailOtp, setEmailOtp] = useState("");
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
    if (field === "email") {
      setEmailVerified(false);
      setOtpSent(false);
      setEmailOtp("");
    }
  }

  const strength = passwordStrength(form.password);
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
      setInfo(res.message + " — Dev : http://localhost:8025");
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
      if (form.phone.replace(/\D/g, "").length < 8) return setError(auth.phoneInvalid);
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
      <h2 className="text-center font-serif text-2xl text-[#0B1F4A]">{auth.registerTitle}</h2>
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
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <Input
                label={auth.cabinetName}
                value={form.cabinet_name}
                onChange={(e) => update("cabinet_name", e.target.value)}
                className="h-11 rounded-xl bg-white"
              />
            </div>
            <Input
              label={auth.city}
              value={form.city}
              onChange={(e) => update("city", e.target.value)}
              className="h-11 rounded-xl bg-white"
            />
            <Input
              label={auth.barreau}
              value={form.barreau}
              onChange={(e) => update("barreau", e.target.value)}
              className="h-11 rounded-xl bg-white"
            />
            <div className="sm:col-span-2">
              <Input
                label={auth.address}
                value={form.address}
                onChange={(e) => update("address", e.target.value)}
                className="h-11 rounded-xl bg-white"
              />
            </div>
            <Input
              label={auth.phone}
              type="tel"
              value={form.phone}
              onChange={(e) => update("phone", e.target.value)}
              className="h-11 rounded-xl bg-white"
            />
            <Input
              label={`${auth.ice} (${auth.optional})`}
              value={form.ice}
              onChange={(e) => update("ice", e.target.value)}
              className="h-11 rounded-xl bg-white"
            />
          </div>
        )}

        {step === 3 && (
          <Input
            label={auth.managerName}
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
                  <div className="mt-2 flex gap-1">
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
                className="mt-1 h-4 w-4 rounded accent-[#0B1F4A]"
              />
              <span>
                {auth.acceptTerms}{" "}
                <Link href="/confidentialite" className="text-[#0B1F4A] hover:underline">
                  {auth.termsLink}
                </Link>{" "}
                {auth.andPrivacy}
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
            className="h-11 flex-[1.4] rounded-xl bg-[#0B1F4A] font-serif text-white hover:bg-[#14306B]"
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
          className="font-medium text-[#0B1F4A] hover:underline"
          onClick={() => onGo("login")}
        >
          {auth.signIn}
        </button>
      </p>
    </div>
  );
}

function JoinPanel({ onGo }: { onGo: (t: AuthTab) => void }) {
  const auth = useTranslations().auth;
  const [code, setCode] = useState("");
  const [codeOk, setCodeOk] = useState<boolean | null>(null);
  const [checking, setChecking] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });

  useEffect(() => {
    const raw = code.trim().toUpperCase();
    if (raw.length < 6) {
      setCodeOk(null);
      return;
    }
    const t = setTimeout(() => {
      setChecking(true);
      api
        .validateJoinCode(raw)
        .then((r) => setCodeOk(r.valid))
        .catch(() => setCodeOk(false))
        .finally(() => setChecking(false));
    }, 450);
    return () => clearTimeout(t);
  }, [code]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!codeOk) return setError(auth.joinInvalidCode);
    if (form.full_name.trim().length < 2) return setError(auth.joinNameRequired);
    const email = normalizeEmail(form.email);
    if (!email) return setError(auth.emailInvalid);
    if (!isPasswordStrong(form.password)) return setError(auth.pwdWeak);
    setLoading(true);
    try {
      await api.submitJoinRequest({
        code: code.trim().toUpperCase(),
        full_name: form.full_name.trim(),
        email,
        password: form.password,
      });
      setPending(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : auth.joinSendError);
    } finally {
      setLoading(false);
    }
  }

  if (pending) {
    return (
      <div className="py-4 text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-amber-50 text-amber-700">
          <Clock3 className="h-7 w-7" />
        </div>
        <h2 className="font-serif text-2xl text-[#0B1F4A]">{auth.joinPendingTitle}</h2>
        <p className="mx-auto mt-3 max-w-sm text-sm text-slate-600">{auth.joinPendingDesc}</p>
        <Button type="button" className="mt-6" onClick={() => onGo("login")}>
          {auth.joinBackLogin}
        </Button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#16233F] text-[#E8C577]">
          <KeyRound className="h-5 w-5" />
        </div>
        <div>
          <h2 className="font-serif text-2xl text-[#0B1F4A]">{auth.joinTitle}</h2>
          <p className="text-sm text-slate-500">{auth.joinSubtitle}</p>
        </div>
      </div>

      <p className="mb-4 rounded-xl border border-amber-200/80 bg-amber-50 px-3 py-2.5 text-xs leading-relaxed text-amber-950">
        {auth.joinNotice}
      </p>

      <form onSubmit={(e) => void submit(e)} className="space-y-4">
        <div>
          <Input
            label={auth.joinCode}
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            placeholder="ATLAS-7F2K"
            className="h-11 rounded-xl bg-white font-mono tracking-wider"
            dir="ltr"
            required
          />
          <p className="mt-1 text-xs text-slate-500">
            {checking && auth.joinChecking}
            {!checking && codeOk === true && (
              <span className="text-emerald-700">{auth.joinCodeValid}</span>
            )}
            {!checking && codeOk === false && code.trim().length >= 6 && (
              <span className="text-red-600">{auth.joinCodeInvalid}</span>
            )}
          </p>
        </div>
        <Input
          label={auth.joinFullName}
          value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          className="h-11 rounded-xl bg-white"
          required
        />
        <Input
          label={auth.email}
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          className="h-11 rounded-xl bg-white"
          dir="ltr"
          required
        />
        <PasswordInput
          label={auth.password}
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />
        {error && (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        )}
        <Button
          type="submit"
          className="h-11 w-full rounded-xl bg-[#0B1F4A] font-serif text-white"
          disabled={loading || !codeOk}
        >
          {loading ? "…" : auth.joinSubmit}
        </Button>
      </form>

      <p className="mt-5 text-center text-sm text-[#2C3B5C]">
        <button
          type="button"
          className="font-medium text-[#0B1F4A] hover:underline"
          onClick={() => onGo("register")}
        >
          {auth.createNewCabinet}
        </button>
        {" · "}
        <button
          type="button"
          className="font-medium text-[#0B1F4A] hover:underline"
          onClick={() => onGo("login")}
        >
          {auth.signIn}
        </button>
      </p>
    </div>
  );
}
