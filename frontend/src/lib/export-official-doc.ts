/** Export PDF / impression — modèle plaidoirie Royaume du Maroc. */

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** Retire l'en-tête du corps si le LLM l'a dupliqué (l'export ajoute déjà un bandeau). */
export function stripExportHeaderFromBody(body: string): string {
  const lines = (body || "").replace(/\r\n/g, "\n").split("\n");
  const out: string[] = [];
  let inHeader = true;
  const headerRe =
    /^(?:المملكة\s*المغربية|Royaume\s+du\s+Maroc|المحكمة|الجهة\s*القضائية|رقم\s*الملف|تاريخ\s*(?:الجلسة|التحرير)|المكتب|المحامي|المحامية|محامي|محامية)/i;
  const introKeepRe =
    /^(?:سيدي\s*الرئيس|حضرة\s*(?:المحكمة|القاضي)|السيد\s+رئيس|السادة\s+القضاة|Monsieur\s+le\s+[Pp]r[eé]sident|Madame\s+la\s+[Pp]r[eé]sidente)/i;

  for (const raw of lines) {
    const line = raw.trim();
    if (inHeader) {
      if (!line) continue;
      if (headerRe.test(line) || /^[\.\…]{3,}$/.test(line)) continue;
      if (introKeepRe.test(line)) {
        inHeader = false;
      } else if (/^[\d]+[\)\.]?\s*[\u0600-\u06FF]/.test(line) && line.length < 80) {
        inHeader = false;
      } else if (/^(تحديد|أولاً|ثانياً|ثالثاً|رابعاً|خامساً|III|II|I[\.\)]|مرافعة|مذكرة|استنتاجات)/.test(line)) {
        inHeader = false;
      } else if (!headerRe.test(line) && line.length > 40) {
        inHeader = false;
      } else {
        continue;
      }
    }
    out.push(raw);
  }
  return out.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

/** Découpe un pavé collé en paragraphes (sauts + أولاً / ثانياً / …). */
export function structurePlaidoirieBody(body: string): string {
  let text = stripExportHeaderFromBody((body || "").replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim());
  if (!text) return "";
  text = text.replace(
    /\[\s*(?:À\s*VÉRIFIER|A\s*VERIFIER|TO\s*VERIFY|ART\.?\s*À\s*COMPLÉTER|يُستكمل)[^\]]*\]/gi,
    "(يُستكمل)",
  );
  text = text.replace(/\[\s*\]/g, "");
  text = text.replace(/([:：])\s*[—\-–]+\s*/g, "$1 ");
  text = text.replace(/([:：])\s*\/\s*/g, "$1 ");
  text = text.replace(/صيغة\s*الختام\s*[:：]?\s*/g, "");
  text = text.replace(/\bCasablanca\b/gi, "الدار البيضاء");
  text = text.replace(/[\.\…]{4,}/g, "[يُستكمل]");
  text = text.replace(/^\s*جده\s*وحيد[،,]?\s*/u, "السيد رئيس المحكمة المحترم،\n\n");
  text = text.replace(/جده\s*وحيد[،,]?\s*/gu, "");
  text = text.replace(
    /([^\n])\s*(أولاً|ثانياً|ثالثاً|رابعاً|خامساً|لهذه\s*الأسباب|تحديد\s*الأطراف|الملتمسات)\s*[:：]?/g,
    "$1\n\n$2 :",
  );
  text = text.replace(/(?:\s+)(\d{1,2}\s*[.)]\s+)/g, "\n$1");
  text = text
    .split("\n")
    .filter((line) => {
      const t = line.trim();
      if (/^(حرر\s*ب|التوقيع|خاتم\s*المحامي)\b/.test(t)) return false;
      if (/حرر\s*ب.+(التوقيع|خاتم)/.test(t) && t.length < 220) return false;
      return true;
    })
    .join("\n");
  return text.replace(/\n{3,}/g, "\n\n").trim();
}

