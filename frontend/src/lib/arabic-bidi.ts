/** RTL / bidi helpers — ponctuation après chiffres/dates (bug classique Unicode). */

const ARABIC_RE = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]/;
const RLM = "\u200F";
const AR_MONTHS =
  "يناير|فبراير|مارس|أبريل|ماي|يونيو|يوليوز|غشت|شتنبر|أكتوبر|نوفمبر|ديسمبر";

/** Classe CSS à mettre sur tout conteneur de texte arabe éditable ou en lecture. */
export const ARABIC_TEXT_CLASS = "arabic-text";

/**
 * Ancre la ponctuation finale après un bloc chiffres/date (ex. « 17 يناير 2025. »).
 * N'altère pas les mots — ajoute seulement des marques Unicode invisibles.
 */
export function fixArabicBidiDisplay(text: string): string {
  if (!text || !ARABIC_RE.test(text)) return text;

  let t = text.replace(/\r\n/g, "\n");

  // Ponctuation orpheline en tête de ligne avant arabe (artefact rare STT/export)
  t = t.replace(/^([.،:؛!?]+)([\u0600-\u06FF])/gm, "$2$1");

  const anchor = (s: string) =>
    s.replace(new RegExp(`([.،:؛!?])(?!${RLM})`, "g"), `$1${RLM}`);

  // 17 يناير 2025.
  t = t.replace(
    new RegExp(
      `(\\d{1,2}\\s+(?:${AR_MONTHS})\\s+\\d{4})([.،:؛!?])(?!${RLM})`,
      "g",
    ),
    `$1$2${RLM}`,
  );

  // 28/02/2025.
  t = t.replace(
    /(\d{1,2}\/\d{1,2}\/\d{4})([.،:؛!?])(?!\u200F)/g,
    `$1$2${RLM}`,
  );

  // Chiffres / milliers + ponctuation en fin de segment
  t = t.replace(/(\d[\d/.,\s]*\d|\d+)([.،:؛!?])(?=\s|$|\n)/g, (m, num, punct) =>
    `${num}${punct}${RLM}`,
  );

  // Point final après lettre arabe (contexte RTL pur — évite le « .النص » visuel)
  t = t.replace(
    /([\u0600-\u06FF])([.،:؛!?])(?=\s|$|\n)(?!\u200F)/g,
    `$1$2${RLM}`,
  );

  return t;
}

export function arabicFieldProps(isFrench: boolean): {
  dir: "rtl" | "ltr";
  className: string;
  lang: string;
} {
  return isFrench
    ? { dir: "ltr", className: "latin-text", lang: "fr" }
    : { dir: "rtl", className: ARABIC_TEXT_CLASS, lang: "ar" };
}

/** HTML sûr pour l’aperçu polish (marqueurs ‹ › STT). */
export function renderArabicPreviewHtml(raw: string): string {
  const t = fixArabicBidiDisplay(raw);
  return t
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/‹([^›]+)›/g, '<mark class="polish-guess" title="STT">$1</mark>');
}
