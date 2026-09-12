/**
 * Carte judiciaire Maroc (indicative) — villes + sièges.
 * Sources : décret carte judiciaire 2023/2024 (108 TPI, 33 CA, 10 TC, 10 TA).
 * La compétence exacte reste à vérifier par l’avocat.
 */

export type CourtKind =
  | "tpi"
  | "commerce"
  | "admin"
  | "social"
  | "appel"
  | "appel_commerce"
  | "appel_admin"
  | "cassation";

export type MoroccoCity = {
  value: string;
  fr: string;
  ar: string;
};

export type CourtSeat = {
  id: string;
  city: string;
  kind: CourtKind;
  fr: string;
  ar: string;
};

export const MOROCCO_CITIES: MoroccoCity[] = [
  { value: "agadir", fr: "Agadir", ar: "أكادير" },
  { value: "al_hoceima", fr: "Al Hoceima", ar: "الحسيمة" },
  { value: "beni_mellal", fr: "Beni Mellal", ar: "بني ملال" },
  { value: "berkane", fr: "Berkane", ar: "بركان" },
  { value: "berrechid", fr: "Berrechid", ar: "برشيد" },
  { value: "casablanca", fr: "Casablanca", ar: "الدار البيضاء" },
  { value: "dakhla", fr: "Dakhla", ar: "الداخلة" },
  { value: "el_jadida", fr: "El Jadida", ar: "الجديدة" },
  { value: "errachidia", fr: "Errachidia", ar: "الرشيدية" },
  { value: "essaouira", fr: "Essaouira", ar: "الصويرة" },
  { value: "fes", fr: "Fès", ar: "فاس" },
  { value: "guelmim", fr: "Guelmim", ar: "كلميم" },
  { value: "kenitra", fr: "Kénitra", ar: "القنيطرة" },
  { value: "khemisset", fr: "Khemisset", ar: "الخميسات" },
  { value: "khouribga", fr: "Khouribga", ar: "خريبكة" },
  { value: "ksar_el_kebir", fr: "Ksar El Kébir", ar: "القصر الكبير" },
  { value: "laayoune", fr: "Laâyoune", ar: "العيون" },
  { value: "larache", fr: "Larache", ar: "العرائش" },
  { value: "marrakech", fr: "Marrakech", ar: "مراكش" },
  { value: "meknes", fr: "Meknès", ar: "مكناس" },
  { value: "mohammedia", fr: "Mohammedia", ar: "المحمدية" },
  { value: "nador", fr: "Nador", ar: "الناظور" },
  { value: "ouarzazate", fr: "Ouarzazate", ar: "ورزازات" },
  { value: "oujda", fr: "Oujda", ar: "وجدة" },
  { value: "rabat", fr: "Rabat", ar: "الرباط" },
  { value: "safi", fr: "Safi", ar: "آسفي" },
  { value: "sale", fr: "Salé", ar: "سلا" },
  { value: "settat", fr: "Settat", ar: "سطات" },
  { value: "sidi_kacem", fr: "Sidi Kacem", ar: "سيدي قاسم" },
  { value: "tanger", fr: "Tanger", ar: "طنجة" },
  { value: "tan_tan", fr: "Tan-Tan", ar: "طانطان" },
  { value: "taourirt", fr: "Taourirt", ar: "تاوريرت" },
  { value: "taroudant", fr: "Taroudant", ar: "تارودانت" },
  { value: "taza", fr: "Taza", ar: "تازة" },
  { value: "temara", fr: "Témara", ar: "تمارة" },
  { value: "tetouan", fr: "Tétouan", ar: "تطوان" },
  { value: "tiznit", fr: "Tiznit", ar: "تيزنيت" },
];

function seat(city: string, kind: CourtKind, fr: string, ar: string): CourtSeat {
  return { id: `${city}-${kind}`, city, kind, fr, ar };
}

