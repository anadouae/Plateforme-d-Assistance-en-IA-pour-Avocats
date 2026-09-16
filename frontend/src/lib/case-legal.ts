/** Qualité juridique (art. 32 CPC) — pas le rôle demandeur/défendeur. */
export const QUALITY_OPTIONS = [
  {
    value: "personne_physique",
    fr: "Personne physique (un individu)",
    ar: "شخص طبيعي (فرد)",
    hintFr: "Un être humain : M. X, Mme Y…",
    hintAr: "إنسان: السيد… السيدة…",
  },
  {
    value: "personne_morale",
    fr: "Personne morale (société, association…)",
    ar: "شخص معنوي (شركة، جمعية…)",
    hintFr: "Une société, SARL, association, banque…",
    hintAr: "شركة، جمعية، بنك…",
  },
  {
    value: "administration",
    fr: "Administration / État",
    ar: "إدارة / الدولة",
    hintFr: "Ministère, commune, établissement public…",
    hintAr: "وزارة، جماعة، مؤسسة عمومية…",
  },
] as const;

/** Explications courtes pour l’avocat (pas du jargon opaque). */
export function roleHelp(uiFr: boolean): { demandeur: string; defendeur: string } {
  return uiFr
    ? {
        demandeur:
          "Demandeur = celui qui a saisi le tribunal (votre client attaque / demande quelque chose).",
        defendeur:
          "Défendeur = celui contre qui on agit (votre client se défend face à une demande).",
      }
    : {
        demandeur: "المدعي = من رفع الدعوى أمام المحكمة.",
        defendeur: "المدعى عليه = من رُفعت الدعوى ضده.",
      };
}

export function qualityHelp(uiFr: boolean): string {
  // Conservé pour compat ; l’UI atelier n’affiche plus ce jargon.
  return uiFr
    ? "Nature : individu, société ou administration."
    : "الطبيعة: فرد، شركة أو إدارة.";
}

/** Domaine de plaidoirie dérivé de la matière du dossier (source de vérité). */
export function caseTypeToPleaTemplate(caseType?: string | null): string | null {
  const t = (caseType || "").toLowerCase();
  if (!t.trim()) return null;
  if (t.includes("famille") || t.includes("أسرة") || t.includes("اسرة")) return "famille";
  if (
    t.includes("pénal") ||
    t.includes("penal") ||
    t.includes("زجر") ||
    t.includes("جنائ") ||
    t.includes("circulation") ||
    t.includes("سير")
  ) {
    return "penal-defense";
  }
  if (t.includes("commercial") || t.includes("تجار") || t.includes("banque") || t.includes("بنكي")) {
    return "commercial";
  }
  if (t.includes("admin") || t.includes("إدار") || t.includes("ادار") || t.includes("fiscal") || t.includes("جبائ")) {
    return "administratif";
  }
  if (t.includes("travail") || t.includes("social") || t.includes("شغل") || t.includes("اجتماع")) {
    return "social-travail";
  }
  if (t.includes("foncier") || t.includes("عقار")) return "foncier";
  if (t.includes("civil") || t.includes("مدن")) return "civil-general";
  return null;
}

export const JURISDICTION_DEGREES = [
  { value: "premiere_instance", fr: "Première instance", ar: "ابتدائي" },
  { value: "appel", fr: "Appel", ar: "استئناف" },
  { value: "cassation", fr: "Cassation", ar: "نقض" },
  { value: "refere", fr: "Référé (urgence)", ar: "استعجالي" },
] as const;

export type JurisdictionDegree = (typeof JURISDICTION_DEGREES)[number]["value"];

export const TRIBUNAL_OPTIONS = [
  { value: "tpi", fr: "Tribunal de première instance", ar: "المحكمة الابتدائية" },
  { value: "commerce", fr: "Tribunal de commerce", ar: "المحكمة التجارية" },
  { value: "admin", fr: "Tribunal administratif", ar: "المحكمة الإدارية" },
  { value: "social", fr: "Tribunal social", ar: "المحكمة الاجتماعية" },
  { value: "appel", fr: "Cour d’appel", ar: "محكمة الاستئناف" },
  { value: "cassation", fr: "Cour de cassation", ar: "محكمة النقض" },
] as const;

export type TribunalCode = (typeof TRIBUNAL_OPTIONS)[number]["value"];

export const ACT_TYPES = [
  {
    value: "requete",
    fr: "Requête introductive d’instance",
    ar: "مقال افتتاحي",
    templateHint: "civil-general",
  },
  {
    value: "replique",
    fr: "Mémoire en réponse / réplique",
    ar: "مذكرة جواب / رد",
    templateHint: "civil-defense",
  },
  {
    value: "plaidoirie_orale",
    fr: "Plaidoirie orale (audience)",
    ar: "مرافعة شفوية",
    templateHint: "civil-general",
  },
  {
    value: "conclusions",
    fr: "Conclusions écrites",
    ar: "مستنتجات كتابية",
    templateHint: "civil-general",
  },
  {
    value: "appel",
    fr: "Mémoire d’appel",
    ar: "مذكرة استئناف",
    templateHint: "appel",
  },
  {
    value: "cassation",
    fr: "Pourvoi en cassation",
    ar: "طعن بالنقض",
    templateHint: "cassation",
  },
] as const;

export type ActType = (typeof ACT_TYPES)[number]["value"];

/** Rôles canoniques stockés en base. */
export const CLIENT_ROLES = [
  "demandeur",
  "defendeur",
  "partie_civile",
  "prevenu",
  "requerant",
  "salarie",
  "employeur",
] as const;

