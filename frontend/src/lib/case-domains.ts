/** Domaines juridiques pour classement / filtre des dossiers (suivi PFA). */

export const CASE_DOMAINS = [
  "Civil",
  "Pénal",
  "Commercial",
  "Administratif",
  "Famille",
  "Travail",
  "Immobilier",
  "Fiscal",
  "Banque & crédit",
  "Autre",
] as const;

export type CaseDomain = (typeof CASE_DOMAINS)[number];

export function isKnownDomain(value: string): boolean {
  return (CASE_DOMAINS as readonly string[]).includes(value);
}