function bodyToHtml(body: string): string {
  const structured = structurePlaidoirieBody(body);
  return escapeHtml(structured)
    .split(/\n\n+/)
    .map((p) => {
      const trimmed = p.trim();
      if (!trimmed) return "";
      const isHead = /^(تحديد\s*الأطراف|أولاً|ثانياً|ثالثاً|رابعاً|خامساً|لهذه\s*الأسباب)/.test(
        trimmed,
      );
      const isClose = /^(تحت\s*جميع|حرر\s*ب)/.test(trimmed);
      let cls = "";
      if (isHead) cls = ' class="sec"';
      else if (isClose) cls = ' class="close"';
      else if (/\[يُستكمل[^\]]*\]/.test(trimmed)) cls = ' class="todo"';
      return `<p${cls}>${trimmed.replace(/\n/g, "<br/>")}</p>`;
    })
    .join("");
}

/** URL absolue des armoiries (nécessaire pour la fenêtre d'impression). */
export function moroccoCoatOfArmsUrl(): string {
  if (typeof window === "undefined") return "/armoiries-maroc.png";
  return `${window.location.origin}/armoiries-maroc.png`;
}

let armsDataUrlCache: string | null = null;

async function moroccoCoatOfArmsDataUrl(): Promise<string> {
  if (armsDataUrlCache) return armsDataUrlCache;
  try {
    const res = await fetch(moroccoCoatOfArmsUrl());
    const blob = await res.blob();
    armsDataUrlCache = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ""));
      reader.onerror = () => reject(reader.error);
      reader.readAsDataURL(blob);
    });
    return armsDataUrlCache;
  } catch {
    return moroccoCoatOfArmsUrl();
  }
}

const PRINT_CSS = `
  @page {
    size: A4;
    margin: 1.5cm 1.8cm 2.2cm 1.8cm;
    @bottom-center {
      content: "(" counter(page) ")";
      font-family: "Amiri", "Traditional Arabic", serif;
      font-size: 10pt;
      color: #64748b;
    }
  }
  * { box-sizing: border-box; }
  body {
    font-family: "Amiri", "Traditional Arabic", "Scheherazade New", "Noto Naskh Arabic", "Times New Roman", serif;
    color: #1a2332;
    line-height: 1.85;
    font-size: 13pt;
    background: #fff;
    counter-reset: page;
  }
  .official-header {
    direction: ltr;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    border-bottom: 2px solid #1a3a2a;
    padding-bottom: 10px;
    margin-bottom: 18px;
  }
  .official-header .col-ar {
    flex: 1;
    text-align: right;
    direction: rtl;
    font-size: 12pt;
    font-weight: 700;
    color: #1a3a2a;
  }
  .official-header .col-logo {
    flex: 0 0 auto;
    text-align: center;
    min-width: 72px;
    min-height: 48px;
  }
  .official-header .col-logo img {
    height: 52px;
    width: auto;
    max-width: 120px;
    object-fit: contain;
  }
  .official-header .col-fr {
    flex: 1;
    text-align: left;
    direction: ltr;
    font-size: 11pt;
    font-weight: 700;
    color: #0B1A4D;
    font-family: Georgia, "Times New Roman", serif;
  }
  .court-line {
    margin-top: 6px;
    font-size: 11pt;
    font-weight: 600;
    color: #334155;
    text-align: center;
    width: 100%;
  }
  .meta-block {
    font-size: 10.5pt;
    color: #334155;
    margin: 0 0 16px;
    line-height: 1.7;
    text-align: right;
  }
  .meta-block div { margin: 0 0 2px; }
  .cabinet-logo-wrap {
    display: none;
  }
  .cabinet-logo-wrap img {
    display: none;
  }
  h1 {
    text-align: center;
    font-size: 14pt;
    color: #1a3a2a;
    margin: 0 0 18px;
    text-decoration: underline;
    text-underline-offset: 6px;
  }
  .body p { margin: 0 0 14px; text-align: justify; text-indent: 1.2em; }
  .body p:first-child { text-indent: 0; }
  .body p.sec {
    text-indent: 0;
    font-weight: 700;
    margin-top: 20px;
    padding: 8px 0 4px;
    border-top: 2px solid rgba(26, 58, 42, 0.25);
    color: #1a3a2a;
  }
  .body p.close { text-indent: 0; margin-top: 24px; font-style: italic; }
  .body p.todo { color: #b45309; font-weight: 600; text-indent: 0; }
  .sign {
    margin-top: 36px;
    text-align: right;
    direction: rtl;
    font-size: 11pt;
  }
  .sign .esign-label {
    font-size: 10pt;
    color: #64748b;
    margin-top: 12px;
  }
  .sign .esign-name {
    font-size: 15pt;
    font-weight: 700;
    font-style: italic;
    color: #1a3a2a;
    margin-top: 4px;
  }
  .sign .esign-date {
    font-size: 9pt;
    color: #64748b;
  }
  .print-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    text-align: center;
    font-size: 9pt;
    color: #94a3b8;
    padding-top: 4px;
  }
  .print-footer .page-num::after {
    content: counter(page);
  }
  @media print {
    .no-print { display: none !important; }
    .print-footer {
      position: fixed;
      bottom: 0.4cm;
    }
  }
`;

