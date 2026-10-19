/** Libellé d’affichage d’un dossier (marché : intitulé > client). */
export function caseDisplayTitle(c: {
  title?: string | null;
  client_name?: string | null;
  reference?: string | null;
}): string {
  const title = (c.title || "").trim();
  if (title) return title;
  const client = (c.client_name || "").trim();
  if (client) return client;
  return (c.reference || "").trim() || "—";
}

/** Ligne courte pour listes / selects : REF — intitulé */
export function caseSelectLabel(c: {
  title?: string | null;
  client_name?: string | null;
  reference?: string | null;
}): string {
  const ref = (c.reference || "").trim() || "—";
  const title = (c.title || "").trim();
  const client = (c.client_name || "").trim();
  if (title && client && title !== client) return `${ref} — ${title} · ${client}`;
  if (title) return `${ref} — ${title}`;
  if (client) return `${ref} — ${client}`;
  return ref;
}

/** Infos compactes pour tooltip / popover au survol. */
export function caseHoverLines(
  c: {
    title?: string | null;
    client_name?: string | null;
    reference?: string | null;
    case_type?: string | null;
    status?: string | null;
    opposing_name?: string | null;
    tribunal?: string | null;
    court_city?: string | null;
    court_file_number?: string | null;
    responsible_name?: string | null;
  },
  lang: "fr" | "ar" = "fr",
): { heading: string; lines: string[] } {
  const fr = lang === "fr";
  const heading = caseDisplayTitle(c);
  const lines: string[] = [];
  if (c.reference) lines.push(fr ? `Réf. ${c.reference}` : `المرجع ${c.reference}`);
  if ((c.title || "").trim() && (c.client_name || "").trim()) {
    lines.push(fr ? `Client : ${c.client_name}` : `الزبون : ${c.client_name}`);
  }
  if ((c.opposing_name || "").trim()) {
    lines.push(fr ? `Adverse : ${c.opposing_name}` : `الخصم : ${c.opposing_name}`);
  }
  if ((c.case_type || "").trim()) {
    lines.push(fr ? `Type : ${c.case_type}` : `النوع : ${c.case_type}`);
  }
  if ((c.status || "").trim()) {
    lines.push(fr ? `Statut : ${c.status}` : `الحالة : ${c.status}`);
  }
  const tribunal = [c.tribunal, c.court_city].filter(Boolean).join(" — ");
  if (tribunal) lines.push(fr ? `Tribunal : ${tribunal}` : `المحكمة : ${tribunal}`);
  if ((c.court_file_number || "").trim()) {
    lines.push(fr ? `N° greffe : ${c.court_file_number}` : `رقم الملف : ${c.court_file_number}`);
  }
  if ((c.responsible_name || "").trim()) {
    lines.push(fr ? `Responsable : ${c.responsible_name}` : `المسؤول : ${c.responsible_name}`);
  }
  return { heading, lines };
}
