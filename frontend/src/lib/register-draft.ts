/** Brouillon inscription — sessionStorage (survit à la lecture des CGU). */

export const REGISTER_DRAFT_KEY = "lexhub-register-draft";

export type RegisterFormDraft = {
  cabinet_name: string;
  city: string;
  address: string;
  barreau: string;
  ice: string;
  manager_name: string;
  email: string;
  phone: string;
  password: string;
  confirm_password: string;
  accept_terms: boolean;
  referral_code: string;
};

export type RegisterDraft = {
  step: number;
  form: RegisterFormDraft;
  emailVerified: boolean;
  otpSent: boolean;
  emailOtp: string;
};

export const emptyRegisterForm = (): RegisterFormDraft => ({
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
  referral_code: "",
});

export function loadRegisterDraft(): RegisterDraft | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(REGISTER_DRAFT_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as RegisterDraft;
    if (!parsed?.form) return null;
    return {
      step: Math.min(4, Math.max(1, Number(parsed.step) || 1)),
      form: { ...emptyRegisterForm(), ...parsed.form },
      emailVerified: Boolean(parsed.emailVerified),
      otpSent: Boolean(parsed.otpSent),
      emailOtp: String(parsed.emailOtp || ""),
    };
  } catch {
    return null;
  }
}

export function saveRegisterDraft(draft: RegisterDraft): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(REGISTER_DRAFT_KEY, JSON.stringify(draft));
  } catch {
    /* quota / private mode */
  }
}

export function clearRegisterDraft(): void {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(REGISTER_DRAFT_KEY);
}
