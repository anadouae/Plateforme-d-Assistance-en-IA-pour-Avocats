"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Download } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { api, type ActivityArchiveItem, type WorkspaceActivityItem } from "@/lib/api";
import { useLocaleStore } from "@/store/locale";

export default function ActivityPage() {
  const locale = useLocaleStore((s) => s.locale);
  const ar = locale === "ar";
  const [items, setItems] = useState<WorkspaceActivityItem[]>([]);
  const [archives, setArchives] = useState<ActivityArchiveItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    function load() {
      Promise.all([
        api.workspaceActivity(50).catch(() => [] as WorkspaceActivityItem[]),
        api.listActivityArchives().catch(() => [] as ActivityArchiveItem[]),
      ])
        .then(([feed, arch]) => {
          setItems(feed);
          setArchives(arch);
        })
        .finally(() => setLoading(false));
    }
    load();
    function onRt() {
      load();
    }
    window.addEventListener("lexhub-cabinet-event", onRt);
    return () => window.removeEventListener("lexhub-cabinet-event", onRt);
  }, []);

  return (
    <AppShell>
      <div className="space-y-6" dir={ar ? "rtl" : "ltr"}>
        <div>
          <h1 className="text-2xl font-bold text-[var(--ink)]">
            {ar ? "نشاط المكتب" : "Activité du cabinet"}
          </h1>
          <p className="mt-1 text-sm text-[var(--ink-soft)]">
            {ar
              ? "مرئي للفريق كله — اعتمادات، تصديرات، ملفات… الأقدم من 90 يوماً يُؤرشف في Excel."
              : "Visible pour tout le cabinet — validations, exports, dossiers… Au-delà de 90 jours, archive Excel automatique."}
          </p>
        </div>

        {loading ? (
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="lexhub-skel h-14 rounded-xl" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <p className="text-sm text-[var(--ink-soft)]">
            {ar ? "لا نشاط بعد." : "Aucune activité pour l’instant."}
          </p>
        ) : (
          <ul className="space-y-2">
            {items.map((it) => (
              <li key={it.id}>
                <Link
                  href={it.href || "#"}
                  className="block rounded-xl border border-[var(--line)] bg-white/80 px-4 py-3 transition hover:shadow-sm"
                >
                  <p className="text-sm text-[var(--ink)]">
                    <strong>{it.actor_name || (ar ? "عضو" : "Membre")}</strong>{" "}
                    {it.label}
                    {it.details ? (
                      <span className="text-[var(--ink-soft)]"> — {it.details}</span>
                    ) : null}
                  </p>
                  <p className="mt-1 text-xs text-[var(--ink-soft)]">
                    {new Date(it.created_at).toLocaleString(ar ? "ar-MA" : "fr-FR")}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        )}

        <section className="rounded-2xl border border-[var(--line)] bg-white/70 p-4">
          <h2 className="text-base font-semibold text-[var(--ink)]">
            {ar ? "أرشيف Excel" : "Archives Excel"}
          </h2>
          <p className="mt-1 text-xs text-[var(--ink-soft)]">
            {ar
              ? "تُحفظ الآثار ثم يُفرَّغ الشريط المباشر — يمكنكم تنزيل الملفات هنا."
              : "Les traces sont conservées, le fil live est allégé — téléchargez les fichiers ici."}
          </p>
          {archives.length === 0 ? (
            <p className="mt-3 text-sm text-[var(--ink-soft)]">
              {ar ? "لا أرشيف بعد." : "Aucune archive pour l’instant."}
            </p>
          ) : (
            <ul className="mt-3 space-y-2">
              {archives.map((a) => (
                <li
                  key={a.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-[var(--line)] bg-white px-3 py-2.5"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-[var(--ink)]">{a.filename}</p>
                    <p className="text-xs text-[var(--ink-soft)]">
                      {a.row_count} {ar ? "سطر" : "lignes"} ·{" "}
                      {new Date(a.period_start).toLocaleDateString(ar ? "ar-MA" : "fr-FR")} →{" "}
                      {new Date(a.period_end).toLocaleDateString(ar ? "ar-MA" : "fr-FR")}
                    </p>
                  </div>
                  <button
                    type="button"
                    className="chip-btn inline-flex items-center gap-1.5"
                    onClick={() => void api.downloadActivityArchive(a.id, a.filename)}
                  >
                    <Download className="h-4 w-4" />
                    {ar ? "تحميل" : "Télécharger"}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </AppShell>
  );
}
