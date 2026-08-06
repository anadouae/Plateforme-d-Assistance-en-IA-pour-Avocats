"use client";

import { useEffect, useState } from "react";
import { FileSignature, Loader2 } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api, type DocumentTemplate } from "@/lib/api";
import { RoleGate } from "@/components/auth/role-gate";

export default function TemplatesPage() {
  return (
    <RoleGate allow={["avocat", "admin_cabinet"]}>
      <TemplatesPageInner />
    </RoleGate>
  );
}

function TemplatesPageInner() {
  const [templates, setTemplates] = useState<DocumentTemplate[]>([]);
  const [selected, setSelected] = useState<DocumentTemplate | null>(null);
  const [fields, setFields] = useState<Record<string, string>>({});
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getTemplates().then((r) => setTemplates(r.templates)).catch(() => {});
  }, []);

  const handleSelect = (t: DocumentTemplate) => {
    setSelected(t);
    setFields(Object.fromEntries(t.fields.map((f) => [f, ""])));
    setOutput("");
    setError("");
  };

  const handleGenerate = async () => {
    if (!selected) return;
    setLoading(true);
    setError("");
    try {
      const result = await api.generateDocument(selected.id, fields);
      setOutput(result.content);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur de génération");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-sanad-slate">
            <FileSignature className="h-6 w-6 text-sanad-blue" />
            Modèles de contrats
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Génération de documents juridiques marocains — style Adala, intégré à Sanad.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-1">
            <CardContent className="space-y-2 p-4">
              <h2 className="font-semibold text-sanad-slate">Modèles disponibles</h2>
              {templates.map((t) => (
                <button
                  key={t.id}
                  onClick={() => handleSelect(t)}
                  className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition-colors ${
                    selected?.id === t.id
                      ? "border-sanad-blue bg-sanad-blue/5 text-sanad-blue"
                      : "border-sanad-border hover:bg-sanad-light"
                  }`}
                >
                  <p className="font-medium">{t.name}</p>
                  <p className="text-xs text-slate-500">{t.category}</p>
                </button>
              ))}
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardContent className="space-y-4 p-6">
              {selected ? (
                <>
                  <div>
                    <h2 className="font-semibold text-sanad-slate">{selected.name}</h2>
                    <p className="text-sm text-slate-500">{selected.description}</p>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {selected.fields.map((field) => (
                      <label key={field} className="block text-sm">
                        <span className="mb-1 block font-medium text-slate-600">{field}</span>
                        <input
                          className="w-full rounded-lg border border-sanad-border px-3 py-2"
                          value={fields[field] || ""}
                          onChange={(e) => setFields({ ...fields, [field]: e.target.value })}
                        />
                      </label>
                    ))}
                  </div>
                  {error && <p className="text-sm text-red-600">{error}</p>}
                  <Button onClick={handleGenerate} disabled={loading}>
                    {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Générer le document
                  </Button>
                  {output && (
                    <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-lg bg-sanad-light p-4 text-sm">
                      {output}
                    </pre>
                  )}
                </>
              ) : (
                <p className="text-sm text-slate-500">Sélectionnez un modèle pour commencer.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
