/** Persistance locale de l'atelier plaidoirie (retour dossier ↔ rédaction sans perte). */

export const PLEA_SESSION_KEY = "lexhub_plea_session_v1";

export type PleaSessionSnapshot = {
  v: 1;
  templateId: string;
  step: number;
  caseId: string;
  raw: string;
  polished: string;
  docTitle: string;
  docBody: string;
  composeChecks: string[];
  pleaType: string;
  actType: string;
  briefPosture: string;
  briefJurisdiction: string;
  settingsVisited: boolean;
  editingPolished: boolean;
  savedAt: number;
  pendingReturn?: boolean;
};

export function pleaResumeHref(templateId: string): string {
  const id = encodeURIComponent(templateId || "libre");
  return `/redaction/${id}?resume=1`;
}

export function savePleaSession(snap: PleaSessionSnapshot): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(PLEA_SESSION_KEY, JSON.stringify(snap));
  } catch {
    /* quota / private mode */
  }
}

export function loadPleaSession(): PleaSessionSnapshot | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(PLEA_SESSION_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as PleaSessionSnapshot;
    if (!data || data.v !== 1 || !data.templateId) return null;
    return data;
  } catch {
    return null;
  }
}

export function clearPleaSession(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(PLEA_SESSION_KEY);
  } catch {
    /* ignore */
  }
}

export function markPleaPendingReturn(templateId: string): string {
  const cur = loadPleaSession();
  const href = pleaResumeHref(templateId);
  if (cur) {
    savePleaSession({ ...cur, pendingReturn: true, templateId, savedAt: Date.now() });
  } else {
    savePleaSession({
      v: 1,
      templateId,
      step: 0,
      caseId: "",
      raw: "",
      polished: "",
      docTitle: "",
      docBody: "",
      composeChecks: [],
      pleaType: templateId,
      actType: "plaidoirie_orale",
      briefPosture: "demandeur",
      briefJurisdiction: "tpi",
      settingsVisited: false,
      editingPolished: false,
      savedAt: Date.now(),
      pendingReturn: true,
    });
  }
  return href;
}

export function hasActivePleaSessionFor(caseId?: string | null): boolean {
  const s = loadPleaSession();
  if (!s) return false;
  if (caseId && s.caseId !== caseId) return false;
  return Boolean(s.pendingReturn || s.raw.trim() || s.polished.trim() || s.docBody.trim());
}

export function hasActivePleaSession(): boolean {
  return hasActivePleaSessionFor(loadPleaSession()?.caseId);
}

/** Brouillon local assez consistant pour proposer « Reprendre » (pas juste un dossier choisi). */
export function hasMeaningfulPleaSession(): boolean {
  const s = loadPleaSession();
  if (!s) return false;
  return Boolean(s.raw.trim() || s.polished.trim() || s.docBody.trim() || s.pendingReturn);
}

export function pleaSessionPreview(max = 90): string {
  const s = loadPleaSession();
  if (!s) return "";
  const src = (s.raw || s.polished || s.docTitle || "").replace(/\s+/g, " ").trim();
  if (!src) return "";
  return src.length > max ? `${src.slice(0, max)}…` : src;
}

export function startFreshPleaHref(): string {
  clearPleaSession();
  return "/redaction/libre?fresh=1";
}
