"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AuthLayout } from "@/components/auth/auth-layout";
import { PasswordInput } from "@/components/auth/password-input";
import { GoogleSignIn } from "@/components/auth/google-sign-in";
import { api, ApiError } from "@/lib/api";
import { normalizeEmail } from "@/lib/password";
import { useAuthStore } from "@/store/auth";
import { useTranslations } from "@/store/locale";

export function LoginForm() {
  const searchParams = useSearchParams();
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
  const sessionExpired = searchParams.get("expired") === "1";

  useEffect(() => {
    if (sessionExpired) useAuthStore.getState().logout();
  }, [sessionExpired]);

  async function completeLogin(data: Awaited<ReturnType<typeof api.login>>) {
    setAuth(data, { remember });
    const dest = data.user.role === "admin_webvoice" ? "/admin" : "/dashboard";
    window.location.assign(dest);
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
      const data = await api.login({
        email: cleaned,
        password,
        totp_code: needs2fa ? totpCode : undefined,
      });
      await completeLogin(data);
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

  async function handleGoogle(idToken: string) {
    setError("");
    setLoading(true);
    try {
      await completeLogin(await api.googleLogin(idToken));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : auth.loginError);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout>
      <div className="rounded-2xl border border-white/50 bg-white/95 p-7 shadow-royal sm:p-8">
        <h1 className="text-center font-serif text-2xl text-sanad-navy">{auth.loginTitle}</h1>

        <form onSubmit={handleSubmit} className="mt-7 space-y-4" noValidate>
          <Input
            label={auth.email}
            type="email"
            name="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            className="h-11 rounded-xl"
            disabled={loading}
          />
          <PasswordInput
            label={auth.password}
            name="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            disabled={loading}
          />
          {needs2fa && (
            <Input
              label={auth.totpCode}
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
              required
              className="h-11 rounded-xl tracking-[0.3em]"
            />
          )}

          <div className="flex items-center justify-between text-sm">
            <label className="flex items-center gap-2 text-sanad-muted">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="h-4 w-4 rounded accent-sanad-navy"
              />
              {auth.remember}
            </label>
            <Link href="/forgot-password" className="text-sanad-navy/70 hover:underline">
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
              Lien envoyé. Vérifiez votre boîte mail.
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
          className="mt-3 w-full text-center text-sm text-sanad-navy/70 underline-offset-2 hover:underline"
        >
          Recevoir un lien de connexion
        </button>

        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-sanad-navy/10" />
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="bg-white px-3 text-sanad-muted">{auth.or}</span>
          </div>
        </div>

        <GoogleSignIn label={auth.google} onSuccess={handleGoogle} disabled={loading} />

        <p className="mt-6 text-center text-sm text-sanad-muted">
          {auth.noAccount}{" "}
          <Link href="/register" className="font-medium text-sanad-navy hover:underline">
            {auth.createFirm}
          </Link>
        </p>
      </div>
    </AuthLayout>
  );
}
