"use client";

import { AppShell } from "@/components/layout/app-shell";
import { useLocaleStore } from "@/store/locale";

/** Placeholder priorité 5 — ne pas construire avant validation des 4 écrans. */
export default function DashboardPage() {
  const locale = useLocaleStore((s) => s.locale);
  const ar = locale === "ar";

  return (
    <AppShell>
      <div className="section-title">{ar ? "لوحة القيادة" : "Tableau de bord"}</div>
      <div className="section-sub">
        {ar
          ? "واجهة موجزة — تُبنى بعد التحقق من المرافعة والملفات والوثائق والتخطيط."
          : "Vue d’ensemble — à construire après validation des écrans prioritaires."}
      </div>
      <div
        className="card"
        style={{
          padding: 50,
          textAlign: "center",
          color: "var(--ink-soft)",
        }}
      >
        À construire après validation de Plaidoirie · Dossiers · Documents · Planning.
      </div>
    </AppShell>
  );
}