function buildDocumentHtml(opts: {
  title: string;
  body: string;
  headerAr?: string;
  headerFr?: string;
  courtName?: string;
  cabinetName?: string;
  cabinetNameAr?: string;
  lawyerName?: string;
  city?: string;
  cabinetLogoUrl?: string;
  includeEsignature?: boolean;
  autoPrint?: boolean;
}): string {
  const nameFr = (opts.headerFr || opts.cabinetName || "").trim();
  const nameAr = (opts.headerAr || opts.cabinetNameAr || opts.cabinetName || nameFr).trim();
  const today = new Date().toLocaleDateString("ar-MA", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const todayShort = new Date().toLocaleDateString("fr-MA");
  const logo = opts.cabinetLogoUrl
    ? `<img src="${escapeHtml(opts.cabinetLogoUrl)}" alt="Logo cabinet" />`
    : "";
  const signBlock = opts.includeEsignature && opts.lawyerName
    ? `<div>حرر بـ ${escapeHtml(opts.city || "")}</div>
       <div class="esign-label">التوقيع الإلكتروني</div>
       <div class="esign-name">${escapeHtml(opts.lawyerName)}</div>
       <div class="esign-date">${escapeHtml(todayShort)}</div>`
    : `${opts.city ? `<div>حرر بـ ${escapeHtml(opts.city)}</div>` : ""}
       ${opts.lawyerName ? `<div style="margin-top:28px">التوقيع<br/><strong>${escapeHtml(opts.lawyerName)}</strong><br/>خاتم المحامي</div>` : ""}`;

  return `<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8" />
  <title>${escapeHtml(opts.title)}</title>
  <style>${PRINT_CSS}</style>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap" rel="stylesheet" />
</head>
<body>
  <div class="official-header">
    <div class="col-ar">${escapeHtml(nameAr)}</div>
    <div class="col-logo">${logo || "&nbsp;"}</div>
    <div class="col-fr">${escapeHtml(nameFr)}</div>
  </div>
  ${opts.courtName ? `<div class="court-line">${escapeHtml(opts.courtName)}</div>` : ""}
  <div class="meta-block">
    ${opts.lawyerName ? `<div>المحامي المعد : ${escapeHtml(opts.lawyerName)}</div>` : ""}
    <div>تاريخ التحرير : ${escapeHtml(today)}</div>
  </div>
  <h1>${escapeHtml(opts.title)}</h1>
  <div class="body">${bodyToHtml(opts.body)}</div>
  <div class="sign">${signBlock}</div>
  <div class="print-footer" aria-hidden="true">
    LexHub — صفحة <span class="page-num"></span>
  </div>
  ${opts.autoPrint ? `<script>window.onload = () => { setTimeout(() => window.print(), 400); };</script>` : ""}
</body>
</html>`;
}

export async function exportOfficialArabicDocument(opts: {
  title: string;
  body: string;
  headerAr?: string;
  headerFr?: string;
  cabinetName?: string;
  lawyerName?: string;
  city?: string;
  cabinetLogoUrl?: string;
  includeEsignature?: boolean;
  /** true = dialogue d'impression ; false = ouverture pour Enregistrer en PDF */
  autoPrint?: boolean;
}) {
  const html = buildDocumentHtml({
    title: opts.title,
    body: opts.body,
    headerAr: opts.headerAr,
    headerFr: opts.headerFr,
    cabinetName: opts.cabinetName,
    lawyerName: opts.lawyerName,
    city: opts.city,
    cabinetLogoUrl: opts.cabinetLogoUrl,
    includeEsignature: opts.includeEsignature,
    autoPrint: opts.autoPrint !== false,
  });
  const win = window.open("", "_blank");
  if (!win) {
    alert("Autorisez les pop-ups pour imprimer / enregistrer en PDF.");
    return;
  }
  win.document.write(html);
  win.document.close();
}

/** Construit le HTML officiel (sans auto-print) pour PDF/DOC. */
export async function buildOfficialArabicHtml(opts: {
  title: string;
  body: string;
  headerAr?: string;
  headerFr?: string;
  cabinetName?: string;
  cabinetNameAr?: string;
  lawyerName?: string;
  city?: string;
  cabinetLogoUrl?: string;
  includeEsignature?: boolean;
}): Promise<string> {
  return buildDocumentHtml({ ...opts, autoPrint: false });
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/** Télécharge un fichier .doc (HTML compatible Word). */
export async function downloadOfficialArabicDoc(opts: {
  title: string;
  body: string;
  cabinetName?: string;
  lawyerName?: string;
  city?: string;
  filename?: string;
  cabinetLogoUrl?: string;
  includeEsignature?: boolean;
}) {
  const html = await buildOfficialArabicHtml(opts);
  const blob = new Blob(["\ufeff", html], { type: "application/msword;charset=utf-8" });
  const safe = (opts.filename || opts.title || "plaidoirie")
    .replace(/[^\w\u0600-\u06FF\-]+/g, "_")
    .slice(0, 60);
  triggerDownload(blob, `${safe}.doc`);
}

/** Téléchargement direct (sans dialogue d'impression) — HTML prêt pour PDF navigateur. */
export async function downloadOfficialArabicHtml(opts: {
  title: string;
  body: string;
  cabinetName?: string;
  lawyerName?: string;
  city?: string;
  filename?: string;
}) {
  const html = await buildOfficialArabicHtml(opts);
  const blob = new Blob(["\ufeff", html], { type: "text/html;charset=utf-8" });
  const safe = (opts.filename || opts.title || "plaidoirie")
    .replace(/[^\w\u0600-\u06FF\-]+/g, "_")
    .slice(0, 60);
  triggerDownload(blob, `${safe}.html`);
}

/** Alias PDF → téléchargement HTML direct (ouvrir puis Ctrl+P → Enregistrer en PDF). */
export const downloadOfficialArabicPdf = downloadOfficialArabicHtml;

/** Fichier texte/HTML pour archivage dans un dossier LexHub. */
export async function plaidoirieFileFromContent(opts: {
  title: string;
  body: string;
  cabinetName?: string;
  lawyerName?: string;
}): Promise<File> {
  const html = await buildOfficialArabicHtml(opts);
  const safe = (opts.title || "plaidoirie").replace(/[^\w\u0600-\u06FF\-]+/g, "_").slice(0, 40);
  return new File([html], `plaidoirie_${safe}.html`, { type: "text/html" });
}
