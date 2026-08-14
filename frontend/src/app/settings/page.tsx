"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { TeamPanel } from "@/components/settings/team-panel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, ApiError, type CabinetSettings, type TwoFactorSetup } from "@/lib/api";
import { canManageTeam, roleLabel } from "@/lib/roles";
import { useAuthStore } from "@/store/auth";
import { useLocaleStore, useTranslations } from "@/store/locale";
import { cn } from "@/lib/utils";

type Tab = "general" | "team";

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const locale = useLocaleStore((s) => s.locale);
  const t = useTranslations().app.settings;
  const isAdmin = canManageTeam(user?.role);
  const isPlatformAdmin = user?.role === "admin_webvoice";
  const [tab, setTab] = useState<Tab>("general");
  const [mfaQuery, setMfaQuery] = useState(false);
  const mfaForced = mfaQuery || isPlatformAdmin;
  const [cabinet, setCabinet] = useState<CabinetSettings | null>(null);
  const [form, setForm] = useState({
    name: "",
    city: "",
    address: "",
    barreau: "",
    ice: "",
    ai_custom_prompt: "",
  });
  const [passwords, setPasswords] = useState({
    current: "",
    new: "",
    confirm: "",
    email_otp: "",
  });
  const [pwdOtpSent, setPwdOtpSent] = useState(false);
  const [twoFactorSetup, setTwoFactorSetup] = useState<TwoFactorSetup | null>(null);
  const [twoFactorCode, setTwoFactorCode] = useState("");
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      setMfaQuery(params.get("mfa") === "1");
    }
    api
      .getMe()
      .then((me) => setTwoFactorEnabled(!!me.totp_enabled))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      if (params.get("tab") === "team" && isAdmin) setTab("team");
    }
    if (!isAdmin) return;
    api
      .getCabinetSettings()
      .then((data) => {
        setCabinet(data);
        setForm({
          name: data.name,
          city: data.city,
          address: data.address,
          barreau: data.barreau,
          ice: data.ice || "",
          ai_custom_prompt: data.ai_custom_prompt || "",
        });
      })
      .catch(() => {});
  }, [isAdmin]);

  async function saveCabinet(e: React.FormEvent) {
    e.preventDefault();
    try {
      const updated = await api.updateCabinetSettings(form);
      setCabinet(updated);
      setMessage(t.updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur");
    }
  }

  async function sendPasswordOtp() {
    setError("");
    try {
      const res = await api.requestPasswordOtp();
      setPwdOtpSent(true);
      setMessage(res.message + " (dev : http://localhost:8025)");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur");
    }
  }

  async function changePassword(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (passwords.new !== passwords.confirm) {
      setError(t.pwdMismatch);
      return;
    }
    if (passwords.email_otp.length !== 6) {
      setError("Entrez le code à 6 chiffres reçu par email.");
      return;
    }
    try {
      const res = await api.changePassword(
        passwords.new,
        passwords.email_otp,
        passwords.current || undefined,
      );
      setMessage(res.message);
      setPasswords({ current: "", new: "", confirm: "", email_otp: "" });
      setPwdOtpSent(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur");
    }
  }

  async function start2fa() {
    setError("");
    try {
      const setup = await api.setup2fa();
      setTwoFactorSetup(setup);
      setTwoFactorCode("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur");
    }
  }

  async function confirm2fa() {
    setError("");
    try {
      const res = await api.enable2fa(twoFactorCode);
      setMessage(res.message);
      setTwoFactorEnabled(true);
      setTwoFactorSetup(null);
      setTwoFactorCode("");
      setRecoveryCodes(res.recovery_codes || []);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur");
    }
  }

  async function remove2fa() {
    setError("");
    if (isPlatformAdmin) {
      setError("La 2FA est obligatoire pour l'administrateur plateforme.");
      return;
    }
    try {
      const res = await api.disable2fa(twoFactorCode);
      setMessage(res.message);
      setTwoFactorEnabled(false);
      setTwoFactorCode("");
      setRecoveryCodes([]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur");
    }
  }

  const ar = locale === "ar";

  return (
    <AppShell>
      <div className="mx-auto max-w-2xl space-y-6" dir={ar ? "rtl" : "ltr"}>
        <h1 className="text-2xl font-bold text-sanad-slate">{t.title}</h1>

        {isAdmin && (
          <div className="flex gap-1 rounded-xl border border-sanad-border bg-white p-1">
            <button
              type="button"
              onClick={() => setTab("general")}
              className={cn(
                "flex-1 rounded-lg px-3 py-2 text-sm font-medium transition",
                tab === "general"
                  ? "bg-sanad-navy text-white shadow-sm"
                  : "text-sanad-navy/70 hover:bg-sanad-cream",
              )}
            >
              {t.tabGeneral}
            </button>
            <button
              type="button"
              onClick={() => setTab("team")}
              className={cn(
                "flex-1 rounded-lg px-3 py-2 text-sm font-medium transition",
                tab === "team"
                  ? "bg-sanad-navy text-white shadow-sm"
                  : "text-sanad-navy/70 hover:bg-sanad-cream",
              )}
            >
              {t.tabTeam}
            </button>
          </div>
        )}

        {message && (
          <p className="rounded-lg bg-green-50 px-3 py-2 text-sm text-green-700">{message}</p>
        )}
        {error && (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
        )}

        {tab === "team" && isAdmin ? (
          <TeamPanel />
        ) : (
          <>
            {isAdmin && cabinet && (
              <Card>
                <CardHeader>
                  <CardTitle>{t.cabinetInfo}</CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={saveCabinet} className="space-y-4">
                    <Input
                      label={t.cabinetName}
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      required
                    />
                    <div className="grid gap-4 sm:grid-cols-2">
                      <Input
                        label={t.city}
                        value={form.city}
                        onChange={(e) => setForm({ ...form, city: e.target.value })}
                        required
                      />
                      <Input
                        label={t.barreau}
                        value={form.barreau}
                        onChange={(e) => setForm({ ...form, barreau: e.target.value })}
                        required
                      />
                    </div>
                    <Input
                      label={t.address}
                      value={form.address}
                      onChange={(e) => setForm({ ...form, address: e.target.value })}
                      required
                    />
                    <Input
                      label={t.ice}
                      value={form.ice}
                      onChange={(e) => setForm({ ...form, ice: e.target.value })}
                    />
                    <Button type="submit">{t.save}</Button>
                  </form>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader>
                <CardTitle>{t.account}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-slate-600">
                <div className="flex items-center gap-4 rounded-xl border border-sanad-stone bg-sanad-cream/40 p-4">
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-sanad-navy font-serif text-lg font-semibold text-sanad-gold">
                    {(user?.full_name || "?")
                      .split(" ")
                      .map((p) => p[0])
                      .slice(0, 2)
                      .join("")
                      .toUpperCase()}
                  </div>
                  <div>
                    <p className="font-semibold text-sanad-navy">{user?.full_name}</p>
                    <p>{user?.email}</p>
                    <p className="mt-1 text-xs uppercase tracking-wide text-sanad-muted">
                      {roleLabel(user?.role, ar ? "ar" : "fr")}
                      {isAdmin && ar ? " · منسّق" : ""}
                    </p>
                  </div>
                </div>
                <p>
                  <strong>{t.cabinet} :</strong> {user?.cabinet_name}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t.twoFactor}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-slate-600">{t.twoFactorDesc}</p>
                {mfaForced && !twoFactorEnabled && (
                  <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                    Activez la 2FA pour sécuriser votre compte administrateur. Obligatoire
                    pour l&apos;accès admin plateforme.
                  </p>
                )}
                {recoveryCodes.length > 0 && (
                  <div className="rounded-xl border border-sanad-gold/30 bg-sanad-cream/50 p-4">
                    <p className="mb-2 text-sm font-medium text-sanad-navy">
                      Codes de récupération (à conserver hors ligne — affichage unique)
                    </p>
                    <ul className="grid gap-1 font-mono text-xs text-sanad-slate sm:grid-cols-2">
                      {recoveryCodes.map((c) => (
                        <li key={c}>{c}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {twoFactorEnabled ? (
                  <div className="space-y-3">
                    <p className="text-sm font-medium text-green-700">{t.twoFactorEnabled}</p>
                    {!isPlatformAdmin && (
                      <>
                        <Input
                          label={t.enterCode}
                          value={twoFactorCode}
                          onChange={(e) =>
                            setTwoFactorCode(e.target.value.replace(/\D/g, "").slice(0, 6))
                          }
                          maxLength={6}
                        />
                        <Button
                          variant="outline"
                          onClick={remove2fa}
                          disabled={twoFactorCode.length !== 6}
                        >
                          {t.disable2fa}
                        </Button>
                      </>
                    )}
                  </div>
                ) : twoFactorSetup ? (
                  <div className="space-y-4">
                    <p className="text-sm text-slate-600">{t.scanQr}</p>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={`data:image/png;base64,${twoFactorSetup.qr_code_base64}`}
                      alt="QR 2FA"
                      className="mx-auto h-48 w-48 rounded-lg border border-sanad-border"
                    />
                    <p className="text-center font-mono text-sm text-slate-500">
                      {twoFactorSetup.secret}
                    </p>
                    <Input
                      label={t.enterCode}
                      value={twoFactorCode}
                      onChange={(e) =>
                        setTwoFactorCode(e.target.value.replace(/\D/g, "").slice(0, 6))
                      }
                      maxLength={6}
                    />
                    <div className="flex gap-2">
                      <Button onClick={confirm2fa} disabled={twoFactorCode.length !== 6}>
                        {t.confirm}
                      </Button>
                      <Button variant="outline" onClick={() => setTwoFactorSetup(null)}>
                        {t.cancel}
                      </Button>
                    </div>
                  </div>
                ) : (
                  <Button onClick={start2fa}>{t.enable2fa}</Button>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t.security}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="mb-4 text-sm text-slate-600">
                  Changement de mot de passe par code email (pas de 2FA téléphone).
                </p>
                <form onSubmit={changePassword} className="space-y-4">
                  <Input
                    label={t.newPassword}
                    type="password"
                    value={passwords.new}
                    onChange={(e) => setPasswords({ ...passwords, new: e.target.value })}
                    required
                  />
                  <Input
                    label={t.confirmPassword}
                    type="password"
                    value={passwords.confirm}
                    onChange={(e) =>
                      setPasswords({ ...passwords, confirm: e.target.value })
                    }
                    required
                  />
                  <div className="flex flex-wrap items-end gap-2">
                    <div className="min-w-[160px] flex-1">
                      <Input
                        label="Code email"
                        inputMode="numeric"
                        maxLength={6}
                        value={passwords.email_otp}
                        onChange={(e) =>
                          setPasswords({
                            ...passwords,
                            email_otp: e.target.value.replace(/\D/g, "").slice(0, 6),
                          })
                        }
                        placeholder="000000"
                        required
                      />
                    </div>
                    <Button type="button" variant="outline" onClick={() => void sendPasswordOtp()}>
                      {pwdOtpSent ? "Renvoyer le code" : "Envoyer le code"}
                    </Button>
                  </div>
                  <Button type="submit">{t.changePassword}</Button>
                </form>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </AppShell>
  );
}
