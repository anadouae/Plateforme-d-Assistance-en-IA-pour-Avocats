import type { Locale } from "@/lib/i18n/translations";
import { getTranslations } from "@/lib/i18n/translations";
import { canManageTeam, isAssistant } from "@/lib/roles";

/** Config déclarative du tour — facile à réordonner / étendre. */
export type OnboardingStepConfig = {
  id: string;
  /** Sélecteur stable : [data-tour-id="…"] — vide = carte centrée (accueil). */
  target: string;
  /** Si true, étape réservée aux admins cabinet. */
  adminOnly?: boolean;
  /** Si true, uniquement assistant. */
  assistantOnly?: boolean;
  /** Si true, avocat / admin cabinet (pas assistant). */
  lawyerOnly?: boolean;
  titleKey: keyof ReturnType<typeof getTranslations>["app"]["onboarding"]["steps"];
  bodyKey: keyof ReturnType<typeof getTranslations>["app"]["onboarding"]["steps"];
};

/**
 * Tour court (2–3 étapes) — bienvenue + cœur produit.
 * Le reste (docs, agenda, équipe…) se découvre dans la nav.
 */
export const ONBOARDING_STEP_DEFS: OnboardingStepConfig[] = [
  {
    id: "welcome",
    target: "",
    titleKey: "welcomeTitle",
    bodyKey: "welcomeBody",
  },
  {
    id: "welcome-assistant",
    target: "",
    assistantOnly: true,
    titleKey: "welcomeAssistantTitle",
    bodyKey: "welcomeAssistantBody",
  },
  {
    id: "redaction",
    target: '[data-tour-id="nav-redaction"]',
    lawyerOnly: true,
    titleKey: "redactionTitle",
    bodyKey: "redactionBody",
  },
  {
    id: "redaction-assistant",
    target: '[data-tour-id="nav-redaction"]',
    assistantOnly: true,
    titleKey: "redactionAssistantTitle",
    bodyKey: "redactionAssistantBody",
  },
  {
    id: "cases",
    target: '[data-tour-id="nav-cases"]',
    titleKey: "casesTitle",
    bodyKey: "casesBody",
  },
];

export type ResolvedTourStep = {
  id: string;
  target: string;
  title: string;
  body: string;
};

export function resolveOnboardingSteps(
  locale: Locale,
  role: string | undefined | null,
): ResolvedTourStep[] {
  const t = getTranslations(locale).app.onboarding.steps;
  const assistant = isAssistant(role);
  const admin = canManageTeam(role);

  return ONBOARDING_STEP_DEFS.filter((s) => {
    if (s.id === "welcome" && assistant) return false;
    if (s.adminOnly && !admin) return false;
    if (s.assistantOnly && !assistant) return false;
    if (s.lawyerOnly && assistant) return false;
    return true;
  }).map((s) => ({
    id: s.id,
    target: s.target,
    title: t[s.titleKey],
    body: t[s.bodyKey],
  }));
}

export function formatTourStepIndex(current: number, total: number, locale: Locale): string {
  if (locale === "ar") {
    const eastern = (n: number) =>
      String(n).replace(/\d/g, (d) => "٠١٢٣٤٥٦٧٨٩"[Number(d)]!);
    return `${eastern(current)} من ${eastern(total)}`;
  }
  if (locale === "fr") return `${current} / ${total}`;
  return `${current} of ${total}`;
}
