"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { PLEA_DRAFT_RESTORE_KEY } from "@/components/redaction/template-picker";
import { useAuthStore } from "@/store/auth";
import { isAssistant } from "@/lib/roles";
import { useLocaleStore } from "@/store/locale";
import {
  ArrowLeft,
  CheckCircle2,
  Download,
  FileText,
  Mic,
  Printer,
  Trash2,
} from "lucide-react";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { PlaidoirieDocumentPreview } from "@/components/redaction/plaidoirie-document-preview";
import { exportOfficialArabicDocument } from "@/lib/export-official-doc";
import { api, type PlaidoirieDraftItem } from "@/lib/api";
import { PLAIDOIRIE_TEMPLATES } from "@/lib/plaidoirie-templates";
import { useCabinetEvent } from "@/hooks/use-cabinet-realtime";
import { useActionToast } from "@/store/action-toast";
import {
  clearPleaSession,
  hasMeaningfulPleaSession,
  loadPleaSession,
  pleaResumeHref,
  pleaSessionPreview,
} from "@/lib/plea-session";

export default function RedactionPage() {
  const user = useAuthStore((s) => s.user);
  return (
    <AppShell>
      {isAssistant(user?.role) ? <AssistantPleaLibrary /> : <LawyerPleaLibrary />}
    </AppShell>
  );
}

