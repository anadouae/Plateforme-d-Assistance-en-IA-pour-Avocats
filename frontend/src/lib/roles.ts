/** Rôles cabinet Sanad — alignés sur le backend UserRole. */

export type CabinetRole =
  | "avocat"
  | "assistant_juridique"
  | "admin_cabinet"
  | "admin_webvoice";

/** Libellés FR */
export const ROLE_LABELS: Record<string, string> = {
  avocat: "Avocat",
  assistant_juridique: "Stagiaire",
  admin_cabinet: "Gestion",
  admin_webvoice: "Admin plateforme",
};

/** Libellés AR (UI cabinet) */
export const ROLE_LABELS_AR: Record<string, string> = {
  avocat: "محامٍ",
  assistant_juridique: "متدرّج",
  admin_cabinet: "إدارة",
  admin_webvoice: "منصة",
};

/** Rôles assignables à l'approbation d'une demande */
export const ASSIGNABLE_ROLES = [
  { value: "avocat", labelAr: "محامٍ", labelFr: "Avocat" },
  { value: "assistant_juridique", labelAr: "متدرّج", labelFr: "Stagiaire" },
  { value: "admin_cabinet", labelAr: "إدارة", labelFr: "Gestion" },
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

export function roleLabel(role?: string | null, locale: "ar" | "fr" = "ar"): string {
  if (!role) return "";
  if (locale === "ar") return ROLE_LABELS_AR[role] || ROLE_LABELS[role] || role;
  return ROLE_LABELS[role] || role;
}
