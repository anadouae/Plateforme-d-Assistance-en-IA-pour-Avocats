"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
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
  return (
    <AppShell>
      {isAssistant(user?.role) ? <AssistantPlaidoirieView /> : <LawyerTemplateHub />}
    </AppShell>
  );
}

/** Même parcours qu’avant : picker → /redaction/[templateId]. */
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
    <TemplatePicker
      systemTemplates={PLAIDOIRIE_TEMPLATES}
      customTemplates={customTemplates}
      onSelect={(id) => router.push(`/redaction/${encodeURIComponent(id)}`)}
      onDeleteCustom={(id) => void handleDeleteCustom(id)}
    />
  );
}

function AssistantPlaidoirieView() {
  const [docs, setDocs] = useState<(DocumentItem & { caseRef?: string })[]>([]);
  const [loading, setLoading] = useState(true);
  const [preview, setPreview] = useState<{ title: string; body: string } | null>(null);

  useEffect(() => {
    async function load() {
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
              name.includes("marafa")
            ) {
              all.push({ ...d, caseRef: c.reference });
            }
          }
        }
        setDocs(all);
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  if (loading) {
    return <p className="py-10 text-center text-sm text-[var(--ink-soft)]">…</p>;
  }

  return (
    <div className="space-y-4" dir="rtl">
      <h1 className="font-display text-2xl font-medium text-[var(--ink)]">مرافعة</h1>
      <p className="text-sm text-[var(--ink-soft)]">وثائق المرافعة المتاحة للتصدير</p>
      {docs.length === 0 ? (
        <p className="text-sm text-[var(--ink-soft)]">لا توجد مرافعات محفوظة بعد.</p>
      ) : (
        docs.map((d) => (
          <div
            key={d.id}
            className="rounded-2xl border border-[var(--line)] bg-white/70 p-4 backdrop-blur"
          >
            <p className="font-semibold">{d.original_name}</p>
            <p className="font-mono text-xs text-[var(--ink-soft)]">{d.caseRef}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                className="chip-btn"
                onClick={() => {
                  api.getDocument(d.id).then((full) => {
                    setPreview({
                      title: d.original_name,
                      body: full.extracted_text_preview || "",
                    });
                  });
                }}
              >
                معاينة
              </button>
              {preview?.title === d.original_name && (
                <>
                  <button
                    type="button"
                    className="chip-btn primary"
                    onClick={() =>
                      exportOfficialArabicDocument({
                        title: preview.title,
                        body: preview.body,
                      })
                    }
                  >
                    PDF
                  </button>
                  <button
                    type="button"
                    className="chip-btn"
                    onClick={() =>
                      void downloadOfficialArabicDoc({
                        title: preview.title,
                        body: preview.body,
                      })
                    }
                  >
                    Word
                  </button>
                </>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
