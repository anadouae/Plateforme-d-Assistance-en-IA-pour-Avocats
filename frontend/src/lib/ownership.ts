/** Qui peut supprimer un dossier / une pièce — créateur uniquement. */

export function canDeleteCase(opts: {
  role?: string | null;
  userId?: string | null;
  responsibleId?: string | null;
}): boolean {
  if (opts.role === "assistant_juridique") return false;
  if (opts.responsibleId) return opts.userId === opts.responsibleId;
  return opts.role === "admin_cabinet";
}

export function canDeleteDocument(opts: {
  role?: string | null;
  userId?: string | null;
  uploadedBy?: string | null;
}): boolean {
  if (!opts.userId) return false;
  if (opts.uploadedBy) return opts.userId === opts.uploadedBy;
  // Anciennes pièces sans uploaded_by : avocat / admin seulement
  return opts.role === "avocat" || opts.role === "admin_cabinet";
}

export { looksLikeGibberish } from "@/lib/dictation-quality";
