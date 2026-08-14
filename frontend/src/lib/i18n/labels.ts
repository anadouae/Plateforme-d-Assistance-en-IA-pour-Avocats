import type { Locale } from "@/lib/i18n/translations";
import { getTranslations } from "@/lib/i18n/translations";
import { CASE_DOMAINS } from "@/lib/case-domains";

/** Statuts stockés en FR en BDD — libellés UI selon la locale. */
export function caseStatusLabel(status: string, locale: Locale): string {
  const t = getTranslations(locale).app.cases;
  const map: Record<string, string> = {
    "En cours": t.statusEnCours,
    Urgent: t.statusUrgent,
    "Clôturé": t.statusCloture,
  };
  return map[status] || status;
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
  if (locale === "ar") return DOMAIN_AR[domain] || domain;
  return domain;
}

export function caseDomainOptions(locale: Locale): { value: string; label: string }[] {
  return CASE_DOMAINS.map((d) => ({ value: d, label: caseDomainLabel(d, locale) }));
}
