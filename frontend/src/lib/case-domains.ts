/** Domaines juridiques marocains — alignés cabinets + classificateurs type Marsad (adapté MA). */

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
  "Circulation",
  "Détention",
  "Social",
  "Autre",
] as const;

export type CaseDomain = (typeof CASE_DOMAINS)[number];

export const PRESET_CASE_DOMAINS = CASE_DOMAINS.filter((d) => d !== "Autre");

/** Libellés FR + AR pour filtres UI (plaidoirie / dossiers). */
export const CASE_DOMAIN_META: Record<
  Exclude<CaseDomain, "Autre">,
  { fr: string; ar: string; hintFr: string }
> = {
  Civil: { fr: "Civil", ar: "مدني", hintFr: "Contrats, responsabilité, obligations" },
  Pénal: { fr: "Pénal", ar: "زجري / جنائي", hintFr: "Crimes, délits, contravention" },
  Commercial: { fr: "Commercial", ar: "تجاري", hintFr: "Sociétés, fonds de commerce, recouvrement" },
  Administratif: { fr: "Administratif", ar: "إداري", hintFr: "Annulation, responsabilité admin." },
  Famille: { fr: "Famille", ar: "أسرة", hintFr: "Divorce, pension, garde (Moudawana)" },
  Travail: { fr: "Social / travail", ar: "شغل", hintFr: "Licenciement, salaires, CNSS" },
  Immobilier: { fr: "Immobilier", ar: "عقاري", hintFr: "Propriété, possession, conservation foncière" },
  Fiscal: { fr: "Fiscal", ar: "جبائي", hintFr: "Impôts, redressement, contentieux fiscal" },
  "Banque & crédit": { fr: "Banque & crédit", ar: "بنكي وائتمان", hintFr: "Crédit, garanties, contentieux bancaire" },
  Circulation: { fr: "Délit de circulation", ar: "حوادث السير", hintFr: "Code de la route, accidents" },
  Détention: { fr: "Détenus", ar: "معتقلون", hintFr: "Détention, mise en liberté, exécution peines" },
  Social: { fr: "Social", ar: "اجتماعي", hintFr: "Sécurité sociale, prestations" },
};

export function isKnownDomain(value: string): boolean {
  return (CASE_DOMAINS as readonly string[]).includes(value);
}

/** Anciennes valeurs de type → domaine canonique. */
const DOMAIN_ALIASES: Record<string, string> = {
  "Bail commercial": "Commercial",
  "Droit commercial": "Commercial",
  Recouvrement: "Commercial",
  "Droit du travail": "Travail",
  "Social/travail": "Travail",
  "Social / travail": "Travail",
  "Délit de circulation": "Circulation",
  "Délit ordinaire": "Pénal",
  Détenus: "Détention",
  Detenus: "Détention",
  Immobilier: "Immobilier",
  Foncier: "Immobilier",
  civil: "Civil",
  penal: "Pénal",
  pénal: "Pénal",
  commercial: "Commercial",
  administratif: "Administratif",
  famille: "Famille",
  fiscal: "Fiscal",
};

export function sanitizeCustomDomain(value: string): string {
  return value.replace(/\s+/g, " ").trim().slice(0, 100);
}

export function normalizeCaseDomain(value: string): string {
  const v = sanitizeCustomDomain(value);
  if (isKnownDomain(v)) return v;
  if (DOMAIN_ALIASES[v]) return DOMAIN_ALIASES[v];
  const lower = v.toLowerCase();
  const hit = CASE_DOMAINS.find((d) => d.toLowerCase() === lower);
  if (hit) return hit;
  const metaHit = Object.entries(CASE_DOMAIN_META).find(
    ([, m]) => m.fr.toLowerCase() === lower || m.ar === v,
  );
  return metaHit ? metaHit[0] : v;
}

/** Types déjà utilisés au cabinet (hors liste de base) — ils s’ajoutent aux filtres. */
export function customDomainsFromCases(caseTypes: string[]): string[] {
  const extras = new Set<string>();
  for (const raw of caseTypes) {
    const n = normalizeCaseDomain(raw);
    if (n && n !== "Autre" && !isKnownDomain(n)) extras.add(n);
  }
  return [...extras].sort((a, b) => a.localeCompare(b, "fr", { sensitivity: "base" }));
}

export function filterDomainValues(caseTypes: string[]): string[] {
  const extras = customDomainsFromCases(caseTypes);
  const hasAutre = caseTypes.some((t) => normalizeCaseDomain(t) === "Autre");
  return [...PRESET_CASE_DOMAINS, ...extras, ...(hasAutre ? ["Autre"] : [])];
}
