/** Intent plan après clic landing / tarifs (style Coursera). */

const KEY = "lexhub_billing_intent";

export type BillingIntent = {
  plan: string;
  cycle: "monthly" | "yearly";
  intent?: string;
};

export function saveBillingIntent(intent: BillingIntent) {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(intent));
  } catch {
    /* ignore */
  }
}

export function readBillingIntent(): BillingIntent | null {
  if (typeof window === "undefined") return null;
  try {
    const fromSs = sessionStorage.getItem(KEY);
    if (fromSs) {
      const parsed = JSON.parse(fromSs) as BillingIntent;
      if (parsed?.plan) return parsed;
    }
  } catch {
    /* ignore */
  }
  const q = new URLSearchParams(window.location.search);
  const plan = (q.get("plan") || "").trim();
  if (!plan) return null;
  const cycle = q.get("cycle") === "yearly" ? "yearly" : "monthly";
  return { plan, cycle, intent: q.get("intent") || undefined };
}

export function clearBillingIntent() {
  try {
    sessionStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}

/** Destination après login / inscription. */
export function postAuthPath(role?: string | null): string {
  if (role === "admin_webvoice") return "/admin";
  const intent = readBillingIntent();
  if (intent?.plan && intent.plan !== "free") {
    return `/checkout?plan=${encodeURIComponent(intent.plan)}&cycle=${intent.cycle}`;
  }
  if (intent?.plan === "free") {
    clearBillingIntent();
    return "/dashboard";
  }
  return "/dashboard";
}

/** @deprecated — plus de qualification commerciale ; conservé pour anciens liens. */
export function commercialHref(_intent: "enterprise" | "custom" = "enterprise") {
  return "/tarifs";
}

/** Plus aucun plan ne passe par un formulaire avant essai. */
export function needsCommercialQualification(_slug: string) {
  return false;
}

export function checkoutHref(plan: string, cycle: "monthly" | "yearly" = "monthly") {
  return `/checkout?plan=${encodeURIComponent(plan)}&cycle=${cycle}`;
}

export function authHrefForPlan(
  plan: string,
  cycle: "monthly" | "yearly" = "monthly",
  tab: "login" | "register" = "register",
) {
  const params = new URLSearchParams({ tab, plan, cycle, intent: plan === "free" ? "free" : "trial" });
  return `/login?${params.toString()}`;
}