/** Sièges principaux (TPI ville + spécialisés régionaux + CA). */
export const MOROCCO_COURT_SEATS: CourtSeat[] = [
  // Casablanca
  seat("casablanca", "tpi", "Tribunal de première instance de Casablanca", "المحكمة الابتدائية بالدار البيضاء"),
  seat("casablanca", "social", "Tribunal social de Casablanca", "المحكمة الاجتماعية بالدار البيضاء"),
  seat("casablanca", "commerce", "Tribunal de commerce de Casablanca", "المحكمة التجارية بالدار البيضاء"),
  seat("casablanca", "admin", "Tribunal administratif de Casablanca", "المحكمة الإدارية بالدار البيضاء"),
  seat("casablanca", "appel", "Cour d’appel de Casablanca", "محكمة الاستئناف بالدار البيضاء"),
  seat("casablanca", "appel_commerce", "Cour d’appel de commerce de Casablanca", "محكمة الاستئناف التجارية بالدار البيضاء"),
  // Rabat
  seat("rabat", "tpi", "Tribunal de première instance de Rabat", "المحكمة الابتدائية بالرباط"),
  seat("rabat", "commerce", "Tribunal de commerce de Rabat", "المحكمة التجارية بالرباط"),
  seat("rabat", "admin", "Tribunal administratif de Rabat", "المحكمة الإدارية بالرباط"),
  seat("rabat", "appel", "Cour d’appel de Rabat", "محكمة الاستئناف بالرباط"),
  seat("rabat", "cassation", "Cour de cassation (Rabat)", "محكمة النقض (الرباط)"),
  // Salé / Témara
  seat("sale", "tpi", "Tribunal de première instance de Salé", "المحكمة الابتدائية بسلا"),
  seat("temara", "tpi", "Tribunal de première instance de Témara", "المحكمة الابتدائية بتمارة"),
  // Fès
  seat("fes", "tpi", "Tribunal de première instance de Fès", "المحكمة الابتدائية بفاس"),
  seat("fes", "commerce", "Tribunal de commerce de Fès", "المحكمة التجارية بفاس"),
  seat("fes", "admin", "Tribunal administratif de Fès", "المحكمة الإدارية بفاس"),
  seat("fes", "appel", "Cour d’appel de Fès", "محكمة الاستئناف بفاس"),
  seat("fes", "appel_commerce", "Cour d’appel de commerce de Fès", "محكمة الاستئناف التجارية بفاس"),
  // Marrakech
  seat("marrakech", "tpi", "Tribunal de première instance de Marrakech", "المحكمة الابتدائية بمراكش"),
  seat("marrakech", "commerce", "Tribunal de commerce de Marrakech", "المحكمة التجارية بمراكش"),
  seat("marrakech", "admin", "Tribunal administratif de Marrakech", "المحكمة الإدارية بمراكش"),
  seat("marrakech", "appel", "Cour d’appel de Marrakech", "محكمة الاستئناف بمراكش"),
  seat("marrakech", "appel_commerce", "Cour d’appel de commerce de Marrakech", "محكمة الاستئناف التجارية بمراكش"),
  // Tanger
  seat("tanger", "tpi", "Tribunal de première instance de Tanger", "المحكمة الابتدائية بطنجة"),
  seat("tanger", "commerce", "Tribunal de commerce de Tanger", "المحكمة التجارية بطنجة"),
  seat("tanger", "admin", "Tribunal administratif de Tanger", "المحكمة الإدارية بطنجة"),
  seat("tanger", "appel", "Cour d’appel de Tanger", "محكمة الاستئناف بطنجة"),
  seat("tanger", "appel_commerce", "Cour d’appel de commerce de Tanger", "محكمة الاستئناف التجارية بطنجة"),
  // Agadir
  seat("agadir", "tpi", "Tribunal de première instance d’Agadir", "المحكمة الابتدائية بأكادير"),
  seat("agadir", "commerce", "Tribunal de commerce d’Agadir", "المحكمة التجارية بأكادير"),
  seat("agadir", "admin", "Tribunal administratif d’Agadir", "المحكمة الإدارية بأكادير"),
  seat("agadir", "appel", "Cour d’appel d’Agadir", "محكمة الاستئناف بأكادير"),
  seat("agadir", "appel_commerce", "Cour d’appel de commerce d’Agadir", "محكمة الاستئناف التجارية بأكادير"),
  // Meknès / Oujda / autres CA
  seat("meknes", "tpi", "Tribunal de première instance de Meknès", "المحكمة الابتدائية بمكناس"),
  seat("meknes", "commerce", "Tribunal de commerce de Meknès", "المحكمة التجارية بمكناس"),
  seat("meknes", "appel", "Cour d’appel de Meknès", "محكمة الاستئناف بمكناس"),
  seat("oujda", "tpi", "Tribunal de première instance d’Oujda", "المحكمة الابتدائية بوجدة"),
  seat("oujda", "commerce", "Tribunal de commerce d’Oujda", "المحكمة التجارية بوجدة"),
  seat("oujda", "appel", "Cour d’appel d’Oujda", "محكمة الاستئناف بوجدة"),
  seat("kenitra", "tpi", "Tribunal de première instance de Kénitra", "المحكمة الابتدائية بالقنيطرة"),
  seat("kenitra", "appel", "Cour d’appel de Kénitra", "محكمة الاستئناف بالقنيطرة"),
  seat("tetouan", "tpi", "Tribunal de première instance de Tétouan", "المحكمة الابتدائية بتطوان"),
  seat("tetouan", "appel", "Cour d’appel de Tétouan", "محكمة الاستئناف بتطوان"),
  seat("nador", "tpi", "Tribunal de première instance de Nador", "المحكمة الابتدائية بالناظور"),
  seat("nador", "appel", "Cour d’appel de Nador", "محكمة الاستئناف بالناظور"),
  seat("al_hoceima", "tpi", "Tribunal de première instance d’Al Hoceima", "المحكمة الابتدائية بالحسيمة"),
  seat("al_hoceima", "appel", "Cour d’appel d’Al Hoceima", "محكمة الاستئناف بالحسيمة"),
  seat("settat", "tpi", "Tribunal de première instance de Settat", "المحكمة الابتدائية بسطات"),
  seat("settat", "appel", "Cour d’appel de Settat", "محكمة الاستئناف بسطات"),
  seat("el_jadida", "tpi", "Tribunal de première instance d’El Jadida", "المحكمة الابتدائية بالجديدة"),
  seat("el_jadida", "appel", "Cour d’appel d’El Jadida", "محكمة الاستئناف بالجديدة"),
  seat("safi", "tpi", "Tribunal de première instance de Safi", "المحكمة الابتدائية بآسفي"),
  seat("safi", "appel", "Cour d’appel de Safi", "محكمة الاستئناف بآسفي"),
  seat("beni_mellal", "tpi", "Tribunal de première instance de Beni Mellal", "المحكمة الابتدائية ببني ملال"),
  seat("beni_mellal", "appel", "Cour d’appel de Beni Mellal", "محكمة الاستئناف ببني ملال"),
  seat("khouribga", "tpi", "Tribunal de première instance de Khouribga", "المحكمة الابتدائية بخريبكة"),
  seat("khouribga", "appel", "Cour d’appel de Khouribga", "محكمة الاستئناف بخريبكة"),
  seat("taza", "tpi", "Tribunal de première instance de Taza", "المحكمة الابتدائية بتازة"),
  seat("taza", "appel", "Cour d’appel de Taza", "محكمة الاستئناف بتازة"),
  seat("ouarzazate", "tpi", "Tribunal de première instance d’Ouarzazate", "المحكمة الابتدائية بورزازات"),
  seat("ouarzazate", "appel", "Cour d’appel d’Ouarzazate", "محكمة الاستئناف بورزازات"),
  seat("errachidia", "tpi", "Tribunal de première instance d’Errachidia", "المحكمة الابتدائية بالرشيدية"),
  seat("errachidia", "appel", "Cour d’appel d’Errachidia", "محكمة الاستئناف بالرشيدية"),
  seat("guelmim", "tpi", "Tribunal de première instance de Guelmim", "المحكمة الابتدائية بكلميم"),
  seat("guelmim", "appel", "Cour d’appel de Guelmim", "محكمة الاستئناف بكلميم"),
  seat("laayoune", "tpi", "Tribunal de première instance de Laâyoune", "المحكمة الابتدائية بالعيون"),
  seat("laayoune", "commerce", "Tribunal de commerce de Laâyoune", "المحكمة التجارية بالعيون"),
  seat("laayoune", "admin", "Tribunal administratif de Laâyoune", "المحكمة الإدارية بالعيون"),
  seat("laayoune", "appel", "Cour d’appel de Laâyoune", "محكمة الاستئناف بالعيون"),
  seat("dakhla", "tpi", "Tribunal de première instance de Dakhla", "المحكمة الابتدائية بالداخلة"),
  seat("dakhla", "appel", "Cour d’appel de Dakhla", "محكمة الاستئناف بالداخلة"),
  // Autres TPI fréquents
  seat("mohammedia", "tpi", "Tribunal de première instance de Mohammedia", "المحكمة الابتدائية بالمحمدية"),
  seat("berrechid", "tpi", "Tribunal de première instance de Berrechid", "المحكمة الابتدائية ببرشيد"),
  seat("khemisset", "tpi", "Tribunal de première instance de Khemisset", "المحكمة الابتدائية بالخميسات"),
  seat("larache", "tpi", "Tribunal de première instance de Larache", "المحكمة الابتدائية بالعرائش"),
  seat("ksar_el_kebir", "tpi", "Tribunal de première instance de Ksar El Kébir", "المحكمة الابتدائية بالقصر الكبير"),
  seat("sidi_kacem", "tpi", "Tribunal de première instance de Sidi Kacem", "المحكمة الابتدائية بسيدي قاسم"),
  seat("berkane", "tpi", "Tribunal de première instance de Berkane", "المحكمة الابتدائية ببركان"),
  seat("taourirt", "tpi", "Tribunal de première instance de Taourirt", "المحكمة الابتدائية بتاوريرت"),
  seat("essaouira", "tpi", "Tribunal de première instance d’Essaouira", "المحكمة الابتدائية بالصويرة"),
  seat("taroudant", "tpi", "Tribunal de première instance de Taroudant", "المحكمة الابتدائية بتارودانت"),
  seat("tiznit", "tpi", "Tribunal de première instance de Tiznit", "المحكمة الابتدائية بتيزنيت"),
  seat("tan_tan", "tpi", "Tribunal de première instance de Tan-Tan", "المحكمة الابتدائية بطانطان"),
];

