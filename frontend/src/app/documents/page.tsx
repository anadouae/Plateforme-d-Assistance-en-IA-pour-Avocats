"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, Eye, FileText, Trash2 } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api, type DocumentItem } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} o`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
}

export default function DocumentsPage() {
  const user = useAuthStore((s) => s.user);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api.getDocuments().then(setDocuments).catch(() => setDocuments([])).finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  const canDelete = user?.role !== "assistant_juridique";

  return (
    <AppShell>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-sanad-slate">Documents</h1>

        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-sanad-border bg-sanad-light text-left text-slate-500">
                    <th className="px-6 py-3 font-medium">Nom</th>
                    <th className="px-6 py-3 font-medium">Dossier</th>
                    <th className="px-6 py-3 font-medium">Taille</th>
                    <th className="px-6 py-3 font-medium">OCR</th>
                    <th className="px-6 py-3 font-medium">Statut</th>
                    <th className="px-6 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-8 text-center text-slate-400">
                        Chargement...
                      </td>
                    </tr>
                  ) : documents.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-8 text-center text-slate-400">
                        Aucun document. Importez depuis un dossier.
                      </td>
                    </tr>
                  ) : (
                    documents.map((doc) => (
                      <tr key={doc.id} className="border-b border-sanad-border hover:bg-sanad-light/50">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 text-sanad-blue" />
                            <span className="font-medium text-sanad-slate">{doc.original_name}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <Link href={`/cases/${doc.case_id}`} className="text-sanad-blue hover:underline">
                            {doc.case_reference || "—"}
                          </Link>
                        </td>
                        <td className="px-6 py-4 text-slate-600">{formatSize(doc.file_size)}</td>
                        <td className="px-6 py-4">
                          {doc.ocr_score != null ? (
                            <span className={doc.ocr_score < 70 ? "flex items-center gap-1 text-amber-600" : "text-green-700"}>
                              {doc.ocr_score < 70 && <AlertTriangle className="h-3.5 w-3.5" />}
                              {doc.ocr_score} %
                            </span>
                          ) : (
                            <span className="text-slate-400">N/A</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">
                            {doc.status}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex gap-2">
                            <Link href={`/documents/${doc.id}`}>
                              <Button variant="ghost" size="sm">
                                <Eye className="h-4 w-4" />
                                Voir
                              </Button>
                            </Link>
                            {canDelete && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={async () => {
                                  if (confirm("Supprimer ce document ?")) {
                                    await api.deleteDocument(doc.id);
                                    load();
                                  }
                                }}
                              >
                                <Trash2 className="h-4 w-4 text-red-500" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
