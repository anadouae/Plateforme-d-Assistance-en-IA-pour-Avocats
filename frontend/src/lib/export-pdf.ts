import type { AIResult } from "@/lib/api";

const sourceLabels: Record<string, string> = {
  rag: "Corpus juridique",
  web: "Recherche web",
  document: "Document",
  "rag+web": "Corpus + Web",
};

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function exportAiResponsePdf(result: AIResult, title = "Réponse Sanad IA") {
  const sourcesHtml = result.sources
    .map(
      (src) =>
        `<div class="source"><strong>${escapeHtml(src.label)}</strong><p>${escapeHtml(src.excerpt)}</p></div>`,
    )
    .join("");

  const html = `<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <title>${escapeHtml(title)}</title>
  <style>
    @page { margin: 2cm; }
    body { font-family: Georgia, "Times New Roman", serif; color: #1e293b; line-height: 1.6; font-size: 11pt; }
    .header { border-bottom: 2px solid #1e40af; padding-bottom: 12px; margin-bottom: 24px; }
    .logo { font-size: 18pt; font-weight: bold; color: #1e40af; }
    .meta { display: flex; gap: 16px; margin: 16px 0; flex-wrap: wrap; }
    .badge { background: #eff6ff; color: #1e40af; padding: 4px 12px; border-radius: 999px; font-size: 9pt; }
    .confidence { background: ${result.confidence_score < 60 ? "#fef3c7" : "#dcfce7"}; color: ${result.confidence_score < 60 ? "#92400e" : "#166534"}; padding: 4px 12px; border-radius: 999px; font-size: 9pt; }
    .answer { white-space: pre-wrap; margin: 20px 0; }
    .sources-title { font-size: 9pt; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; margin-top: 24px; }
    .source { border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-top: 8px; }
    .source p { margin: 6px 0 0; color: #475569; font-size: 10pt; }
    .disclaimer { font-size: 8pt; color: #94a3b8; font-style: italic; margin-top: 32px; border-top: 1px solid #e2e8f0; padding-top: 12px; }
    .date { font-size: 9pt; color: #64748b; }
  </style>
</head>
<body>
  <div class="header">
    <div class="logo">Sanad — Avocat AI Assistance</div>
    <div class="date">Exporté le ${new Date().toLocaleString("fr-FR")}</div>
  </div>
  <h2>${escapeHtml(title)}</h2>
  <div class="meta">
    <span class="badge">${escapeHtml(sourceLabels[result.source_type] || result.source_type)}</span>
    <span class="confidence">Confiance : ${result.confidence_score} %</span>
  </div>
  <div class="answer">${escapeHtml(result.answer)}</div>
  ${result.sources.length > 0 ? `<p class="sources-title">Sources citées</p>${sourcesHtml}` : ""}
  <p class="disclaimer">${escapeHtml(result.disclaimer)}</p>
  <script>window.onload = () => { window.print(); }</script>
</body>
</html>`;

  const win = window.open("", "_blank");
  if (!win) {
    alert("Autorisez les pop-ups pour exporter en PDF.");
    return;
  }
  win.document.write(html);
  win.document.close();
}
