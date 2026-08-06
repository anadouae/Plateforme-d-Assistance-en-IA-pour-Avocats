"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CalendarDays, FileText, Sparkles } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { DocumentStatusBadge } from "@/components/ai/document-status-badge";
import { DocumentUpload } from "@/components/documents/document-upload";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  api,
  type AgendaEventItem,
  type CaseAnalysisResult,
  type CaseDetail,
  type DocumentItem,
} from "@/lib/api";
import { FadeIn } from "@/components/motion/fade-in";
import { useAuthStore } from "@/store/auth";

type Tab = "resume" | "documents" | "activite";

export default function CaseDetailPage() {
  const params = useParams();
  const caseId = params.id as string;
  const user = useAuthStore((s) => s.user);
  const [tab, setTab] = useState<Tab>("resume");
  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [agenda, setAgenda] = useState<AgendaEventItem[]>([]);
  const [analysis, setAnalysis] = useState<CaseAnalysisResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyseError, setAnalyseError] = useState<string | null>(null);

  const canUseAI = user?.role !== "assistant_juridique";

  function load() {
    api.getCase(caseId).then(setCaseData).catch(() => setCaseData(null));
    api.getDocuments(caseId).then(setDocuments).catch(() => setDocuments([]));
    api.getAgenda(caseId).then(setAgenda).catch(() => setAgenda([]));
  }

  useEffect(() => {
    load();
  }, [caseId]);

  async function runAnalysis() {
    setAnalyzing(true);
    setAnalyseError(null);
    try {
      const result = await api.analyseCase(caseId);
      setAnalysis(result);
    } catch (e) {
      const msg =
        e instanceof Error && e.name === "TimeoutError"
          ? "L'analyse prend trop de temps (max 5 min). Réessayez."
          : e instanceof Error
            ? e.message
            : "Analyse impossible";
      setAnalyseError(msg);
    } finally {
      setAnalyzing(false);
    }
  }

  const tabs: { id: Tab; label: string; hidden?: boolean }[] = [
    { id: "resume", label: "Résumé" },
    { id: "documents", label: "Documents" },
    { id: "activite", label: "Activité" },
  ];

  if (!caseData) {
    return (
      <AppShell>
        <div className="flex items-center gap-2 text-slate-500">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-sanad-blue border-t-transparent" />
          Chargement du dossier...
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <FadeIn className="space-y-6">
        <div>
          <Link
            href="/cases"
            className="mb-2 inline-flex items-center gap-1 text-sm text-sanad-blue hover:underline"
          >
            <ArrowLeft className="h-4 w-4" />
            Retour aux dossiers
          </Link>
          <h1 className="font-display text-2xl font-semibold text-sanad-navy">
            {caseData.reference} — {caseData.client_name}
          </h1>
          <p className="text-sm text-slate-500">
            <span className="rounded-md bg-sanad-gold/15 px-1.5 py-0.5 font-medium text-sanad-navy">
              {caseData.case_type}
            </span>{" "}
            · {caseData.status}
          </p>
        </div>

        <div className="flex gap-1 overflow-x-auto border-b border-sanad-border">
          {tabs
            .filter((t) => !t.hidden)
            .map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTab(t.id)}
                className={`whitespace-nowrap px-4 py-2.5 text-sm font-medium transition-colors ${
                  tab === t.id
                    ? "border-b-2 border-sanad-blue text-sanad-blue"
                    : "text-slate-500 hover:text-sanad-slate"
                }`}
              >
                {t.label}
              </button>
            ))}
        </div>

        {tab === "resume" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Informations dossier</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3 text-sm sm:grid-cols-2">
                <div>
                  <span className="text-slate-500">Client :</span> {caseData.client_name}
                </div>
                <div>
                  <span className="text-slate-500">Responsable :</span>{" "}
                  {caseData.responsible_name}
                </div>
                <div>
                  <span className="text-slate-500">Ouverture :</span>{" "}
                  {new Date(caseData.opened_at).toLocaleDateString("fr-FR")}
                </div>
                <div>
                  <span className="text-slate-500">Statut :</span> {caseData.status}
                </div>
                {caseData.description && (
                  <div className="sm:col-span-2">
                    <span className="text-slate-500">Description :</span>{" "}
                    {caseData.description}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="border-sanad-gold/25 shadow-luxe">
              <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <CalendarDays className="h-5 w-5 text-sanad-gold" />
                  Planning lié à ce dossier
                </CardTitle>
                <Link href="/agenda">
                  <Button size="sm" variant="outline">
                    Ouvrir le planning
                  </Button>
                </Link>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {agenda.length === 0 ? (
                  <p className="text-slate-500">
                    Aucun événement rattaché. Créez une audience ou un délai depuis le Planning
                    en sélectionnant ce dossier.
                  </p>
                ) : (
                  <ul className="divide-y divide-sanad-border">
                    {agenda.map((e) => (
                      <li key={e.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
                        <div>
                          <p className="font-medium text-sanad-navy">{e.title}</p>
                          <p className="text-xs text-slate-500">
                            {e.event_type} ·{" "}
                            {new Date(e.starts_at).toLocaleString("fr-FR")}
                          </p>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            {canUseAI && (
              <Card>
                <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-sanad-blue" />
                    Analyse IA du dossier
                  </CardTitle>
                  <Button
                    type="button"
                    onClick={runAnalysis}
                    disabled={analyzing || documents.length === 0}
                  >
                    {analyzing ? "Analyse en cours…" : "Analyser le dossier"}
                  </Button>
                </CardHeader>
                <CardContent className="space-y-4 text-sm">
                  {documents.length === 0 && (
                    <p className="text-slate-500">
                      Ajoutez des documents pour lancer l&apos;analyse Sanad-Legal.
                    </p>
                  )}
                  {analyseError && <p className="text-red-600">{analyseError}</p>}
                  {analysis && (
                    <div className="space-y-4">
                      <p className="whitespace-pre-wrap text-sanad-slate">{analysis.summary}</p>
                      <div className="grid gap-3 sm:grid-cols-2">
                        <div>
                          <p className="font-medium text-sanad-slate">Parties</p>
                          <ul className="mt-1 list-disc pl-5 text-slate-600">
                            {analysis.parties.map((p) => (
                              <li key={p}>{p}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <p className="font-medium text-sanad-slate">Dates clés</p>
                          <ul className="mt-1 list-disc pl-5 text-slate-600">
                            {analysis.key_dates.map((d) => (
                              <li key={d}>{d}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <p className="font-medium text-sanad-slate">Risques / délais</p>
                          <ul className="mt-1 list-disc pl-5 text-slate-600">
                            {analysis.risks_and_deadlines.map((r) => (
                              <li key={r}>{r}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <p className="font-medium text-sanad-slate">Checklist</p>
                          <ul className="mt-1 list-disc pl-5 text-slate-600">
                            {analysis.checklist.map((c) => (
                              <li key={c}>{c}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                      <p className="text-xs text-slate-400">
                        Confiance {analysis.confidence_score}% · {analysis.disclaimer}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {tab === "documents" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Importer un document</CardTitle>
              </CardHeader>
              <CardContent>
                <DocumentUpload
                  caseId={caseId}
                  onUpload={(cid, file) => api.uploadDocument(cid, file)}
                  onUploaded={load}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Documents ({documents.length})</CardTitle>
              </CardHeader>
              <CardContent className="divide-y divide-sanad-border">
                {documents.length === 0 ? (
                  <p className="py-4 text-center text-slate-400">Aucun document</p>
                ) : (
                  documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex flex-wrap items-center justify-between gap-3 py-4 first:pt-0"
                    >
                      <div className="flex min-w-0 items-start gap-3">
                        <FileText className="mt-0.5 h-4 w-4 shrink-0 text-sanad-blue" />
                        <div className="min-w-0">
                          <p className="truncate font-medium text-sanad-slate">
                            {doc.original_name}
                          </p>
                          <DocumentStatusBadge
                            className="mt-1"
                            status={doc.status}
                            ocrScore={doc.ocr_score}
                            ocrAlert={doc.ocr_alert}
                          />
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Link href={`/documents/${doc.id}`}>
                          <Button variant="outline" size="sm">
                            Analyser
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {tab === "activite" && (
          <Card>
            <CardHeader>
              <CardTitle>Timeline</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="flex gap-3">
                <div className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-sanad-blue" />
                <div>
                  <p className="font-medium">Dossier créé</p>
                  <p className="text-slate-500">
                    {new Date(caseData.opened_at).toLocaleString("fr-FR")}
                  </p>
                </div>
              </div>
              {documents.map((doc) => (
                <div key={doc.id} className="flex gap-3">
                  <div className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-sanad-gold" />
                  <div>
                    <p className="font-medium">Document : {doc.original_name}</p>
                    <p className="text-slate-500">
                      {new Date(doc.created_at).toLocaleString("fr-FR")} · {doc.status}
                    </p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </FadeIn>
    </AppShell>
  );
}
