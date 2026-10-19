"use client";

import { useEffect, useMemo, useState } from "react";
import { KeyRound, X } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { isPasswordStrong, passwordRules, passwordStrength } from "@/lib/password";
import { PasswordInput } from "@/components/auth/password-input";
import { useAuthStore } from "@/store/auth";
import { useClientLocale } from "@/store/locale";
import { cn } from "@/lib/utils";

const DISMISS_KEY = "lexhub_pwd_banner_dismiss_day";

function todayKey() {
  return new Date().toISOString().slice(0, 10);
}

export function SetPasswordModal({
  open,
  onClose,
  title,
  subtitle,
}: {
  open: boolean;
  onClose: () => void;
  title?: string;
  subtitle?: string;
}) {
  const ar = useClientLocale() === "ar";
  const setAuth = useAuthStore((s) => s.setAuth);
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const strength = passwordStrength(password);
  const rules = passwordRules(password);
  const colors = ["bg-red-500", "bg-orange-400", "bg-amber-400", "bg-emerald-500"];

  useEffect(() => {
    if (!open) {
      setPassword("");
      setConfirm("");
      setError("");
    }
  }, [open]);

  if (!open) return null;

  async function submit() {
    setError("");
    if (!isPasswordStrong(password)) {
      setError(ar ? "كلمة المرور ضعيفة." : "Mot de passe trop faible.");
      return;
    }
    if (password !== confirm) {
      setError(ar ? "كلمتا المرور غير متطابقتين." : "Les mots de passe ne correspondent pas.");
      return;
    }
    setLoading(true);
    try {
      const updated = await api.setPassword(password);
      if (token && user) {
        setAuth(
          {
            access_token: token,
            refresh_token: "",
            token_type: "bearer",
            user: { ...user, ...updated, must_set_password: false },
          },
          { remember: true },
        );
      }
      onClose();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : ar ? "تعذر الحفظ." : "Impossible d’enregistrer.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[10050] flex items-end justify-center bg-black/40 p-4 sm:items-center" role="dialog">
      <div className="w-full max-w-md rounded-2xl border border-[var(--line)] bg-white p-5 shadow-2xl">
        <div className="mb-3 flex items-start justify-between gap-3">
          <div>
            <h3 className="font-serif text-lg text-[#0B1A4D]">
              {title || (ar ? "أنشئوا كلمة مرور" : "Sécurisez votre compte")}
            </h3>
            <p className="mt-1 text-sm text-slate-600">
              {subtitle ||
                (ar
                  ? "دقيقة واحدة — لحماية الدخول القادم والاشتراك والفريق."
                  : "30 secondes — pour protéger la prochaine connexion, l’abonnement et l’équipe.")}
            </p>
          </div>
          <button type="button" onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100" aria-label="Fermer">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="space-y-3">
          <PasswordInput label={ar ? "كلمة المرور" : "Mot de passe"} value={password} onChange={(e) => setPassword(e.target.value)} />
          {password ? (
            <div className="flex gap-1">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className={cn("h-1 flex-1 rounded", i < strength ? colors[Math.max(0, strength - 1)] : "bg-slate-200")} />
              ))}
            </div>
          ) : null}
          <PasswordInput label={ar ? "تأكيد" : "Confirmation"} value={confirm} onChange={(e) => setConfirm(e.target.value)} />
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
          <button
            type="button"
            disabled={loading}
            onClick={() => void submit()}
            className="w-full rounded-xl bg-[#0B1A4D] py-2.5 text-sm font-semibold text-white disabled:opacity-60"
          >
            {loading ? "…" : ar ? "حفظ كلمة المرور" : "Enregistrer le mot de passe"}
          </button>
          <ul className="grid gap-0.5 text-[11px] text-slate-500">
            {(
              [
                [rules.length, ar ? "١٢ حرفاً على الأقل" : "12 caractères min."],
                [rules.upperLower, ar ? "أحرف كبيرة وصغيرة" : "Majuscules + minuscules"],
                [rules.digit, ar ? "رقم" : "Un chiffre"],
                [rules.symbol, ar ? "رمز" : "Un symbole"],
              ] as const
            ).map(([ok, label], i) => (
              <li key={i} className={ok ? "text-emerald-700" : undefined}>
                {ok ? "✓" : "·"} {label}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

/** Soft banner — max 1× / jour si dismissed ; pulse léger. */
export function SetPasswordBanner() {
  const user = useAuthStore((s) => s.user);
  const ar = useClientLocale() === "ar";
  const [openModal, setOpenModal] = useState(false);
  const [hidden, setHidden] = useState(true);

  const needed = Boolean(user?.must_set_password) && !user?.auth_via_google;

  useEffect(() => {
    if (!needed) {
      setHidden(true);
      return;
    }
    try {
      const d = sessionStorage.getItem(DISMISS_KEY);
      setHidden(d === todayKey());
    } catch {
      setHidden(false);
    }
  }, [needed]);

  // Après 1ʳᵉ session utile (~90s) : rappeler une fois si pas encore créé
  useEffect(() => {
    if (!needed || !hidden) return;
    const t = window.setTimeout(() => {
      try {
        if (sessionStorage.getItem(DISMISS_KEY) !== todayKey()) setHidden(false);
      } catch {
        setHidden(false);
      }
    }, 90_000);
    return () => window.clearTimeout(t);
  }, [needed, hidden]);

  if (!needed || hidden) {
    return <SetPasswordModal open={openModal} onClose={() => setOpenModal(false)} />;
  }

  return (
    <>
      <div
        className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-xl border border-amber-300 bg-gradient-to-r from-amber-50 to-orange-50 px-3 py-2.5 text-sm text-amber-950 shadow-sm"
        role="status"
      >
        <span className="flex items-center gap-2 font-medium">
          <KeyRound className="h-4 w-4 shrink-0 text-amber-700" />
          {ar
            ? "أمّنوا حسابكم: أنشئوا كلمة مرور (٣٠ ثانية)."
            : "Sécurisez votre compte : créez un mot de passe (30 s)."}
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="rounded-lg bg-[#0B1A4D] px-3 py-1.5 text-xs font-semibold text-white"
            onClick={() => setOpenModal(true)}
          >
            {ar ? "إنشاء الآن" : "Créer maintenant"}
          </button>
          <button
            type="button"
            className="rounded-lg px-2 py-1.5 text-xs text-amber-800/80 hover:underline"
            onClick={() => {
              try {
                sessionStorage.setItem(DISMISS_KEY, todayKey());
              } catch {
                /* ignore */
              }
              setHidden(true);
            }}
          >
            {ar ? "لاحقاً" : "Plus tard"}
          </button>
        </div>
      </div>
      <SetPasswordModal open={openModal} onClose={() => setOpenModal(false)} />
    </>
  );
}

/** Hard gate helper — ouvre la modal si PASSWORD_REQUIRED. */
export function usePasswordGate() {
  const user = useAuthStore((s) => s.user);
  const ar = useClientLocale() === "ar";
  const [open, setOpen] = useState(false);
  const needed = Boolean(user?.must_set_password) && !user?.auth_via_google;

  const ensurePassword = useMemo(
    () => () => {
      if (needed) {
        setOpen(true);
        return false;
      }
      return true;
    },
    [needed],
  );

  const gateFromError = (msg: string) => {
    if (msg.includes("PASSWORD_REQUIRED")) {
      setOpen(true);
      return true;
    }
    return false;
  };

  return {
    needed,
    ensurePassword,
    gateFromError,
    modal: (
      <SetPasswordModal
        open={open}
        onClose={() => setOpen(false)}
        subtitle={
          ar
            ? "مطلوب قبل الاشتراك أو دعوة الفريق."
            : "Obligatoire avant un abonnement ou une invitation d’équipe."
        }
      />
    ),
  };
}
