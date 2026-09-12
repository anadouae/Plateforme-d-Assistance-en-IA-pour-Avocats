/**
 * Dossier judiciaire vivant — statuts procédure, décisions, délais de recours.
 * Les délais sont indicatifs CPC ; la date de notification réelle prime.
 */

export const PROCEDURE_STATUSES = [
  { value: "ouverture", fr: "Ouverture / dépôt", ar: "افتتاح / إيداع" },
  { value: "instruction", fr: "Instruction", ar: "تحقيق" },
  { value: "audience", fr: "Audience fixée", ar: "جلسة محددةرة" },
  { value: "delibere", fr: "Mise en délibéré", ar: "مداولة" },
  { value: "jugement", fr: "Jugement rendu", ar: "حكم صادر" },
  { value: "notification", fr: "Notification", ar: "تبليغ" },
  { value: "appel_forme", fr: "Appel formé", ar: "استئناف مرفوع" },
  { value: "execution", fr: "Exécution", ar: "تنفيذ" },
  { value: "clos", fr: "Clos", ar: "مغلق" },
] as const;

export const DECISION_TYPES = [
  { value: "jugement", fr: "Jugement", ar: "حكم" },
  { value: "ordonnance", fr: "Ordonnance", ar: "أمر" },
  { value: "arret", fr: "Arrêt", ar: "قرار" },
  { value: "autre", fr: "Autre décision", ar: "قرار آخر" },
] as const;

export const EXHIBIT_TYPES = [
  { value: "contrat", fr: "Contrat", ar: "عقد" },
  { value: "acte", fr: "Acte / titre", ar: "رسم / سند" },
  { value: "pv", fr: "PV / procès-verbal", ar: "محضر" },
  { value: "jugement", fr: "Jugement adverse", ar: "حكم الخصم" },
  { value: "piece_identite", fr: "Pièce d’identité", ar: "وثيقة هوية" },
  { value: "correspondance", fr: "Correspondance", ar: "مراسلة" },
  { value: "expertise", fr: "Expertise", ar: "خبرة" },
  { value: "autre", fr: "Autre", ar: "أخرى" },
] as const;

export const PRODUCED_BY = [
  { value: "client", fr: "Notre client", ar: "موكلنا" },
  { value: "adverse", fr: "Partie adverse", ar: "الخصم" },
  { value: "tribunal", fr: "Tribunal / greffe", ar: "المحكمة / كتابة الضبط" },
  { value: "tiers", fr: "Tiers", ar: "طرف ثالث" },
] as const;

export const EXHIBIT_VERSIONS = [
  { value: "original", fr: "Original", ar: "أصل" },
  { value: "copie", fr: "Copie", ar: "نسخة" },
  { value: "traduction", fr: "Traduction", ar: "ترجمة" },
] as const;

/** Délai indicatif (jours) selon degré — à partir de la notification. */
export function defaultAppealDays(degree?: string | null): number {
  if (degree === "refere") return 15;
  if (degree === "appel") return 30;
  if (degree === "cassation") return 30;
  return 30;
}

export function computeAppealDeadline(
  notificationIso: string | Date | null | undefined,
  days: number,
): Date | null {
  if (!notificationIso) return null;
  const d = typeof notificationIso === "string" ? new Date(notificationIso) : notificationIso;
  if (Number.isNaN(d.getTime())) return null;
  const out = new Date(d.getTime());
  out.setDate(out.getDate() + Math.max(1, days));
  return out;
}

export function appealDeadlineLabel(
  deadline: Date | null,
  ar: boolean,
): { text: string; urgent: boolean } | null {
  if (!deadline) return null;
  const now = Date.now();
  const ms = deadline.getTime() - now;
  const daysLeft = Math.ceil(ms / 86400000);
  const dateStr = deadline.toLocaleDateString(ar ? "ar-MA" : "fr-FR");
  if (daysLeft < 0) {
    return {
      text: ar ? `انتهى أجل الطعن (${dateStr})` : `Délai de recours expiré (${dateStr})`,
      urgent: true,
    };
  }
  if (daysLeft <= 7) {
    return {
      text: ar
        ? `أجل الطعن: ${dateStr} — متبقي ${daysLeft} يوم`
        : `Délai de recours : ${dateStr} — ${daysLeft} j restants`,
      urgent: true,
    };
  }
  return {
    text: ar ? `أجل الطعن الإرشادي: ${dateStr}` : `Délai de recours indicatif : ${dateStr}`,
    urgent: false,
  };
}

export const AGENDA_EVENT_TYPES = [
  { value: "audience", fr: "Audience", ar: "جلسة" },
  { value: "notification", fr: "Notification", ar: "تبليغ" },
  { value: "recours", fr: "Délai de recours", ar: "أجل طعن" },
  { value: "expertise", fr: "Expertise", ar: "خبرة" },
  { value: "mediation", fr: "Médiation", ar: "وساطة" },
  { value: "deadline", fr: "Délai", ar: "أجل" },
  { value: "rdv", fr: "Rendez-vous", ar: "موعد" },
  { value: "other", fr: "Autre", ar: "آخر" },
] as const;
