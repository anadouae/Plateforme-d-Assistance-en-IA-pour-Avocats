"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, ApiError, type CabinetSettings, type TeamMember, type TwoFactorSetup } from "@/lib/api";
import { canManageTeam, isAssistant, roleLabel } from "@/lib/roles";
import { restartOnboardingTour } from "@/hooks/use-onboarding";
import { useUiTheme } from "@/hooks/use-ui-prefs";
import { useAuthStore } from "@/store/auth";
import { useLocaleStore, useTranslations } from "@/store/locale";
import { BillingPanel } from "@/components/settings/billing-panel";
import { AdminCabinetCenter } from "@/components/settings/admin-cabinet-center";

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const locale = useLocaleStore((s) => s.locale);
  const ar = locale === "ar";
  const t = useTranslations().app.settings;
  const isAdmin = canManageTeam(user?.role);
  const assistant = isAssistant(user?.role);
  const isPlatformAdmin = user?.role === "admin_webvoice";
  const isCabinetAdmin = user?.role === "admin_cabinet";
  const { theme, setTheme } = useUiTheme();
  const [digestBusy, setDigestBusy] = useState(false);
  const [assistants, setAssistants] = useState<TeamMember[]>([]);
  const [digestIds, setDigestIds] = useState<string[]>([]);
  const [mfaQuery, setMfaQuery] = useState(false);
  const mfaForced = mfaQuery || isPlatformAdmin;
  const [cabinet, setCabinet] = useState<CabinetSettings | null>(null);
  const [form, setForm] = useState({
    name: "",
    name_ar: "",
    city: "",
    address: "",
    barreau: "",
    ice: "",
    ai_custom_prompt: "",
  });
  const [lawyerAr, setLawyerAr] = useState("");
  const [logoBusy, setLogoBusy] = useState(false);
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
  const [delForm, setDelForm] = useState({ password: "", email_otp: "", confirmation: "" });
  const [delOtpSent, setDelOtpSent] = useState(false);
  const [delBusy, setDelBusy] = useState(false);
  const [emailForm, setEmailForm] = useState({ new_email: "", otp: "", password: "" });
  const [emailOtpSent, setEmailOtpSent] = useState(false);
  const [emailBusy, setEmailBusy] = useState(false);
  const logout = useAuthStore((s) => s.logout);
  const router = useRouter();
  type SettingsSection = "general" | "cabinet" | "plan" | "security" | "danger";
  const [section, setSection] = useState<SettingsSection>("general");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const hash = window.location.hash.replace("#", "");
    if (hash === "abonnement" || hash === "plan" || hash === "factures") setSection("plan");
    else if (hash === "parrainage" || hash === "referral") setSection("plan");
    else if (hash === "security" || hash === "securite") setSection("security");
    else if (hash === "cabinet") setSection("cabinet");
    else if (hash === "danger") setSection("danger");
  }, []);

  useEffect(() => {
    if (typeof window === "undefined" || section !== "plan") return;
    const hash = window.location.hash.replace("#", "");
    if (hash !== "parrainage" && hash !== "referral" && hash !== "factures") return;
    const targetId = hash === "factures" ? "factures" : "parrainage";
    const timer = window.setTimeout(() => {
      document.getElementById(targetId)?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 200);
    return () => window.clearTimeout(timer);
  }, [section]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      setMfaQuery(params.get("mfa") === "1");
      if (params.get("mfa") === "1") setSection("security");
    }
    api
      .getMe()
      .then((me) => setTwoFactorEnabled(!!me.totp_enabled))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!isAdmin) return;
    api
      .getCabinetSettings()
      .then((data) => {
        setCabinet(data);
        setForm({
          name: data.name,
          name_ar: data.name_ar || "",
          city: data.city,
          address: data.address,
          barreau: data.barreau,
          ice: data.ice || "",
          ai_custom_prompt: data.ai_custom_prompt || "",
        });
      })
      .catch(() => {});
  }, [isAdmin]);

  useEffect(() => {
    setLawyerAr(user?.full_name_ar || "");
  }, [user?.full_name_ar]);

  useEffect(() => {
    if (!isAdmin) return;
    void api
      .listAssistants()
      .then((list) => {
        setAssistants(list);
        setDigestIds(list.map((a) => a.id));
      })
      .catch(() => setAssistants([]));
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
      setMessage(res.message);
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

  async function sendEmailChangeOtp() {
    setError("");
    const next = emailForm.new_email.trim().toLowerCase();
    if (!next || !next.includes("@")) {
      setError(ar ? "أدخلوا عنوان بريد صالح." : "Entrez une adresse email valide.");
      return;
    }
    setEmailBusy(true);
    try {
      const res = await api.requestEmailChangeOtp(next);
      setEmailOtpSent(true);
      setMessage(
        ar
          ? "تم إرسال رمز إلى العنوان الجديد."
          : res.message || "Un code a été envoyé à la nouvelle adresse.",
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur");
    } finally {
      setEmailBusy(false);
    }
  }

  async function confirmEmailChange(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (emailForm.otp.length !== 6) {
      setError(ar ? "أدخلوا الرمز المكوّن من 6 أرقام." : "Entrez le code à 6 chiffres reçu par email.");
      return;
    }
    if (!emailForm.password) {
      setError(ar ? "كلمة المرور الحالية مطلوبة." : "Mot de passe actuel requis.");
      return;
    }
    setEmailBusy(true);
    try {
      const me = await api.confirmEmailChange(
        emailForm.new_email.trim().toLowerCase(),
        emailForm.otp,
        emailForm.password,
      );
      useAuthStore.setState({ user: me });
      setEmailForm({ new_email: "", otp: "", password: "" });
      setEmailOtpSent(false);
      setMessage(ar ? "تم تغيير البريد. العنوان القديم لم يعد صالحًا لتسجيل الدخول." : "Adresse email mise à jour. L’ancienne ne permet plus de se connecter.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur");
    } finally {
      setEmailBusy(false);
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


  async function sendDeleteOtp() {
    setError("");
    setMessage("");
    try {
      const res = await api.requestAccountDeleteOtp();
      setDelOtpSent(true);
      setMessage(res.message);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur");
    }
  }

  async function onDeleteAccount(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setDelBusy(true);
    try {
      const res = await api.deleteAccount(
        delForm.password,
        delForm.email_otp,
        delForm.confirmation,
      );
      setMessage(res.message || t.deleteDone);
      logout();
      window.setTimeout(() => router.replace("/login"), 1200);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur");
    } finally {
      setDelBusy(false);
    }
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl" dir={ar ? "rtl" : "ltr"}>
        <h1 className="mb-5 text-2xl font-bold text-sanad-slate">{t.title}</h1>

        {message && (
          <p className="mb-4 rounded-lg bg-green-50 px-3 py-2 text-sm text-green-700">{message}</p>
        )}
        {error && (
          <p className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
        )}

        <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
          <nav className="w-full shrink-0 rounded-2xl border border-slate-200/80 bg-[#F7F5F0]/70 p-2 lg:sticky lg:top-20 lg:w-56">
            {(
              [
                { id: "general" as const, label: ar ? "عام" : "Général" },
                ...(isAdmin ? [{ id: "cabinet" as const, label: ar ? "المكتب" : "Cabinet" }] : []),
                ...(!isPlatformAdmin
                  ? [
                      {
                        id: "plan" as const,
                        label: assistant
                          ? ar
                            ? "الاستخدام"
                            : "Usage"
                          : ar
                            ? "الخطة والاستخدام"
                            : "Plan & usage",
                      },
                    ]
                  : []),
                { id: "security" as const, label: ar ? "الأمان" : "Sécurité" },
                ...(!isPlatformAdmin
                  ? [{ id: "danger" as const, label: ar ? "منطقة الخطر" : "Zone sensible" }]
                  : []),
              ] as { id: SettingsSection; label: string }[]
            ).map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  setSection(item.id);
                  if (typeof window !== "undefined") {
                    const h =
                      item.id === "plan"
                        ? "abonnement"
                        : item.id === "security"
                          ? "securite"
                          : item.id;
                    window.history.replaceState(null, "", `#${h}`);
                  }
                }}
                className={`mb-0.5 flex w-full rounded-xl px-3 py-2.5 text-start text-sm transition ${
                  section === item.id
                    ? "bg-white font-semibold text-[#0B1A4D] shadow-sm"
                    : "text-slate-600 hover:bg-white/70"
                }`}
              >
                {item.label}
              </button>
            ))}
          </nav>

          <div className="min-w-0 flex-1 space-y-6 rounded-2xl border border-slate-200/70 bg-white p-5 shadow-sm sm:p-7">
        <div className={section === "cabinet" ? "space-y-6" : "hidden"}>
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
                    <Input
                      label={ar ? "اسم المكتب بالعربية" : "Nom du cabinet (arabe)"}
                      value={form.name_ar}
                      onChange={(e) => setForm({ ...form, name_ar: e.target.value })}
                      dir="rtl"
                    />
                    <div className="space-y-2 rounded-xl border border-sanad-stone bg-sanad-cream/30 p-4">
                      <p className="text-sm font-semibold text-sanad-navy">
                        {ar ? "شعار المكتب" : "Logo du cabinet"}
                      </p>
                      <p className="text-xs text-slate-500">
                        {ar
                          ? "يظهر مع ترويسة المكتب على Word/PDF. PNG أو JPG ≤ 1.5 ميغا."
                          : "Sur Word/PDF avec le nom du cabinet (AR / FR). PNG/JPG ≤ 1,5 Mo."}
                      </p>
                      {cabinet.has_logo ? (
                        <p className="text-xs text-emerald-700">{ar ? "شعار محمّل" : "Logo enregistré"}</p>
                      ) : null}
                      <label className="inline-flex cursor-pointer rounded-lg bg-sanad-navy px-3 py-2 text-sm text-white">
                        {logoBusy ? "…" : ar ? "رفع الشعار" : "Téléverser"}
                        <input
                          type="file"
                          accept="image/png,image/jpeg,image/webp"
                          className="hidden"
                          disabled={logoBusy}
                          onChange={(e) => {
                            const f = e.target.files?.[0];
                            if (!f) return;
                            setLogoBusy(true);
                            setError("");
                            void api
                              .uploadCabinetLogo(f)
                              .then((updated) => {
                                setCabinet(updated);
                                setMessage(ar ? "تم حفظ الشعار." : "Logo enregistré.");
                                return api.getMe();
                              })
                              .then((me) => {
                                if (me) useAuthStore.setState({ user: me });
                              })
                              .catch((err) =>
                                setError(err instanceof ApiError ? err.message : "Erreur logo"),
                              )
                              .finally(() => setLogoBusy(false));
                          }}
                        />
                      </label>
                    </div>
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
        </div>

        <div className={section === "general" ? "space-y-6" : "hidden"}>
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
                  <div className="flex-1 space-y-2">
                    <p className="font-semibold text-sanad-navy">{user?.full_name}</p>
                    <p>{user?.email}</p>
                    <form className="mt-3 space-y-2" onSubmit={(e) => void confirmEmailChange(e)}>
                      <p className="text-xs font-semibold uppercase tracking-wide text-sanad-muted">
                        {ar ? "تغيير البريد" : "Changer l'email"}
                      </p>
                      <Input
                        type="email"
                        label={ar ? "البريد الجديد" : "Nouvelle adresse"}
                        value={emailForm.new_email}
                        onChange={(e) =>
                          setEmailForm({ ...emailForm, new_email: e.target.value })
                        }
                        autoComplete="email"
                      />
                      {emailOtpSent ? (
                        <>
                          <Input
                            label={ar ? "رمز من البريد الجديد" : "Code reçu sur le nouvel email"}
                            value={emailForm.otp}
                            onChange={(e) =>
                              setEmailForm({
                                ...emailForm,
                                otp: e.target.value.replace(/\D/g, "").slice(0, 6),
                              })
                            }
                            inputMode="numeric"
                          />
                          <Input
                            type="password"
                            label={ar ? "كلمة المرور الحالية" : "Mot de passe actuel"}
                            value={emailForm.password}
                            onChange={(e) =>
                              setEmailForm({ ...emailForm, password: e.target.value })
                            }
                            autoComplete="current-password"
                          />
                          <Button type="submit" disabled={emailBusy}>
                            {ar ? "تأكيد العنوان الجديد" : "Confirmer la nouvelle adresse"}
                          </Button>
                        </>
                      ) : (
                        <Button
                          type="button"
                          variant="outline"
                          disabled={emailBusy}
                          onClick={() => void sendEmailChangeOtp()}
                        >
                          {ar ? "إرسال رمز التحقق" : "Envoyer le code de vérification"}
                        </Button>
                      )}
                      <p className="text-[11px] text-slate-500">
                        {ar
                          ? "يُرسل الرمز إلى العنوان الجديد. تُخطر العنوان الحالي أيضًا."
                          : "Le code part sur la nouvelle adresse. L’ancienne est aussi notifiée."}
                      </p>
                    </form>
                    {!assistant ? (
                      <>
                        <Input
                          label={ar ? "الاسم بالعربية (التوقيع على المرافعات)" : "Nom en arabe (signature plaidoiries)"}
                          value={lawyerAr}
                          dir="rtl"
                          onChange={(e) => setLawyerAr(e.target.value)}
                        />
                        <Button
                          type="button"
                          onClick={() => {
                            void api
                              .updateProfileNames({ full_name_ar: lawyerAr || undefined })
                              .then((me) => {
                                useAuthStore.setState({ user: me });
                                setMessage(ar ? "تم حفظ الاسم العربي." : "Nom arabe enregistré.");
                              })
                              .catch((err) =>
                                setError(err instanceof ApiError ? err.message : "Erreur"),
                              );
                          }}
                        >
                          {ar ? "حفظ الاسم العربي" : "Enregistrer le nom arabe"}
                        </Button>
                      </>
                    ) : null}
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

            {!assistant ? (
            <Card>
              <CardHeader>
                <CardTitle>{ar ? "المظهر" : "Thème de l’espace de travail"}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant={theme === "light" ? "default" : "outline"}
                    onClick={() => setTheme("light")}
                  >
                    {ar ? "فاتح" : "Clair"}
                  </Button>
                  <Button
                    type="button"
                    variant={theme === "dark" ? "default" : "outline"}
                    onClick={() => setTheme("dark")}
                  >
                    {ar ? "داكن" : "Sombre"}
                  </Button>
                </div>
              </CardContent>
            </Card>
            ) : null}

            {isAdmin ? (
              <Card>
                <CardHeader>
                  <CardTitle>{t.digest}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-slate-600">{t.digestDesc}</p>
                  {assistants.length === 0 ? (
                    <p className="text-sm text-amber-800">
                      {ar
                        ? "لا مساعد في المكتب — أضيفوا مساعداً من صفحة الفريق أولاً."
                        : "Aucun assistant dans le cabinet — invitez-en un depuis Équipe d’abord."}
                    </p>
                  ) : (
                    <ul className="space-y-2 rounded-xl border border-slate-200 bg-white px-3 py-2">
                      {assistants.map((a) => (
                        <li key={a.id} className="flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            id={`digest-${a.id}`}
                            checked={digestIds.includes(a.id)}
                            onChange={() =>
                              setDigestIds((prev) =>
                                prev.includes(a.id)
                                  ? prev.filter((id) => id !== a.id)
                                  : [...prev, a.id],
                              )
                            }
                          />
                          <label htmlFor={`digest-${a.id}`} className="cursor-pointer">
                            {a.full_name} · {a.email}
                          </label>
                        </li>
                      ))}
                    </ul>
                  )}
                  <Button
                    type="button"
                    variant="outline"
                    disabled={digestBusy || digestIds.length === 0}
                    onClick={() => {
                      setDigestBusy(true);
                      setError("");
                      void api
                        .sendNotificationsDigest(digestIds)
                        .then((res) => {
                          setMessage(
                            res.message ||
                              (ar
                                ? `تم الإرسال إلى ${res.sent} مساعد(ين)`
                                : `Envoyé à ${res.sent} assistant(s) sélectionné(s)`),
                          );
                        })
                        .catch((err) =>
                          setError(err instanceof ApiError ? err.message : "Erreur digest"),
                        )
                        .finally(() => setDigestBusy(false));
                    }}
                  >
                    {digestBusy ? "…" : t.digestSend}
                  </Button>
                </CardContent>
              </Card>
            ) : null}

            {isAdmin ? (
              <AdminCabinetCenter />
            ) : null}
        </div>

        <div className={section === "plan" ? "space-y-6" : "hidden"}>
            {!isPlatformAdmin ? (
              <Suspense fallback={<Card><CardContent className="py-8 text-sm text-slate-500">…</CardContent></Card>}>
                <BillingPanel />
              </Suspense>
            ) : null}
        </div>

        <div className={section === "general" ? "space-y-6" : "hidden"}>
            <Card>
              <CardHeader>
                <CardTitle>{ar ? "الجولة التعريفية" : "Visite guidée"}</CardTitle>
              </CardHeader>
              <CardContent>
                <Button type="button" variant="outline" onClick={() => restartOnboardingTour()}>
                  {ar ? "إعادة تشغيل الجولة" : "Relancer la visite"}
                </Button>
              </CardContent>
            </Card>
        </div>

        <div className={section === "security" ? "space-y-6" : "hidden"}>
            {!assistant ? (
            <Card>
              <CardHeader>
                <CardTitle>{t.twoFactor}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-slate-600">{t.twoFactorDesc}</p>
                {mfaForced && !twoFactorEnabled && (
                  <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                    {ar
                      ? "فعّلوا المصادقة الثنائية لتأمين حساب المسؤول. إلزامية لوصول إدارة المنصة."
                      : "Activez la 2FA pour sécuriser votre compte administrateur. Obligatoire pour l'accès admin plateforme."}
                  </p>
                )}
                {recoveryCodes.length > 0 && (
                  <div className="rounded-xl border border-sanad-gold/30 bg-sanad-cream/50 p-4">
                    <p className="mb-2 text-sm font-medium text-sanad-navy">
                      {ar
                        ? "رموز الاسترداد (احفظوها دون اتصال — عرض مرة واحدة)"
                        : "Codes de récupération (à conserver hors ligne — affichage unique)"}
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
            ) : null}

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
        </div>

        <div className={section === "danger" ? "space-y-6" : "hidden"}>
            {!isPlatformAdmin ? (
              <Card className="border-red-200/80">
                <CardHeader>
                  <CardTitle className="text-red-800">{t.dangerZone}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-sm font-semibold text-red-900">
                      {isCabinetAdmin ? t.deleteAccountCabinet : t.deleteAccountMember}
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      {isCabinetAdmin ? t.deleteAccountCabinetDesc : t.deleteAccountMemberDesc}
                    </p>
                    <p className="mt-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs leading-relaxed text-slate-600">
                      {isCabinetAdmin ? t.deleteAccountCabinetNote : t.deleteAccountMemberNote}
                    </p>
                  </div>
                  <form onSubmit={onDeleteAccount} className="space-y-3">
                    <Input
                      label={t.deletePassword}
                      type="password"
                      autoComplete="current-password"
                      value={delForm.password}
                      onChange={(e) => setDelForm({ ...delForm, password: e.target.value })}
                      required
                    />
                    <div className="flex flex-wrap items-end gap-2">
                      <div className="min-w-[160px] flex-1">
                        <Input
                          label={t.deleteOtp}
                          value={delForm.email_otp}
                          onChange={(e) =>
                            setDelForm({
                              ...delForm,
                              email_otp: e.target.value.replace(/\D/g, "").slice(0, 6),
                            })
                          }
                          maxLength={6}
                          required
                        />
                      </div>
                      <Button type="button" variant="outline" onClick={() => void sendDeleteOtp()}>
                        {t.deleteSendOtp}
                      </Button>
                    </div>
                    {delOtpSent ? (
                      <p className="text-xs text-slate-500">Code envoyé — valable 15 minutes.</p>
                    ) : null}
                    <Input
                      label={t.deleteConfirmLabel}
                      value={delForm.confirmation}
                      onChange={(e) => setDelForm({ ...delForm, confirmation: e.target.value })}
                      placeholder="SUPPRIMER"
                      required
                    />
                    <Button
                      type="submit"
                      variant="outline"
                      className="border-red-300 text-red-800 hover:bg-red-50"
                      disabled={
                        delBusy ||
                        delForm.email_otp.length !== 6 ||
                        !delForm.password ||
                        !delForm.confirmation
                      }
                    >
                      {t.deleteSubmit}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            ) : null}
        </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
