import type { Locale } from "@/lib/i18n/translations";
import { getTranslations } from "@/lib/i18n/translations";
import { CASE_DOMAINS, normalizeCaseDomain } from "@/lib/case-domains";

/** Statuts canoniques stockés en FR en BDD. */
export const CASE_STATUSES = ["En cours", "Urgent", "Clôturé"] as const;
export type CaseStatus = (typeof CASE_STATUSES)[number];

const STATUS_ALIASES: Record<string, CaseStatus> = {
  "En cours": "En cours",
  Ouvert: "En cours",
  Open: "En cours",
  "قيد المعالجة": "En cours",
  "قيد التنفيذ": "En cours",
  Urgent: "Urgent",
  "عاجل": "Urgent",
  "Clôturé": "Clôturé",
  Cloture: "Clôturé",
  Closed: "Clôturé",
  "مغلق": "Clôturé",
};

export function normalizeCaseStatus(value: string): string {
  const v = (value || "").trim();
  if (!v) return "En cours";
  if (STATUS_ALIASES[v]) return STATUS_ALIASES[v];
  const lower = v.toLowerCase();
  const hit = Object.entries(STATUS_ALIASES).find(([k]) => k.toLowerCase() === lower);
  return hit ? hit[1] : v;
}

/** Statuts stockés en FR en BDD — libellés UI selon la locale. */
export function caseStatusLabel(status: string, locale: Locale): string {
  const t = getTranslations(locale).app.cases;
  const canonical = normalizeCaseStatus(status);
  const map: Record<string, string> = {
    "En cours": t.statusEnCours,
    Urgent: t.statusUrgent,
    "Clôturé": t.statusCloture,
  };
  return map[canonical] || canonical;
}

export function caseStatusOptions(locale: Locale): { value: string; label: string }[] {
  return CASE_STATUSES.map((s) => ({ value: s, label: caseStatusLabel(s, locale) }));
}

const DOMAIN_AR: Record<string, string> = {
  Civil: "مدني",
  Pénal: "جنائي",
  Commercial: "تجاري",
  Administratif: "إداري",
  Famille: "أسرة",
  Travail: "شغل",
  Immobilier: "عقاري",
  Fiscal: "ضريبي",
  "Banque & crédit": "بنك وائتمان",
  Autre: "أخرى",
};

/** Domaines juridiques — valeurs FR en BDD, labels UI bilingues. */
export function caseDomainLabel(domain: string, locale: Locale): string {
  const canonical = normalizeCaseDomain(domain);
  if (locale === "ar") return DOMAIN_AR[canonical] || canonical;
  return canonical;
}

export function caseDomainOptions(
  locale: Locale,
  extras: string[] = [],
): { value: string; label: string }[] {
  const seen = new Set<string>();
  const out: { value: string; label: string }[] = [];
  for (const d of [...CASE_DOMAINS.filter((x) => x !== "Autre"), ...extras]) {
    const n = normalizeCaseDomain(d);
    if (!n || n === "Autre" || seen.has(n.toLowerCase())) continue;
    seen.add(n.toLowerCase());
    out.push({ value: n, label: caseDomainLabel(n, locale) });
  }
  return out;
}

/** Libellé espace de travail selon le rôle connecté. */
export function workspaceRoleLabel(role: string | undefined, locale: Locale): string {
  const fr = locale === "fr";
  switch (role) {
    case "admin_cabinet":
      return fr ? "Workspace avocat admin" : "مساحة محامٍ — مدير";
    case "avocat":
      return fr ? "Espace avocat" : "مساحة محامٍ";
    case "assistant_juridique":
      return fr ? "Espace assistant" : "مساحة مساعد";
    case "admin_webvoice":
      return fr ? "Espace administrateur LexHub" : "مساحة إدارة LexHub";
    default:
      return fr ? "Espace cabinet" : "مساحة المكتب";
  }
}