const KIND_FOR_DEGREE: Record<string, CourtKind[]> = {
  premiere_instance: ["tpi", "commerce", "admin", "social"],
  refere: ["tpi", "commerce", "admin", "social"],
  appel: ["appel", "appel_commerce", "appel_admin"],
  cassation: ["cassation"],
};

export function courtsForCity(
  city: string | null | undefined,
  degree?: string | null,
): CourtSeat[] {
  if (!city) return [];
  const kinds = degree ? KIND_FOR_DEGREE[degree] : null;
  return MOROCCO_COURT_SEATS.filter(
    (s) => s.city === city && (!kinds || kinds.includes(s.kind)),
  );
}

export function courtSeatById(id?: string | null): CourtSeat | undefined {
  if (!id) return undefined;
  return MOROCCO_COURT_SEATS.find((s) => s.id === id);
}

export function cityLabel(value?: string | null, ar = false): string {
  const c = MOROCCO_CITIES.find((x) => x.value === value);
  if (!c) return value || "";
  return ar ? c.ar : c.fr;
}

export function courtSeatLabel(idOrKind?: string | null, ar = false): string {
  const seatHit = courtSeatById(idOrKind);
  if (seatHit) return ar ? seatHit.ar : seatHit.fr;
  return idOrKind || "";
}

/** Compat : anciennes valeurs tpi/commerce → kind générique. */
export function resolveCourtKind(tribunal?: string | null): CourtKind | string {
  const seatHit = courtSeatById(tribunal);
  if (seatHit) return seatHit.kind;
  return tribunal || "tpi";
}
