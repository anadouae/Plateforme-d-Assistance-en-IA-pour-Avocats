/**
 * Transforme un extrait brut (OCR / DOCX) en Markdown lisible
 * pour l'aperçu LexHub (titres, listes, gras) — sans appeler l'IA.
 */

function isMostlyArabic(s: string): boolean {
  const ar = (s.match(/[\u0600-\u06FF]/g) || []).length;
  const lat = (s.match(/[A-Za-z]/g) || []).length;
  return ar > lat;
}

/** Insère des sauts de ligne si l'extrait est un pavé sans structure. */
function normalizeRawExtract(raw: string): string {
  let t = (raw || "").replace(/\r\n/g, "\n").replace(/\u00a0/g, " ").trim();
  if (!t) return "";

  const nl = (t.match(/\n/g) || []).length;
  const isWall = nl < 3 && t.length > 180;

  // Uniquement sur un vrai pavé : ne pas casser les titres DOCX du type « A — B — C »
  if (isWall) {
    // Puces « — » après ponctuation / début
    t = t.replace(/([.؛;:!؟?])\s*[—–•●▪]\s+/g, "$1\n— ");
    t = t.replace(/(^|\n)\s*[—–•●▪]\s+/g, "$1— ");

    const labelStarts =
      "(?:الخبيرة|الخبير|التاريخ|تاريخ التقرير|تاريخ الحادثة|المعني بالأمر|المقاولة|الملاحظات|الخلاصة|الخاتمة|الموضوع|موضوع الخبرة|" +
      "الشاهد|النتائج|الوقائع|الطلبات|المقدمة|استنتاج|شهادة|محضر|عقد|" +
      "Rapport|Expertise|Conclusion|Objet|Résumé|Faits|Demandes|Introduction|Constat|Date|Expert|Employeur|Témoin)";
    t = t.replace(new RegExp(`(?<!^|\\n)\\s*(${labelStarts})\\s*[:：]`, "giu"), "\n$1 :");

    t = t.replace(
      /(?<!^|\n)\s+(الملاحظات|الخلاصة|الخاتمة|النتائج|الوقائع|الطلبات|المقدمة|استنتاج|خلاصة|Conclusion|Faits|Demandes)\b/giu,
      "\n$1",
    );
  }

  t = t.replace(/\n{3,}/g, "\n\n");
  return t.trim();
}

function looksLikeHeading(line: string): boolean {
  const t = line.trim();
  if (!t || t.length > 90) return false;
  if (/^#{1,3}\s/.test(t)) return true;
  // Ne jamais traiter une ligne « clé : valeur » comme titre
  if (/[:：]/.test(t) && looksLikeKv(t)) return false;
  if (
    /^(تقرير|خبرة|خاتمة|ملاحظات|موضوع|الخلاصة|الخاتمة|النتائج|الوقائع|الطلبات|المقدمة|استنتاج|خلاصة|شهادة|محضر|عقد|خبرة طبية|الملاحظات)$/.test(
      t,
    ) ||
    /^(تقرير|خبرة طبية|خاتمة|ملاحظات|الخلاصة|الخاتمة)\b/.test(t)
  ) {
    return true;
  }
  if (
    /^(rapport|expertise|conclusion|objet|résumé|faits|demandes|introduction|constat|contrat)\b/i.test(
      t,
    )
  ) {
    return true;
  }
  // Majuscules latines courtes uniquement (pas d’arabe + CIN)
  const hasArabic = /[\u0600-\u06FF]/.test(t);
  if (
    !hasArabic &&
    t.length < 70 &&
    t === t.toUpperCase() &&
    /[A-ZÀÂÉÈÊËÎÏÔÙÛÜ]{3,}/.test(t)
  ) {
    return true;
  }
  return false;
}

function looksLikeBullet(line: string): boolean {
  return /^[-–—•●▪]\s+/.test(line.trim()) || /^\d+[.)]\s+/.test(line.trim());
}

function looksLikeKv(line: string): { key: string; value: string } | null {
  const t = line.trim();
  const m = t.match(/^(.{2,48}?)\s*[:：]\s*(.{1,})$/);
  if (!m) return null;
  const key = m[1].trim();
  const value = m[2].trim();
  if (!value || key.length > 48) return null;
  if (key.split(/\s+/).length > 8) return null;
  // « الخلاصة: … » long → titre + paragraphe plutôt que puce
  if (/^(الخلاصة|الخاتمة|خلاصة|conclusion)$/i.test(key) && value.length > 80) {
    return null;
  }
  return { key, value };
}