function formatDate(iso: string, locale: string) {
  try {
    return new Date(iso).toLocaleDateString(locale === "ar" ? "ar-MA" : "fr-FR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function initials(title: string) {
  const parts = (title || "?")
    .split(/\s+/)
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2);
  const joined = parts.join("");
  // Latin → uppercase; Arabic keeps original glyphs (toUpperCase is a no-op).
  return /[A-Za-z]/.test(joined) ? joined.toUpperCase() : joined;
}

/** Arabic titles must use dir=auto — truncate in LTR UI cuts the START of RTL text. */
function PleaTitle({ title, pinned, className }: { title: string; pinned?: boolean; className?: string }) {
  return (
    <p className={className ?? "line-clamp-2 break-words font-semibold text-[var(--ink)]"} dir="auto" title={title}>
      {pinned ? "📌 " : ""}
      {title}
    </p>
  );
}

/** Avocat / admin cabinet : liste type dossiers + détail (pas le wizard). */
function LawyerPleaLibrary() {
  const router = useRouter();
  const locale = useLocaleStore((s) => s.locale);
  const isAr = locale === "ar";
  const confirm = useConfirm();
  const user = useAuthStore((s) => s.user);
  const [items, setItems] = useState<PlaidoirieDraftItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "draft" | "validated" | "finalized">("all");
  const [period, setPeriod] = useState<"all" | "today" | "7d" | "30d">("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<PlaidoirieDraftItem | null>(null);
  const [busy, setBusy] = useState(false);
  const [exportBusy, setExportBusy] = useState(false);
  const [assistants, setAssistants] = useState<{ id: string; full_name: string }[]>([]);
  const [cases, setCases] = useState<{ id: string; reference: string; client_name: string }[]>([]);
  const [localDraft, setLocalDraft] = useState<{ preview: string; href: string } | null>(null);
  /** Multi-sélection liste (suppression sans ouvrir la fiche). */
  const [checkedIds, setCheckedIds] = useState<string[]>([]);
  const pushToast = useActionToast((s) => s.push);

  function dismissLocalDraft() {
    clearPleaSession();
    setLocalDraft(null);
  }

  const exportMeta = {
    cabinet_name: user?.cabinet_name || undefined,
    lawyer_name: user?.full_name_ar || user?.full_name || undefined,
    city: undefined as string | undefined,
  };

  async function exportWord(d: PlaidoirieDraftItem) {
    setExportBusy(true);
    try {
      await api.downloadPlaidoirieDocx({
        title: d.title,
        body: d.body,
        ...exportMeta,
      });
    } catch {
      /* silencieux — toast éventuel plus tard */
    } finally {
      setExportBusy(false);
    }
  }

  async function exportPdf(d: PlaidoirieDraftItem) {
    setExportBusy(true);
    try {
      await api.downloadPlaidoiriePdf({
        title: d.title,
        body: d.body,
        ...exportMeta,
      });
    } catch {
      /* silencieux */
    } finally {
      setExportBusy(false);
    }
  }

  const labels = isAr
    ? {
        title: "المرافعات",
        subtitle:
          "انقروا على مرافعة لفتح التفاصيل ثم القيام بالإجراءات (اعتماد، إسناد لمساعد، تصدير، حذف…).",
        statusLegend:
          "الحالات: مسودة = خاصة بالمحامي · معتمدة = ظاهرة للمساعدين · منتهية = بعد تصدير Word/PDF.",
        detailHint:
          "هنا: اعتماد للمساعد، إسناد إلى مساعد، ربط بملف، تصدير أو حذف.",
        new: "مرافعة جديدة",
        search: "بحث عن مرافعة…",
        all: "الكل",
        drafts: "مسودات",
        validated: "معتمدة",
        finalized: "منتهية",
        empty: "لا توجد مرافعة بعد.",
        draft: "مسودة",
        validatedBadge: "معتمدة",
        finalizedBadge: "منتهية",
        open: "فتح التفاصيل",
        back: "العودة للقائمة",
        case: "الملف",
        date: "آخر تحديث",
        validate: "اعتماد للمساعد",
        unvalidate: "إرجاع لمسودة",
        edit: "فتح الورشة",
        openStudio: "فتح الورشة",
        print: "طباعة",
        download: "Word",
        pdf: "PDF",
        delete: "حذف",
        noCase: "بدون ملف مرتبط",
        periodAll: "كل الفترة",
        periodToday: "اليوم",
        period7: "7 أيام",
        period30: "30 يوماً",
        assign: "إسناد إلى",
        pin: "تثبيت",
        unpin: "إلغاء التثبيت",
        shortcuts: "اختصارات: N = جديدة · V = اعتماد",
        selectAll: "تحديد الكل",
        deselectAll: "إلغاء التحديد",
        deleteSelected: "حذف المحدد",
        selectedCount: (n: number) => (n === 1 ? "1 محددة" : `${n} محددةات`),
        deleteSelectedTitle: "حذف المرافعات المحددة؟",
        deleteSelectedDesc: (n: number) =>
          `سيتم حذف ${n} مرافعة نهائياً (بما فيها المسودات) دون فتحها.`,
      }
    : {
        title: "Plaidoiries",
        subtitle:
          "Cliquez sur une plaidoirie pour ouvrir le détail et faire les actions (valider, assigner à un assistant, exporter, supprimer…).",
        statusLegend:
          "Statuts : Brouillon = visible seulement par l’avocat · Validée = visible par les assistants · Finalisée = après export Word/PDF.",
        detailHint:
          "Ici : valider pour l’assistant, assigner à un assistant, lier un dossier, exporter ou supprimer.",
        new: "Nouvelle plaidoirie",
        search: "Rechercher une plaidoirie…",
        all: "Toutes",
        drafts: "Brouillons",
        validated: "Validées",
        finalized: "Finalisées",
        empty: "Aucune plaidoirie.",
        draft: "Brouillon",
        validatedBadge: "Validée",
        finalizedBadge: "Finalisée",
        open: "Voir le détail",
        back: "Retour à la liste",
        case: "Dossier",
        date: "Dernière MAJ",
        validate: "Valider pour l’assistant",
        unvalidate: "Repasser en brouillon",
        edit: "Ouvrir l'atelier",
        openStudio: "Ouvrir l'atelier",
        print: "Imprimer",
        download: "Word",
        pdf: "PDF",
        delete: "Supprimer",
        noCase: "Sans dossier lié",
        periodAll: "Toute période",
        periodToday: "Aujourd’hui",
        period7: "7 jours",
        period30: "30 jours",
        assign: "Assigner à",
        pin: "Épingler",
        unpin: "Désépingler",
        linkCase: "Lier à un dossier",
        linkCaseNone: "Sans dossier",
        linkCaseNew: "Créer un nouveau dossier…",
        shortcuts: "Raccourcis : N = nouvelle · V = valider",
        selectAll: "Tout sélectionner",
        deselectAll: "Tout désélectionner",
        deleteSelected: "Supprimer la sélection",
        selectedCount: (n: number) => (n === 1 ? "1 sélectionnée" : `${n} sélectionnées`),
        deleteSelectedTitle: "Supprimer les plaidoiries sélectionnées ?",
        deleteSelectedDesc: (n: number) =>
          `${n} plaidoirie${n > 1 ? "s" : ""} seront définitivement supprimées (brouillons inclus), sans les ouvrir.`,
      };

  const reload = useCallback(() => {
    setLoading(true);
    api
      .listPlaidoirieDrafts()
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!hasMeaningfulPleaSession()) {
      setLocalDraft(null);
      return;
    }
    const snap = loadPleaSession();
    setLocalDraft({
      preview: pleaSessionPreview(110),
      href: pleaResumeHref(snap?.templateId || "libre"),
    });
  }, []);

  useEffect(() => {
    reload();
    api
      .listAssistants()
      .then((rows) => setAssistants(rows.map((r) => ({ id: r.id, full_name: r.full_name }))))
      .catch(() => setAssistants([]));
    api
      .getCases()
      .then((rows) =>
        setCases(rows.map((c) => ({ id: c.id, reference: c.reference, client_name: c.client_name }))),
      )
      .catch(() => setCases([]));
  }, [reload]);

  useCabinetEvent((data) => {
    const ev = String(data?.event || "");
    if (ev.startsWith("plaidoirie") || ev.startsWith("team")) {
      void reload();
    }
  });

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || (e.target as HTMLElement)?.isContentEditable) {
        return;
      }
      if (e.key.toLowerCase() === "n" && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        router.push("/redaction/new");
      }
      if (e.key.toLowerCase() === "v" && selected && selected.status !== "validated") {
        e.preventDefault();
        void onValidate(selected);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected, router]);

  const filtered = useMemo(() => {
    let list = items;
    if (filter === "draft") list = list.filter((i) => (i.status || "draft") === "draft");
    if (filter === "validated") list = list.filter((i) => i.status === "validated");
    if (filter === "finalized") list = list.filter((i) => i.status === "finalized");
    const now = Date.now();
    if (period === "today") {
      const start = new Date();
      start.setHours(0, 0, 0, 0);
      list = list.filter((i) => new Date(i.updated_at).getTime() >= start.getTime());
    } else if (period === "7d") {
      list = list.filter((i) => now - new Date(i.updated_at).getTime() <= 7 * 864e5);
    } else if (period === "30d") {
      list = list.filter((i) => now - new Date(i.updated_at).getTime() <= 30 * 864e5);
    }
    const q = search.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (i) =>
          i.title.toLowerCase().includes(q) ||
          (i.case_reference || "").toLowerCase().includes(q) ||
          (i.assigned_to_name || "").toLowerCase().includes(q) ||
          (i.template_id || "").toLowerCase().includes(q),
      );
    }
    if (typeFilter !== "all") {
      list = list.filter((i) => (i.template_id || "libre") === typeFilter);
    }
    return [...list].sort((a, b) => Number(!!b.pinned) - Number(!!a.pinned));
  }, [items, filter, search, period, typeFilter]);

  function openNew() {
    router.push("/redaction/new");
  }

  function openEdit(d: PlaidoirieDraftItem) {
    const tpl = d.template_id || "libre";
    try {
      sessionStorage.setItem(
        PLEA_DRAFT_RESTORE_KEY,
        JSON.stringify({
          title: d.title,
          body: d.body,
          case_id: d.case_id || "",
          checks: d.checks || [],
          template_id: tpl,
          draft_id: d.id,
          resume_step: 3,
        }),
      );
    } catch {
      /* ignore */
    }
    // Hard navigation : même template_id sinon Next ne remonte pas l'atelier
    window.location.assign(
      `/redaction/${encodeURIComponent(tpl)}?draft=${encodeURIComponent(d.id)}`,
    );
  }

  async function onValidate(d: PlaidoirieDraftItem) {
    const prev = d;
    const optimistic = { ...d, status: "validated" as const };
    setItems((list) => list.map((x) => (x.id === d.id ? optimistic : x)));
    setSelected(optimistic);
    setBusy(true);
    try {
      const updated = await api.validatePlaidoirieDraft(d.id);
      setItems((list) => list.map((x) => (x.id === d.id ? updated : x)));
      setSelected(updated);
    } catch {
      setItems((list) => list.map((x) => (x.id === d.id ? prev : x)));
      setSelected(prev);
    } finally {
      setBusy(false);
    }
  }

  async function onUnvalidate(d: PlaidoirieDraftItem) {
    setBusy(true);
    try {
      const updated = await api.unvalidatePlaidoirieDraft(d.id);
      setItems((prev) => prev.map((x) => (x.id === d.id ? updated : x)));
      setSelected(updated);
    } catch {
      /* keep previous state — avoid Next.js Unhandled Runtime Error overlay */
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(d: PlaidoirieDraftItem) {
    const ok = await confirm({
      title: isAr ? "حذف المرافعة" : "Supprimer la plaidoirie",
      description: isAr
        ? "سيتم حذف هذه المرافعة نهائياً."
        : "Cette plaidoirie sera définitivement supprimée.",
      tone: "danger",
      deleteVisual: "document",
    });
    if (!ok) return;
    setBusy(true);
    try {
      await api.deletePlaidoirieDraft(d.id);
      setItems((prev) => prev.filter((x) => x.id !== d.id));
      setCheckedIds((prev) => prev.filter((id) => id !== d.id));
      if (selected?.id === d.id) setSelected(null);
      // Brouillon local fantôme : si on nettoie les brouillons serveur, on retire aussi l’atelier local.
      if ((d.status || "draft") === "draft") {
        dismissLocalDraft();
      }
      pushToast(
        isAr ? "تم حذف المرافعة بنجاح." : "Plaidoirie supprimée avec succès.",
        "success",
      );
    } catch (e) {
      pushToast(
        e instanceof Error
          ? e.message
          : isAr
            ? "تعذّر الحذف."
            : "Suppression impossible.",
        "error",
      );
    } finally {
      setBusy(false);
    }
  }

  function toggleChecked(id: string) {
    setCheckedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  function selectAllVisible() {
    setCheckedIds(filtered.map((d) => d.id));
  }

  function clearSelection() {
    setCheckedIds([]);
  }

  async function onDeleteSelected() {
    const ids = checkedIds.filter((id) => filtered.some((d) => d.id === id));
    if (ids.length === 0) return;
    const ok = await confirm({
      title: labels.deleteSelectedTitle,
      description: labels.deleteSelectedDesc(ids.length),
      tone: "danger",
      deleteVisual: "document",
      confirmLabel: labels.deleteSelected,
    });
    if (!ok) return;
    setBusy(true);
    const failed: string[] = [];
    for (const id of ids) {
      try {
        await api.deletePlaidoirieDraft(id);
      } catch {
        failed.push(id);
      }
    }
    const removed = new Set(ids.filter((id) => !failed.includes(id)));
    const removedCount = removed.size;
    setItems((prev) => prev.filter((x) => !removed.has(x.id)));
    setCheckedIds(failed);
    if (selected && removed.has(selected.id)) setSelected(null);
    setBusy(false);
    if (removedCount > 0) {
      // Nettoyage multi : retire aussi le brouillon local (sinon bandeau « non terminé » fantôme).
      dismissLocalDraft();
      pushToast(
        isAr
          ? removedCount === 1
            ? "تم حذف المرافعة بنجاح."
            : `تم حذف ${removedCount} مرافعات بنجاح.`
          : removedCount === 1
            ? "Plaidoirie supprimée avec succès."
            : `${removedCount} plaidoiries supprimées avec succès.`,
        "success",
      );
    }
    if (failed.length > 0) {
      pushToast(
        isAr
          ? `تعذّر حذف ${failed.length} مرافعة — بقيت محددة.`
          : `${failed.length} plaidoirie(s) non supprimée(s) — elles restent sélectionnées.`,
        "error",
      );
    }
  }

  function printPlea(d: PlaidoirieDraftItem) {
    void exportOfficialArabicDocument({
      title: d.title,
      body: d.body,
      cabinetName: user?.cabinet_name,
      lawyerName: user?.full_name_ar || user?.full_name,
      autoPrint: true,
    });
  }

  if (selected) {
    const st = selected.status || "draft";
    const badgeLabel =
      st === "finalized"
        ? labels.finalizedBadge
        : st === "validated"
          ? labels.validatedBadge
          : labels.draft;
    const badgeClass =
      st === "finalized"
        ? "rounded-full bg-sky-50 px-2.5 py-0.5 text-xs font-semibold text-sky-900"
        : st === "validated"
          ? "rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-800"
          : "rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-800";
    const validated = st === "validated";
    return (
      <div className="space-y-4" dir={isAr ? "rtl" : "ltr"}>
        <button
          type="button"
          className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--ink-soft)] hover:text-[var(--ink)]"
          onClick={() => setSelected(null)}
        >
          <ArrowLeft className="h-4 w-4" />
          {labels.back}
        </button>

        <div className="rounded-2xl border border-[var(--line)] bg-white/80 p-5 shadow-sm backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-xl font-bold text-[var(--ink)]" dir="auto">
                  {selected.title}
                </h1>
                <span className={badgeClass}>{badgeLabel}</span>
              </div>
              <dl className="mt-3 grid gap-1 text-sm text-[var(--ink-soft)] sm:grid-cols-2">
                <div>
                  <dt className="text-xs uppercase tracking-wide opacity-70">{labels.case}</dt>
                  <dd className="font-mono text-[var(--ink)]">
                    {selected.case_reference || labels.noCase}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wide opacity-70">{labels.date}</dt>
                  <dd>{formatDate(selected.updated_at, locale)}</dd>
                </div>
              </dl>
              <p className="mt-3 text-xs leading-relaxed text-[var(--ink-soft)]">
                {labels.detailHint}
              </p>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {!validated ? (
              <button
                type="button"
                className="chip-btn primary inline-flex items-center gap-1.5"
                disabled={busy}
                onClick={() => void onValidate(selected)}
              >
                <CheckCircle2 className="h-4 w-4" />
                {labels.validate}
              </button>
            ) : (
              <button
                type="button"
                className="chip-btn inline-flex items-center gap-1.5"
                disabled={busy}
                onClick={() => void onUnvalidate(selected)}
              >
                {labels.unvalidate}
              </button>
            )}
            {cases.length > 0 ? (
              <select
                className="rounded-xl border border-[var(--line)] bg-white px-3 py-2 text-sm"
                value={selected.case_id || ""}
                onChange={(e) => {
                  const v = e.target.value;
                  if (v === "__new__") {
                    router.push("/cases/new");
                    return;
                  }
                  void api
                    .updatePlaidoirieDraftCase(selected.id, v || null)
                    .then((u) => {
                      setItems((prev) => prev.map((x) => (x.id === u.id ? u : x)));
                      setSelected(u);
                    })
                    .catch(() => {});
                }}
              >
                <option value="">{labels.linkCaseNone}</option>
                {cases.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.reference} — {c.client_name}
                  </option>
                ))}
                <option value="__new__">{labels.linkCaseNew}</option>
              </select>
            ) : null}
            <button
              type="button"
              className="chip-btn"
              disabled={busy}
              onClick={() =>
                void api
                  .pinPlaidoirieDraft(selected.id)
                  .then((u) => {
                    setItems((prev) => prev.map((x) => (x.id === u.id ? u : x)));
                    setSelected(u);
                  })
                  .catch(() => {})
              }
            >
              {selected.pinned ? labels.unpin : labels.pin}
            </button>
            {assistants.length > 0 ? (
              <select
                className="rounded-xl border border-[var(--line)] bg-white px-3 py-2 text-sm"
                value={selected.assigned_to_user_id || ""}
                onChange={(e) => {
                  const uid = e.target.value || null;
                  void api
                    .assignPlaidoirieDraft(selected.id, uid)
                    .then((u) => {
                      setItems((prev) => prev.map((x) => (x.id === u.id ? u : x)));
                      setSelected(u);
                    })
                    .catch(() => {});
                }}
              >
                <option value="">{labels.assign}…</option>
                {assistants.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.full_name}
                  </option>
                ))}
              </select>
            ) : null}
            <button type="button" className="chip-btn primary" onClick={() => openEdit(selected)}>
              {labels.edit}
            </button>
            <button
              type="button"
              className="chip-btn inline-flex items-center gap-1.5"
              onClick={() => printPlea(selected)}
            >
              <Printer className="h-4 w-4" />
              {labels.print}
            </button>
            <button
              type="button"
              className="chip-btn inline-flex items-center gap-1.5"
              disabled={exportBusy}
              onClick={() => void exportWord(selected)}
            >
              <Download className="h-4 w-4" />
              {labels.download}
            </button>
            <button
              type="button"
              className="chip-btn inline-flex items-center gap-1.5 text-red-700"
              disabled={busy}
              onClick={() => void onDelete(selected)}
            >
              <Trash2 className="h-4 w-4" />
              {labels.delete}
            </button>
          </div>

          <PlaidoirieDocumentPreview
            title={selected.title}
            body={selected.body}
            cabinetName={user?.cabinet_name}
            lawyerName={user?.full_name_ar || user?.full_name}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5 plea-library" dir={isAr ? "rtl" : "ltr"}>
      <div className="plea-library__head flex flex-wrap items-end justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-bold text-[var(--ink)] max-md:text-xl">{labels.title}</h1>
          <p className="mt-1 max-w-2xl text-sm text-[var(--ink-soft)] max-md:text-xs">{labels.subtitle}</p>
          <p
            className="mt-2 max-w-2xl rounded-xl border border-[var(--line)] bg-white/70 px-3 py-2 text-xs leading-relaxed text-[var(--ink)] max-md:text-[11px]"
            style={{ borderColor: "rgba(15, 76, 129, 0.18)" }}
          >
            {labels.statusLegend}
          </p>
        </div>
        <button type="button" className="chip-btn primary inline-flex items-center gap-2 max-md:w-full max-md:justify-center" onClick={openNew}>
          <Mic className="h-4 w-4" />
          {labels.new}
        </button>
      </div>
      {localDraft ? (
        <div
          className="rounded-2xl border px-4 py-3"
          style={{
            borderColor: "rgba(180, 83, 9, 0.35)",
            background: "rgba(255, 247, 237, 0.95)",
          }}
        >
          <p style={{ margin: 0, fontSize: 13, fontWeight: 650, color: "#9a3412" }}>
            {isAr
              ? "مسودة محلية على هذا الجهاز (ليست من قائمة المرافعات). احذفوها إن لم تعودوا بحاجة إليها."
              : "Brouillon local sur cet appareil (pas la liste serveur). Effacez-le s’il ne vous sert plus — même après suppression des plaidoiries de la liste."}
          </p>
          {localDraft.preview ? (
            <p
              className="mt-1 text-sm text-[var(--ink)]"
              dir="auto"
              style={{ marginBottom: 0, opacity: 0.9 }}
            >
              {localDraft.preview}
            </p>
          ) : null}
                    <button
                      type="button"
            className="chip-btn mt-3"
            onClick={() => router.push(localDraft.href)}
                    >
            {isAr ? "استئناف هذه المسودة" : "Reprendre ce brouillon"}
                    </button>
                    <button
                      type="button"
            className="chip-btn mt-3 ms-2"
                      onClick={() => {
              dismissLocalDraft();
              pushToast(
                isAr ? "تم مسح المسودة المحلية." : "Brouillon local effacé.",
                "success",
              );
            }}
          >
            {isAr ? "تجاهل المسودة المحلية" : "Effacer le brouillon local"}
          </button>
        </div>
      ) : null}

      <div className="plea-library__filters">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={labels.search}
          className="plea-library__search rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2 text-sm outline-none focus:border-[var(--royal-700)]"
        />
        <div className="plea-library__chips" role="tablist" aria-label={isAr ? "حالة المرافعة" : "Statut"}>
          {(
            [
              ["all", labels.all],
              ["draft", labels.drafts],
              ["validated", labels.validated],
              ["finalized", labels.finalized],
            ] as const
          ).map(([k, lab]) => (
            <button
              key={k}
              type="button"
              className={filter === k ? "chip-btn primary" : "chip-btn"}
              onClick={() => setFilter(k)}
            >
              {lab}
            </button>
          ))}
        </div>
        <div className="plea-library__selects">
          <select
            className="rounded-xl border border-[var(--line)] bg-white px-3 py-2 text-sm"
            value={period}
            onChange={(e) => setPeriod(e.target.value as typeof period)}
          >
            <option value="all">{labels.periodAll}</option>
            <option value="today">{labels.periodToday}</option>
            <option value="7d">{labels.period7}</option>
            <option value="30d">{labels.period30}</option>
          </select>
          <select
            className="rounded-xl border border-[var(--line)] bg-white px-3 py-2 text-sm"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            title={isAr ? "نوع المرافعة" : "Type de plaidoirie"}
          >
            <option value="all">{isAr ? "كل الأنواع" : "Tous les types"}</option>
            {PLAIDOIRIE_TEMPLATES.map((tpl) => (
              <option key={tpl.id} value={tpl.id}>
                {isAr ? tpl.labelAr : tpl.labelFr}
              </option>
            ))}
          </select>
        </div>
      </div>
      <p className="text-xs text-[var(--ink-soft)] max-md:hidden">{labels.shortcuts}</p>

      {!loading && filtered.length > 0 ? (
        <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-[var(--line)] bg-white/70 px-3 py-2.5">
          <label className="inline-flex cursor-pointer items-center gap-2 text-sm font-medium text-[var(--ink)]">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-[var(--line)] accent-[var(--royal-800)]"
              checked={filtered.length > 0 && filtered.every((d) => checkedIds.includes(d.id))}
              ref={(el) => {
                if (!el) return;
                const n = filtered.filter((d) => checkedIds.includes(d.id)).length;
                el.indeterminate = n > 0 && n < filtered.length;
              }}
              onChange={(e) => {
                if (e.target.checked) selectAllVisible();
                else clearSelection();
              }}
            />
            {labels.selectAll}
          </label>
          {checkedIds.length > 0 ? (
            <>
              <span className="text-xs font-semibold text-[var(--ink-soft)]">
                {labels.selectedCount(checkedIds.filter((id) => filtered.some((d) => d.id === id)).length)}
              </span>
              <button type="button" className="chip-btn" disabled={busy} onClick={clearSelection}>
                {labels.deselectAll}
                    </button>
                    <button
                      type="button"
                className="chip-btn inline-flex items-center gap-1.5 text-red-700"
                      disabled={busy}
                onClick={() => void onDeleteSelected()}
              >
                <Trash2 className="h-3.5 w-3.5" />
                {labels.deleteSelected}
              </button>
            </>
          ) : null}
        </div>
      ) : null}

      {loading ? (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="lexhub-skel h-28 rounded-2xl" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[var(--line)] bg-white/50 p-8 text-center text-sm text-[var(--ink-soft)]">
          <p>{labels.empty}</p>
          <button type="button" className="chip-btn primary mt-4 inline-flex items-center gap-2" onClick={openNew}>
            <Mic className="h-4 w-4" />
            {labels.new}
                    </button>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {filtered.map((d) => {
            const st = d.status || "draft";
            const badgeLabel =
              st === "finalized"
                ? labels.finalizedBadge
                : st === "validated"
                  ? labels.validatedBadge
                  : labels.draft;
            const badgeClass =
              st === "finalized"
                ? "shrink-0 rounded-full bg-sky-50 px-2 py-0.5 text-[10px] font-bold text-sky-900"
                : st === "validated"
                  ? "shrink-0 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-800"
                  : "shrink-0 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-bold text-amber-800";
            const isChecked = checkedIds.includes(d.id);
            return (
              <div
                key={d.id}
                className={`group relative rounded-2xl border bg-white/80 p-4 text-start shadow-sm transition hover:-translate-y-0.5 hover:shadow-md ${
                  isChecked
                    ? "border-[var(--royal-700)] ring-2 ring-[var(--royal-700)]/20"
                    : "border-[var(--line)]"
                }`}
              >
                <label
                  className="absolute start-3 top-3 z-10 flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg bg-white/95 shadow-sm"
                  onClick={(e) => e.stopPropagation()}
                  onKeyDown={(e) => e.stopPropagation()}
                >
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-[var(--line)] accent-[var(--royal-800)]"
                    checked={isChecked}
                    onChange={() => toggleChecked(d.id)}
                    aria-label={isAr ? "تحديد المرافعة" : "Sélectionner la plaidoirie"}
                  />
                </label>
                    <button
                      type="button"
                  onClick={() => setSelected(d)}
                  className="w-full text-start"
                >
                  <div className="flex items-start gap-3 ps-8">
                    <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--royal-900)] text-xs font-bold text-white">
                      {initials(d.title)}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <PleaTitle
                          title={d.title}
                          pinned={!!d.pinned}
                          className="min-w-0 flex-1 line-clamp-2 break-words font-semibold text-[var(--ink)]"
                        />
                        <span className={badgeClass}>{badgeLabel}</span>
                      </div>
                      <p className="mt-1 font-mono text-xs text-[var(--ink-soft)]">
                        {d.case_reference || labels.noCase}
                      </p>
                      {d.assigned_to_name ? (
                        <p className="mt-1 text-xs text-[var(--royal-700)]">@{d.assigned_to_name}</p>
                      ) : null}
                      <p className="mt-1 text-xs text-[var(--ink-soft)]">
                        {formatDate(d.updated_at, locale)}
                      </p>
                    </div>
                  </div>
                </button>
              </div>
              );
            })}
        </div>
        )}
    </div>
  );
}

