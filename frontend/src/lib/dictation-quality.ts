/** Détecte un texte qui n’est PAS corrigeable (pur clavier) — pas les fautes à approximer. */

/** Pur clavier / ponctuation — les fautes arabes passent à ChatGPT. */
export function looksLikeArabicNonsense(text: string): boolean {
  const t = (text || "").trim();
  if (!t || !/[\u0600-\u06FF]/.test(t)) return false;

  const words = t
    .split(/\s+/)
    .map((w) =>
      w
        .replace(/[\u064B-\u065F\u0670\u0640]/g, "")
        .replace(/[أإآٱ]/g, "ا")
        .replace(/ة/g, "ه")
        .replace(/ى/g, "ي")
        .replace(/^[^\u0600-\u06FF]+|[^\u0600-\u06FF]+$/g, ""),
    )
    .filter((w) => w.length >= 2);

  // Lettres isolées seulement (« ك ك ك »)
  if (words.length === 0) {
    const singles = t.split(/\s+/).filter((w) => /[\u0600-\u06FF]/.test(w));
    return singles.length >= 3 && singles.every((w) => w.replace(/[^\u0600-\u06FF]/g, "").length <= 1);
  }

  const compact = t.replace(/\s+/g, "");
  // Même lettre répétée
  if (/(.)\1{4,}/u.test(compact)) return true;

  return false;
}

export function looksLikeGibberish(text: string): boolean {
  const t = (text || "").trim();
  if (!t) return false;

  const compact = t.replace(/\s+/g, "");
  const letters = t.replace(/[^\p{L}\p{N}]/gu, "");
  const words = t.split(/\s+/).filter((w) => w.replace(/[^\p{L}\p{N}]/gu, "").length >= 2);
  const hasArabic = /[\u0600-\u06FF]/.test(t);
  const lower = t.toLowerCase();

  if (/^[\p{P}\p{S}\s;:_=+\-]+$/u.test(t)) return true;

  if (
    /(?:asdf|qwer|azerty|qwerty|zxcv|hjkl|1234|aaaa|bbbb|xxxx|zzzz|ffff|dddd)/i.test(lower) &&
    words.length < 6
  ) {
    return true;
  }
  if (/(.)\1{4,}/.test(compact) && words.length < 5) return true;

  // Latin mash sans voyelles
  if (!hasArabic && words.length <= 1 && letters.length > 0 && letters.length < 8) {
    return true;
  }
  if (!hasArabic && letters.length >= 4) {
    const vowels = (t.match(/[aeiouyàâäéèêëïîôùûüœæ]/gi) || []).length;
    if (vowels === 0 && words.length < 4) return true;
  }
  if (!hasArabic && words.length >= 2 && words.length <= 8) {
    const tiny = words.filter((w) => w.replace(/[^\p{L}]/gu, "").length <= 2).length;
    if (tiny / words.length >= 0.7 && letters.length < 28) return true;
  }

  // Arabe : seulement charabia irrécupérable (pas les fautes)
  if (hasArabic && looksLikeArabicNonsense(t)) return true;

  return false;
}

/** Y a-t-il assez de « faits » pour lancer une rédaction IA (pas juste une salutation). */
export function hasCheckableFacts(text: string): boolean {
  const t = (text || "").trim();
  if (t.length < 40) return false;
  if (/[\u0600-\u06FF]/.test(t)) {
    const words = t.split(/\s+/).filter((w) => /[\u0600-\u06FF]{2,}/.test(w));
    return words.length >= 8;
  }
  return t.split(/\s+/).filter((w) => w.length >= 3).length >= 10;
}
