/** Export PDF / impression — modèle plaidoirie Royaume du Maroc. */

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function bodyToHtml(body: string): string {
  return escapeHtml(body)
    .split(/\n\n+/)
    .map((p) => `<p>${p.replace(/\n/g, "<br/>")}</p>`)
    .join("");
}

/** URL absolue des armoiries (nécessaire pour la fenêtre d'impression). */
export function moroccoCoatOfArmsUrl(): string {
  if (typeof window === "undefined") return "/armoiries-maroc.png";
  return `${window.location.origin}/armoiries-maroc.png`;
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
    text-align: center;
    border-bottom: 2px solid #1a3a2a;
    padding-bottom: 10px;
    margin-bottom: 18px;
  }
  .emblem {
    display: block;
    margin: 0 auto 6px;
    width: 42px;
    height: auto;
    max-height: 52px;
    object-fit: contain;
  }
  .kingdom-ar {
    font-size: 14pt;
    font-weight: 700;
    color: #1a3a2a;
    letter-spacing: 0.02em;
  }
  .kingdom-fr {
    font-size: 9pt;
    color: #4a5568;
    font-family: Georgia, "Times New Roman", serif;
    direction: ltr;
    margin-top: 2px;
  }
  .doc-kind {
    margin-top: 4px;
    font-size: 10pt;
    font-weight: 700;
    color: #c5a028;
    letter-spacing: 0.04em;
  }
  .motto {
    font-size: 8pt;
    color: #8b7355;
    margin-top: 2px;
    font-weight: 600;
  }
  .meta {
    display: flex;
    justify-content: space-between;
    font-size: 9pt;
    color: #64748b;
    margin-bottom: 16px;
    gap: 12px;
    flex-wrap: wrap;
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
  .sign {
    margin-top: 36px;
    text-align: left;
    direction: rtl;
    font-size: 11pt;
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
    .emblem { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
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
  mottoAr?: string;
  cabinetName?: string;
  lawyerName?: string;
  city?: string;
  autoPrint?: boolean;
}): string {
  const headerAr = opts.headerAr || "المملكة المغربية";
  const headerFr = opts.headerFr || "Royaume du Maroc";
  const mottoAr = opts.mottoAr || "الله · الوطن · الملك";
  const emblemUrl = moroccoCoatOfArmsUrl();
  const today = new Date().toLocaleDateString("ar-MA", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

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
    <img class="emblem" src="${emblemUrl}" alt="Armoiries du Royaume du Maroc" width="42" height="52" />
    <div class="kingdom-ar">${escapeHtml(headerAr)}</div>
    <div class="kingdom-fr">${escapeHtml(headerFr)}</div>
    <div class="doc-kind">مرافعة · Plaidoirie</div>
    <div class="motto">${escapeHtml(mottoAr)}</div>
  </div>
  <div class="meta">
    <span>${opts.cabinetName ? escapeHtml(opts.cabinetName) : ""}</span>
    <span>${escapeHtml(today)}</span>
  </div>
  <h1>${escapeHtml(opts.title)}</h1>
  <div class="body">${bodyToHtml(opts.body)}</div>
  <div class="sign">
    ${opts.city ? `<div>حرر بـ${escapeHtml(opts.city)}</div>` : ""}
    ${opts.lawyerName ? `<div style="margin-top:28px">التوقيع<br/><strong>${escapeHtml(opts.lawyerName)}</strong></div>` : ""}
  </div>
  <div class="print-footer" aria-hidden="true">
    سند — صفحة <span class="page-num"></span>
  </div>
  ${opts.autoPrint ? `<script>window.onload = () => { setTimeout(() => window.print(), 400); };</script>` : ""}
</body>
</html>`;
}

export function exportOfficialArabicDocument(opts: {
  title: string;
  body: string;
  headerAr?: string;
  headerFr?: string;
  mottoAr?: string;
  cabinetName?: string;
  lawyerName?: string;
  city?: string;
}) {
  const html = buildDocumentHtml({ ...opts, autoPrint: true });
  const win = window.open("", "_blank");
  if (!win) {
    alert("Autorisez les pop-ups pour imprimer / enregistrer en PDF.");
    return;
  }
  win.document.write(html);
  win.document.close();
}

/** Construit le HTML officiel (sans auto-print) pour PDF/DOC. */
export function buildOfficialArabicHtml(opts: {
  title: string;
  body: string;
  headerAr?: string;
  headerFr?: string;
  mottoAr?: string;
  cabinetName?: string;
  lawyerName?: string;
  city?: string;
}): string {
  return buildDocumentHtml({ ...opts, autoPrint: false });
}

/** Télécharge un fichier .doc (HTML compatible Word). */
export function downloadOfficialArabicDoc(opts: {
  title: string;
  body: string;
  cabinetName?: string;
  lawyerName?: string;
  city?: string;
  filename?: string;
}) {
  const html = buildOfficialArabicHtml(opts);
  const blob = new Blob(["\ufeff", html], { type: "application/msword;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  const safe = (opts.filename || opts.title || "plaidoirie")
    .replace(/[^\w\u0600-\u06FF\-]+/g, "_")
    .slice(0, 60);
  a.href = url;
  a.download = `${safe}.doc`;
  a.click();
  URL.revokeObjectURL(url);
}

/** Fichier texte/HTML pour archivage dans un dossier Sanad. */
export function plaidoirieFileFromContent(opts: {
  title: string;
  body: string;
  cabinetName?: string;
  lawyerName?: string;
}): File {
  const html = buildOfficialArabicHtml(opts);
  const safe = (opts.title || "plaidoirie").replace(/[^\w\u0600-\u06FF\-]+/g, "_").slice(0, 40);
  return new File([html], `plaidoirie_${safe}.html`, { type: "text/html" });
}
