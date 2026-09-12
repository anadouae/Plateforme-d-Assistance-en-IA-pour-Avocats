/** Détecte un texte qui n’est pas une dictée utilisable (touches au hasard, ponctuation, etc.). */

export function looksLikeGibberish(text: string): boolean {
  const t = (text || "").trim();
  if (!t) return false;

  const compact = t.replace(/\s+/g, "");
  const letters = t.replace(/[^\p{L}\p{N}]/gu, "");
  const words = t.split(/\s+/).filter((w) => w.replace(/[^\p{L}\p{N}]/gu, "").length >= 2);
  const hasArabic = /[\u0600-\u06FF]/.test(t);

  if (/^[\p{P}\p{S}\s;:_=+\-]+$/u.test(t)) return true;
  if (words.length < 2 && compact.length >= 3) return true;
  if (compact.length >= 4) {
    const ratio = letters.length / compact.length;
    if (ratio < 0.45 && words.length < 3) return true;
  }
  if (letters.length >= 4 && new Set(letters.toLowerCase()).size <= 2 && words.length < 3) {
    return true;
  }
  if (!hasArabic && words.length <= 1 && letters.length > 0 && letters.length < 8) {
    return true;
  }
  if (!hasArabic && letters.length >= 4) {
    const vowels = (t.match(/[aeiouyàâäéèêëïîôùûüœæ]/gi) || []).length;
    if (vowels === 0 && words.length < 4) return true;
  }
  return false;
}