/** Assistant : uniquement validées + impression / téléchargement. */
function AssistantPleaLibrary() {
  const locale = useLocaleStore((s) => s.locale);
  const isAr = locale === "ar";
  const user = useAuthStore((s) => s.user);
  const [items, setItems] = useState<PlaidoirieDraftItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<PlaidoirieDraftItem | null>(null);
  const [search, setSearch] = useState("");
  const [period, setPeriod] = useState<"all" | "today" | "7d" | "30d">("all");
  const [exportBusy, setExportBusy] = useState(false);

  const exportMeta = {
    cabinet_name: user?.cabinet_name || undefined,
    lawyer_name: user?.full_name_ar || user?.full_name || undefined,
  };

  async function exportWord(d: PlaidoirieDraftItem) {
    setExportBusy(true);
    try {
      await api.downloadPlaidoirieDocx({
        title: d.title,
        body: d.body,
        ...exportMeta,
      });
    } catch {
      /* ignore */
    } finally {
      setExportBusy(false);
    }
  }

  async function exportPdf(d: PlaidoirieDraftItem) {
    setExportBusy(true);
    try {
      await api.downloadPlaidoiriePdf({
        title: d.title,
        body: d.body,
        ...exportMeta,
      });
    } catch {
      /* ignore */
    } finally {
      setExportBusy(false);
    }
  }

  const labels = isAr
    ? {
        title: "مرافعات معتمدة",
        subtitle:
          "انقروا على مرافعة لفتحها ثم الطباعة أو التحميل. تظهر هنا فقط ما اعتمده المحامي (معتمدة أو منتهية).",
        empty: "لا توجد مرافعة معتمدة بعد. عندما يعتمد المحامي مرافعة، تظهر هنا.",
        back: "العودة",
        case: "الملف",
        date: "التاريخ",
        print: "طباعة",
        word: "Word",
        pdf: "PDF",
        noCase: "بدون ملف",
        search: "بحث…",
        periodAll: "كل الفترة",
        periodToday: "اليوم",
        period7: "7 أيام",
        period30: "30 يوماً",
      }
    : {
        title: "Plaidoiries validées",
        subtitle:
          "Cliquez sur une plaidoirie pour l’ouvrir, puis imprimer ou télécharger. Seules les plaidoiries validées ou finalisées par l’avocat apparaissent ici.",
        empty:
          "Aucune plaidoirie validée. Dès que l’avocat valide une plaidoirie, elle apparaît ici.",
        back: "Retour",
        case: "Dossier",
        date: "Date",
        print: "Imprimer",
        word: "Word",
        pdf: "PDF",
        noCase: "Sans dossier",
        search: "Rechercher…",
        periodAll: "Toute période",
        periodToday: "Aujourd’hui",
        period7: "7 jours",
        period30: "30 jours",
      };

  useEffect(() => {
    api
      .listPlaidoirieDrafts()
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  // Filet de sécurité : refresh périodique si le WS rate un événement
  useEffect(() => {
    const tick = () => {
      if (document.visibilityState !== "visible") return;
      void api
        .listPlaidoirieDrafts()
        .then(setItems)
        .catch(() => undefined);
    };
    const id = window.setInterval(tick, 8000);
    window.addEventListener("focus", tick);
    return () => {
      window.clearInterval(id);
      window.removeEventListener("focus", tick);
    };
  }, []);

  useCabinetEvent((data) => {
    const ev = data?.event || "";
    if (
      ev === "plaidoirie.validated" ||
      ev === "plaidoirie.unvalidated" ||
      ev.startsWith("plaidoirie")
    ) {
      void api
        .listPlaidoirieDrafts()
        .then(setItems)
        .catch(() => undefined);
    }
  });

  const filtered = useMemo(() => {
    let list = items;
    const now = Date.now();
    if (period === "today") {
      const start = new Date();
      start.setHours(0, 0, 0, 0);
      list = list.filter((i) => new Date(i.updated_at).getTime() >= start.getTime());
    } else if (period === "7d") {
      list = list.filter((i) => now - new Date(i.updated_at).getTime() <= 7 * 864e5);
    } else if (period === "30d") {
      list = list.filter((i) => now - new Date(i.updated_at).getTime() <= 30 * 864e5);
    }
    const q = search.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (i) =>
          i.title.toLowerCase().includes(q) ||
          (i.case_reference || "").toLowerCase().includes(q),
      );
    }
    return [...list].sort((a, b) => Number(!!b.pinned) - Number(!!a.pinned));
  }, [items, search, period]);

  function printPlea(d: PlaidoirieDraftItem) {
    void exportOfficialArabicDocument({
      title: d.title,
      body: d.body,
      cabinetName: user?.cabinet_name,
      lawyerName: user?.full_name_ar || user?.full_name,
      autoPrint: true,
    });
  }

  if (selected) {
  return (
      <div className="space-y-4" dir={isAr ? "rtl" : "ltr"}>
              <button
                type="button"
          className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--ink-soft)]"
          onClick={() => setSelected(null)}
        >
          <ArrowLeft className="h-4 w-4" />
          {labels.back}
              </button>
        <div className="rounded-2xl border border-[var(--line)] bg-white/80 p-5 shadow-sm">
          <h1 className="text-xl font-bold text-[var(--ink)]" dir="auto">
            {selected.title}
          </h1>
          <dl className="mt-3 grid gap-1 text-sm text-[var(--ink-soft)] sm:grid-cols-2">
            <div>
              <dt className="text-xs uppercase opacity-70">{labels.case}</dt>
              <dd className="font-mono text-[var(--ink)]">
                {selected.case_reference || labels.noCase}
              </dd>
            </div>
            <div>
              <dt className="text-xs uppercase opacity-70">{labels.date}</dt>
              <dd>{formatDate(selected.updated_at, locale)}</dd>
            </div>
          </dl>
          <div className="mt-4 flex flex-wrap gap-2">
                  <button
                    type="button"
              className="chip-btn primary inline-flex items-center gap-1.5"
              onClick={() => printPlea(selected)}
            >
              <Printer className="h-4 w-4" />
              {labels.print}
                  </button>
                  <button
                    type="button"
              className="chip-btn inline-flex items-center gap-1.5"
              disabled={exportBusy}
              onClick={() => void exportWord(selected)}
            >
              <Download className="h-4 w-4" />
              {labels.word}
                  </button>
          </div>
          <PlaidoirieDocumentPreview
            title={selected.title}
            body={selected.body}
            cabinetName={user?.cabinet_name}
            lawyerName={user?.full_name_ar || user?.full_name}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5" dir={isAr ? "rtl" : "ltr"}>
      <div>
        <h1 className="text-2xl font-bold text-[var(--ink)]">{labels.title}</h1>
        <p className="mt-1 max-w-xl text-sm text-[var(--ink-soft)]">{labels.subtitle}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={labels.search}
          className="min-w-[200px] flex-1 rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2 text-sm outline-none focus:border-[var(--royal-700)]"
        />
        <select
          className="rounded-xl border border-[var(--line)] bg-white px-3 py-2 text-sm"
          value={period}
          onChange={(e) => setPeriod(e.target.value as typeof period)}
        >
          <option value="all">{labels.periodAll}</option>
          <option value="today">{labels.periodToday}</option>
          <option value="7d">{labels.period7}</option>
          <option value="30d">{labels.period30}</option>
        </select>
      </div>
      {loading ? (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="lexhub-skel h-28 rounded-2xl" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[var(--line)] bg-white/50 p-8 text-center text-sm text-[var(--ink-soft)]">
          {labels.empty}
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {filtered.map((d) => (
            <button
              key={d.id}
              type="button"
              onClick={() => setSelected(d)}
              className="rounded-2xl border border-[var(--line)] bg-white/80 p-4 text-start shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <div className="flex items-start gap-3">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-700 text-xs font-bold text-white">
                  {initials(d.title)}
                </span>
                <div className="min-w-0 flex-1">
                  <PleaTitle title={d.title} pinned={!!d.pinned} />
                  <p className="mt-1 font-mono text-xs text-[var(--ink-soft)]">
                    {d.case_reference || labels.noCase}
                  </p>
                  <p className="mt-1 text-xs text-[var(--ink-soft)]">
                    {formatDate(d.updated_at, locale)}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