/** Met en gras montants, dates, CIN, e-mails, téléphones, IPP. */
function emphasizeInline(s: string): string {
  let out = s;
  out = out.replace(
    /(\d{1,3}(?:[.\s]\d{3})*(?:[.,]\d+)?\s*(?:درهم|DH|MAD|€|\$|كلغ|كغ|kg))/gi,
    "**$1**",
  );
  out = out.replace(
    /\b(\d{1,2}[\/.\-]\d{1,2}[\/.\-]\d{2,4}|\d{4}[\/.\-]\d{1,2}[\/.\-]\d{1,2})\b/g,
    "**$1**",
  );
  // Dates arabes / FR en clair (15 أبريل 2026, 15 avril 2026)
  out = out.replace(
    /(\d{1,2}\s+(?:يناير|فبراير|مارس|أبريل|ماي|يونيو|يوليوز|غشت|شتنبر|أكتوبر|نونبر|دجنبر|janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})/gi,
    "**$1**",
  );
  out = out.replace(/\b([A-Z]{1,2}\d{5,8})\b/g, "**$1**");
  out = out.replace(/\b(0[5-7]\d{8}|0[5-7][\s.\-]\d{2}(?:[\s.\-]\d{2}){3})\b/g, "**$1**");
  out = out.replace(
    /\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b/g,
    "`$1`",
  );
  out = out.replace(/\b(IPP\s*\d+\s*%|\d+\s*%\s*IPP)\b/gi, "**$1**");
  out = out.replace(/(ثمانية في المائة)/g, "**$1**");
  out = out.replace(/(?<!\*)(\d+\s*٪)(?!\*)/g, "**$1**");
  return out;
}

/**
 * Convertit le texte extrait en Markdown structuré pour l'UI.
 */
export function formatExtractedPreview(raw: string): string {
  const text = normalizeRawExtract(raw);
  if (!text) return "";

  const lines = text.split("\n");
  const out: string[] = [];
  let i = 0;
  let firstTitleDone = false;

  while (i < lines.length) {
    const rawLine = lines[i];
    const line = rawLine.trim();
    if (!line) {
      out.push("");
      i += 1;
      continue;
    }

    // Titre principal = première ligne courte significative
    if (!firstTitleDone && line.length < 120 && !looksLikeKv(line) && !looksLikeBullet(line)) {
      out.push(`## ${line.replace(/^#+\s*/, "")}`);
      firstTitleDone = true;
      i += 1;
      continue;
    }

    if (looksLikeHeading(line)) {
      out.push("");
      out.push(`### ${line.replace(/^#+\s*/, "")}`);
      i += 1;
      continue;
    }

    // الخلاصة: long texte → titre + paragraphe
    const longKv = line.match(/^(الخلاصة|الخاتمة|خلاصة|Conclusion)\s*[:：]\s*(.+)$/i);
    if (longKv && longKv[2].trim().length > 80) {
      out.push("");
      out.push(`### ${longKv[1].trim()}`);
      out.push(emphasizeInline(longKv[2].trim()));
      out.push("");
      i += 1;
      continue;
    }

    const kv = looksLikeKv(line);
    if (kv) {
      out.push(`- **${kv.key}** : ${emphasizeInline(kv.value)}`);
      i += 1;
      continue;
    }

    if (looksLikeBullet(line)) {
      const items: string[] = [];
      while (i < lines.length) {
        const L = lines[i].trim();
        if (!L) {
          i += 1;
          break;
        }
        if (looksLikeBullet(L)) {
          const body = L.replace(/^[-–—•●▪]\s+/, "").replace(/^\d+[.)]\s+/, "");
          items.push(emphasizeInline(body));
          i += 1;
          continue;
        }
        if (/^\s{2,}\S/.test(lines[i]) && items.length) {
          items[items.length - 1] += " " + emphasizeInline(L);
          i += 1;
          continue;
        }
        break;
      }
      items.forEach((it, idx) => {
        out.push(`${idx + 1}. ${it}`);
      });
      out.push("");
      continue;
    }

    const para: string[] = [line];
    i += 1;
    while (i < lines.length) {
      const L = lines[i].trim();
      if (!L) break;
      if (looksLikeHeading(L) || looksLikeBullet(L) || looksLikeKv(L)) break;
      para.push(L);
      i += 1;
    }
    out.push(emphasizeInline(para.join(" ")));
    out.push("");
  }

  let md = out.join("\n").replace(/\n{3,}/g, "\n\n").trim();
  if (!md) return emphasizeInline(text);
  return md;
}

export function previewTextDir(raw: string): "rtl" | "ltr" {
  return isMostlyArabic(raw || "") ? "rtl" : "ltr";
}
