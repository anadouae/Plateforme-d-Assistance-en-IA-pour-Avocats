"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Download,
  FileText,
  Loader2,
  Printer,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TemplatePicker } from "@/components/redaction/template-picker";
import {
  api,
  ApiError,
  type CabinetPlaidoirieTemplate,
  type DocumentItem,
} from "@/lib/api";
import {
  downloadOfficialArabicDoc,
  exportOfficialArabicDocument,
} from "@/lib/export-official-doc";
import { PLAIDOIRIE_TEMPLATES } from "@/lib/plaidoirie-templates";
import { useAuthStore } from "@/store/auth";
import { isAssistant } from "@/lib/roles";

export default function RedactionPage() {
  const user = useAuthStore((s) => s.user);
  const assistantMode = isAssistant(user?.role);

  return (
    <AppShell>
      {assistantMode ? <AssistantPlaidoirieView /> : <LawyerTemplateHub />}
    </AppShell>
  );
}

function LawyerTemplateHub() {
  const router = useRouter();
  const [customTemplates, setCustomTemplates] = useState<CabinetPlaidoirieTemplate[]>(
    [],
  );

  useEffect(() => {
    api
      .listCabinetPlaidoirieTemplates()
      .then(setCustomTemplates)
      .catch(() => setCustomTemplates([]));
  }, []);

  async function handleDeleteCustom(id: string) {
    if (!window.confirm("حذف هذا النموذج؟")) return;
    try {
      await api.deleteCabinetPlaidoirieTemplate(id);
      setCustomTemplates((prev) => prev.filter((t) => t.id !== id));
    } catch (e) {
      window.alert(e instanceof ApiError ? e.message : "تعذر الحذف");
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-2xl font-semibold text-sanad-navy" dir="rtl">
          مرافعة
        </h1>
      </motion.div>

      <TemplatePicker
        systemTemplates={PLAIDOIRIE_TEMPLATES}
        customTemplates={customTemplates}
        onSelect={(id) => router.push(`/redaction/${encodeURIComponent(id)}`)}
        onDeleteCustom={(id) => void handleDeleteCustom(id)}
      />
    </div>
  );
}

function AssistantPlaidoirieView() {
  const user = useAuthStore((s) => s.user);
  const [docs, setDocs] = useState<(DocumentItem & { caseRef?: string })[]>([]);
  const [loading, setLoading] = useState(true);
  const [preview, setPreview] = useState<{ title: string; body: string } | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const cases = await api.getCases();
        const all: (DocumentItem & { caseRef?: string })[] = [];
        for (const c of cases) {
          const list = await api.getDocuments(c.id).catch(() => []);
          for (const d of list) {
            const name = (d.original_name || "").toLowerCase();
            if (
              name.includes("plaidoirie") ||
              name.includes("مرافعة") ||
              name.includes("marafa") ||
              name.startsWith("plaidoirie_")
            ) {
              all.push({ ...d, caseRef: c.reference });
            }
          }
        }
        setDocs(all);
      } catch {
        setDocs([]);
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  async function openDoc(d: DocumentItem) {
    setBusyId(d.id);
    try {
      const detail = await api.getDocument(d.id);
      const raw = detail.extracted_text_preview || "";
      const text = raw
        .replace(/<style[\s\S]*?<\/style>/gi, " ")
        .replace(/<script[\s\S]*?<\/script>/gi, " ")
        .replace(/<[^>]+>/g, " ")
        .replace(/&nbsp;/g, " ")
        .replace(/\s+/g, " ")
        .trim();
      setPreview({
        title: d.original_name || "مرافعة",
        body: text || "—",
      });
    } catch {
      setPreview({
        title: d.original_name || "مرافعة",
        body: "تعذر التحميل.",
      });
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-2xl font-semibold text-sanad-navy" dir="rtl">
          مرافعات المكتب
        </h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">المحفوظات</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && <p className="text-sm text-slate-400">…</p>}
          {!loading && docs.length === 0 && (
            <p className="py-8 text-center text-sm text-slate-400">لا توجد مرافعات.</p>
          )}
          <ul className="divide-y divide-sanad-border">
            {docs.map((d) => (
              <li key={d.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <div>
                  <p className="font-medium text-sanad-navy">{d.original_name}</p>
                  <p className="text-xs text-slate-500">
                    {d.caseRef || "—"} ·{" "}
                    {new Date(d.created_at).toLocaleDateString("ar-MA")}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={busyId === d.id}
                  onClick={() => void openDoc(d)}
                >
                  {busyId === d.id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <FileText className="h-4 w-4" />
                  )}
                  عرض
                </Button>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {preview && (
        <Card className="border-sanad-gold/30">
          <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
            <CardTitle className="text-base">{preview.title}</CardTitle>
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                onClick={() =>
                  exportOfficialArabicDocument({
                    title: preview.title,
                    body: preview.body,
                    cabinetName: user?.cabinet_name,
                    lawyerName: user?.full_name,
                  })
                }
              >
                <Printer className="h-4 w-4" />
                PDF
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() =>
                  downloadOfficialArabicDoc({
                    title: preview.title,
                    body: preview.body,
                    cabinetName: user?.cabinet_name,
                    lawyerName: user?.full_name,
                  })
                }
              >
                <Download className="h-4 w-4" />
                DOC
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <textarea
              dir="rtl"
              lang="ar"
              readOnly
              className="min-h-[280px] w-full rounded-xl border border-sanad-border bg-sanad-cream/30 px-3 py-3 text-right text-sm leading-relaxed"
              value={preview.body}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
