"use client";

import { useState } from "react";
import Link from "next/link";
import { KeyRound, Mail, Shield } from "lucide-react";
import { LexHubLogo } from "@/components/brand/sanad-logo";
import { LanguageSwitch } from "@/components/layout/language-switch";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";
import { normalizeEmail } from "@/lib/password";
import { useClientLocale, useTranslations } from "@/store/locale";
import "@/styles/auth-glass.css";

export default function ForgotPasswordPage() {
  const auth = useTranslations().auth;
  const locale = useClientLocale();
  const ar = locale === "ar";
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const cleaned = normalizeEmail(email);
    if (!cleaned) return;
    setLoading(true);
    try {
      await api.forgotPassword(cleaned);
      setSent(true);
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 429
          ? auth.forgotRateLimited
          : err instanceof ApiError
            ? err.message
            : auth.registerError,
      );
    } finally {
      setLoading(false);
    }
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
      </div>

      <header className="auth-glass-nav relative z-10">
        <Link href="/" className="inline-flex shrink-0">
          <LexHubLogo size="sm" withWordmark className="scale-95" />
        </Link>
        <LanguageSwitch />
      </header>

      <div className="relative z-10 mx-auto max-w-md px-4 py-10">
        <div
          className="auth-glass-card border border-[#E85A00]/25 bg-white p-6 shadow-xl sm:p-8"
          style={{ background: "#ffffff" }}
        >
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#0B1A4D]/5">
            <Mail className="h-6 w-6 text-[#0B1A4D]" />
          </div>
          <h1 className="text-center font-serif text-2xl text-[#0B1A4D]">{auth.forgot}</h1>
          <p className="mt-2 text-center text-sm text-[#2C3B5C]/80">{auth.forgotHint}</p>

          {sent ? (
            <p className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-3 text-center text-sm text-emerald-900">
              {auth.forgotSent}
            </p>
          ) : (
            <form onSubmit={(e) => void handleSubmit(e)} className="mt-6 space-y-4">
              <Input
                label={auth.email}
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={auth.emailPlaceholder}
                required
                autoFocus
                autoComplete="email"
                className="h-11 rounded-xl bg-white"
              />
              {error && (
                <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                  {error}
                </p>
              )}
              <Button
                type="submit"
                className="h-11 w-full rounded-xl bg-[#0B1A4D] font-serif text-white hover:bg-[#12307A]"
                disabled={loading}
              >
                {loading ? "…" : auth.forgotSend}
              </Button>
            </form>
          )}

          <Link
            href="/login"
            className="mt-5 block text-center text-sm font-medium text-[#0B1A4D] hover:underline"
          >
            {auth.forgotBack}
          </Link>
        </div>

        <div className="mt-4 space-y-2 rounded-xl border border-[#0B1A4D]/10 bg-white/80 px-4 py-3 text-xs leading-relaxed text-[#2C3B5C]/85">
          <p className="flex items-start gap-2">
            <Shield className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#E85A00]" />
            {auth.forgotSecurityNote}
          </p>
          <p className="flex items-center gap-1.5 text-[#2C3B5C]/75">
            <KeyRound className="h-3.5 w-3.5 text-[#E85A00]" />
            {auth.lockNote}
          </p>
        </div>
      </div>
    </div>
  );
}