export type ClientRole = (typeof CLIENT_ROLES)[number];

export function suggestTribunal(caseType: string, degree: string): TribunalCode {
  const t = (caseType || "").toLowerCase();
  if (degree === "appel") return "appel";
  if (degree === "cassation") return "cassation";
  if (t.includes("commercial") || t.includes("تجار") || t.includes("société") || t.includes("banque"))
    return "commerce";
  if (t.includes("admin") || t.includes("إدار") || t.includes("fiscal") || t.includes("جبائ"))
    return "admin";
  if (t.includes("travail") || t.includes("social") || t.includes("شغل") || t.includes("اجتماع"))
    return "social";
  return "tpi";
}

export function partyRoleOptions(caseType: string): { value: ClientRole; fr: string; ar: string }[] {
  const t = (caseType || "").toLowerCase();
  if (t.includes("pénal") || t.includes("penal") || t.includes("زجر") || t.includes("جنائ") || t.includes("circulation") || t.includes("سير") || t.includes("détenu") || t.includes("معتقل")) {
    return [
      { value: "partie_civile", fr: "Partie civile (victime)", ar: "طرف مدني (ضحية)" },
      { value: "prevenu", fr: "Prévenu / accusé", ar: "متهم" },
    ];
  }
  if (t.includes("admin") || t.includes("إدار") || t.includes("fiscal") || t.includes("جبائ")) {
    return [
      { value: "requerant", fr: "Requérant", ar: "طالب" },
      { value: "defendeur", fr: "Partie défenderesse (administration)", ar: "المدعى عليه (إدارة)" },
    ];
  }
  if (t.includes("travail") || t.includes("social") || t.includes("شغل")) {
    return [
      { value: "salarie", fr: "Salarié demandeur", ar: "أجير طالب" },
      { value: "employeur", fr: "Employeur défendeur", ar: "مشغّل مدعى عليه" },
    ];
  }
  return [
    { value: "demandeur", fr: "Demandeur", ar: "مدعي" },
    { value: "defendeur", fr: "Défendeur", ar: "مدعى عليه" },
  ];
}

export function opposingRoleFor(clientRole: string): ClientRole {
  const map: Record<string, ClientRole> = {
    demandeur: "defendeur",
    defendeur: "demandeur",
    partie_civile: "prevenu",
    prevenu: "partie_civile",
    requerant: "defendeur",
    salarie: "employeur",
    employeur: "salarie",
  };
  return map[clientRole] || "defendeur";
}

/** Délais indicatifs — jamais un calcul juridique engageant. */
export function indicativeDeadlineHint(degree: string, uiFr: boolean): string {
  if (degree === "refere") {
    return uiFr
      ? "Délai indicatif souvent 15 jours en référé (à vérifier selon le litige et la notification réelle)."
      : "أجل إرشادي غالباً 15 يوماً في الاستعجالي (يُتحقق حسب طبيعة النزاع وتاريخ التبليغ).";
  }
  if (degree === "appel") {
    return uiFr
      ? "Délai indicatif souvent 30 jours en appel civil ordinaire (à vérifier selon le litige et la notification réelle)."
      : "أجل إرشادي غالباً 30 يوماً في الاستئناف المدني العادي (يُتحقق حسب النزاع وتاريخ التبليغ).";
  }
  return uiFr
    ? "Les délais de recours varient selon la procédure — vérifiez toujours la notification réelle."
    : "آجال الطعن تختلف حسب المسطرة — تحققوا دائماً من تاريخ التبليغ الفعلي.";
}

export type CaseLegalFields = {
  jurisdiction_degree?: string | null;
  tribunal?: string | null;
  client_role?: string | null;
  client_quality?: string | null;
  client_domicile?: string | null;
  opposing_name?: string | null;
  opposing_role?: string | null;
  opposing_quality?: string | null;
  opposing_domicile?: string | null;
};

export function missingLegalFields(c: CaseLegalFields & { case_type?: string; client_name?: string }): string[] {
  const missing: string[] = [];
  if (!c.case_type?.trim()) missing.push("matière");
  if (!c.jurisdiction_degree?.trim()) missing.push("degré de juridiction");
  if (!c.client_name?.trim()) missing.push("identité du client");
  if (!c.client_role?.trim()) missing.push("rôle des parties");
  return missing;
}

export function actTypeToTemplate(act: string, caseType?: string): string {
  // Voies de recours : l’acte prime sur le domaine
  if (act === "appel") return "appel";
  if (act === "cassation") return "cassation";
  // Sinon : le domaine du dossier fixe le modèle (commercial → commercial, etc.)
  const fromCase = caseTypeToPleaTemplate(caseType);
  if (fromCase) {
    if (act === "replique" && fromCase === "civil-general") return "civil-defense";
    return fromCase;
  }
  if (act === "replique") return "civil-defense";
  const hit = ACT_TYPES.find((a) => a.value === act);
  return hit?.templateHint || "civil-general";
}

export function roleToBriefPosture(role?: string | null): string {
  if (!role) return "demandeur";
  if (role === "defendeur" || role === "employeur") return "defendeur";
  if (role === "partie_civile") return "partie-civile";
  if (role === "prevenu") return "defendeur";
  return "demandeur";
}

export function degreeToBriefJurisdiction(degree?: string | null, tribunal?: string | null): string {
  if (degree === "appel") return "appel";
  if (degree === "cassation") return "cassation";
  if (tribunal === "commerce") return "commerce";
  if (tribunal === "admin") return "admin";
  return "tpi";
}
