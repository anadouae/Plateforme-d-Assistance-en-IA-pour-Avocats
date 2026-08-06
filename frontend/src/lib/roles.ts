/** Rôles cabinet Sanad — alignés sur le backend UserRole. */

export type CabinetRole =
  | "avocat"
  | "assistant_juridique"
  | "admin_cabinet"
  | "admin_webvoice";

export const ROLE_LABELS: Record<string, string> = {
  avocat: "Avocat",
  assistant_juridique: "Assistant juridique",
  admin_cabinet: "Administrateur cabinet",
  admin_webvoice: "Admin plateforme",
};

export function isAssistant(role?: string | null): boolean {
  return role === "assistant_juridique";
}

export function canUseAI(role?: string | null): boolean {
  return role === "avocat" || role === "admin_cabinet";
}

export function canManageTeam(role?: string | null): boolean {
  return role === "admin_cabinet";
}

export function canUseTemplates(role?: string | null): boolean {
  return role === "avocat" || role === "admin_cabinet";
}

export function roleLabel(role?: string | null): string {
  if (!role) return "";
  return ROLE_LABELS[role] || role;
}
