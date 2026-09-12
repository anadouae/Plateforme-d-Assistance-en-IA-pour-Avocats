/** Rôles cabinet LexHub — alignés sur le backend UserRole. */

export type CabinetRole =
  | "avocat"
  | "assistant_juridique"
  | "admin_cabinet"
  | "admin_webvoice";

/** Libellés FR */
export const ROLE_LABELS: Record<string, string> = {
  avocat: "Avocat",
  assistant_juridique: "Assistant",
  admin_cabinet: "Admin cabinet",
  admin_webvoice: "Admin plateforme",
};

/** Libellés AR (UI cabinet) */
export const ROLE_LABELS_AR: Record<string, string> = {
  avocat: "محامٍ",
  assistant_juridique: "مساعد",
  admin_cabinet: "مسؤول المكتب",
  admin_webvoice: "منصة",
};

/** Rôles assignables à l'approbation d'une demande */
export const ASSIGNABLE_ROLES = [
  { value: "avocat", labelAr: "محامٍ", labelFr: "Avocat" },
  { value: "assistant_juridique", labelAr: "مساعد", labelFr: "Assistant" },
  { value: "admin_cabinet", labelAr: "مسؤول المكتب", labelFr: "Admin cabinet" },
] as const;

export function isAssistant(role?: string | null): boolean {
  return role === "assistant_juridique";
}

export function canUseAI(role?: string | null): boolean {
  return role === "avocat" || role === "admin_cabinet";
}

/** منسّق = admin_cabinet — seul rôle qui gère les membres */
export function canManageTeam(role?: string | null): boolean {
  return role === "admin_cabinet";
}

export function canUseTemplates(role?: string | null): boolean {
  return role === "avocat" || role === "admin_cabinet";
}

export function roleLabel(role?: string | null, locale: "ar" | "fr" = "fr"): string {
  if (!role) return "";
  if (locale === "ar") return ROLE_LABELS_AR[role] || ROLE_LABELS[role] || role;
  return ROLE_LABELS[role] || role;
}
