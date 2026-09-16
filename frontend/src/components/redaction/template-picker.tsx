"use client";

import { useEffect, useId, useMemo, useState } from "react";
import {
  ChevronDown,
  Download,
  FileEdit,
  FileText,
  History,
  Trash2,
  X,
} from "lucide-react";
import {
  api,
  type CabinetPlaidoirieTemplate,
  type PlaidoirieDraftItem,
} from "@/lib/api";
import {
  FEATURED_PLAIDOIRIE_IDS,
  type PlaidoirieTemplate,
} from "@/lib/plaidoirie-templates";
import { CASE_DOMAIN_META, type CaseDomain } from "@/lib/case-domains";
import { useLocaleStore } from "@/store/locale";
import { useActionToast } from "@/store/action-toast";
import { clearPleaSession } from "@/lib/plea-session";
import { cn } from "@/lib/utils";

export const PLEA_DRAFT_RESTORE_KEY = "lexhub_plea_draft_restore";
export const PLEA_DRAFT_RESTORE_KEY_LEGACY = "sanad_plea_draft_restore";

type Props = {
  systemTemplates: PlaidoirieTemplate[];
  customTemplates: CabinetPlaidoirieTemplate[];
  onSelect: (id: string) => void;
  onDeleteCustom: (id: string) => void;
};

type CardItem = {
  kind: "system" | "custom";
  id: string;
  title: string;
  subtitle: string;
  body: string;
};

/**
 * Parcours avocat :
 * 1) Choisir la matière / le domaine (civil, famille, pénal…)
 * 2) Choisir le type de plaidoirie adapté (oriente l’IA : rôles, sections, tribunal)
 * « Libre » reste disponible en option secondaire — pas comme écran d’entrée.
 */
export function TemplatePicker({
  systemTemplates,
  customTemplates,
  onSelect,
  onDeleteCustom,
}: Props) {
  const locale = useLocaleStore((s) => s.locale);
  const isAr = locale === "ar";
  const [modalId, setModalId] = useState<string | null>(null);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [showOthers, setShowOthers] = useState(false);
  const [domainFilter, setDomainFilter] = useState<string | "all">("all");
  const [drafts, setDrafts] = useState<PlaidoirieDraftItem[]>([]);
  const [draftsLoading, setDraftsLoading] = useState(true);
  const [draftBusyId, setDraftBusyId] = useState<string | null>(null);
  const titleId = useId();
  const pushToast = useActionToast((s) => s.push);

  useEffect(() => {
    let cancelled = false;
    setDraftsLoading(true);
    api
      .listPlaidoirieDrafts()
      .then((rows) => {
        if (!cancelled) setDrafts(rows);
      })
      .catch(() => {
        if (!cancelled) setDrafts([]);
      })
      .finally(() => {
        if (!cancelled) setDraftsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const featuredOrder = FEATURED_PLAIDOIRIE_IDS as readonly string[];

  const domainChips = useMemo(() => {
    const keys = Object.keys(CASE_DOMAIN_META) as Exclude<CaseDomain, "Autre">[];
    return keys;
  }, []);

  const matchesDomain = (tpl: PlaidoirieTemplate, filter: string) => {
    if (filter === "all") return true;
    const meta = CASE_DOMAIN_META[filter as Exclude<CaseDomain, "Autre">];
    if (!meta) return true;
    const hay = `${tpl.domain} ${tpl.labelFr} ${tpl.labelAr} ${tpl.id}`.toLowerCase();
    return (
      hay.includes(meta.fr.toLowerCase()) ||
      hay.includes(meta.ar) ||
      hay.includes(filter.toLowerCase()) ||
      (filter === "Immobilier" && (hay.includes("عقاري") || hay.includes("foncier"))) ||
      (filter === "Travail" && (hay.includes("شغل") || hay.includes("social"))) ||
      (filter === "Circulation" && (hay.includes("سير") || hay.includes("circulation"))) ||
      (filter === "Détention" && (hay.includes("معتقل") || hay.includes("detention"))) ||
      (filter === "Banque & crédit" && (hay.includes("بنكي") || hay.includes("banque"))) ||
      (filter === "Fiscal" && (hay.includes("جبائي") || hay.includes("fiscal"))) ||
      (filter === "Pénal" && (hay.includes("زجري") || hay.includes("جنائ") || hay.includes("penal")))
    );
  };

  const { customCards, featuredCards, otherCards } = useMemo(() => {
    const custom = customTemplates.map((tpl) => ({
      kind: "custom" as const,
      id: tpl.id,
      title: tpl.name,
      subtitle: isAr ? "نموذج المكتب" : "Modèle du cabinet",
      body: tpl.body,
    }));
    const system = systemTemplates
      .filter((tpl) => tpl.id !== "libre")
      .filter((tpl) => matchesDomain(tpl, domainFilter))
      .map((tpl) => ({
        kind: "system" as const,
        id: tpl.id,
        title: isAr ? tpl.labelAr : tpl.labelFr,
        subtitle: isAr
          ? `${tpl.domain} · ${tpl.jurisdiction}`
          : `${tpl.domain} · ${tpl.labelFr}`,
        body: tpl.body,
      }));
    const featured = system.filter((c) => featuredOrder.includes(c.id));
    const others = system.filter((c) => !featuredOrder.includes(c.id));
    featured.sort(
      (a, b) => featuredOrder.indexOf(a.id) - featuredOrder.indexOf(b.id),
    );
    return {
      customCards: custom,
      featuredCards: featured,
      otherCards: others,
    };
  }, [customTemplates, systemTemplates, isAr, featuredOrder, domainFilter]);

  const allCards = useMemo(
    () => [...customCards, ...featuredCards, ...otherCards],
    [customCards, featuredCards, otherCards],
  );
  const modalCard = allCards.find((c) => c.id === modalId) ?? null;

  useEffect(() => {
    if (!modalId) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setModalId(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [modalId]);

  function renderCard(tpl: CardItem) {
    const selected = selectedTemplateId === tpl.id;
    return (
      <div key={tpl.id} className="relative">
        <button
          type="button"
          onClick={() => setSelectedTemplateId(tpl.id)}
          className={cn(
            "card relative w-full overflow-hidden p-5 text-start transition",
            "hover:-translate-y-0.5 hover:border-[var(--gold)]/40",
            selected &&
              "border-[var(--gold)]/45 shadow-[0_16px_40px_rgba(26,43,74,0.1)]",
          )}
        >
          <div className="flex items-start gap-3">
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-[12px] bg-[rgba(184,148,74,0.14)] text-[var(--gold-deep)]">
              <FileText className="h-5 w-5" />
            </span>
            <div className="min-w-0 pe-8">
              <p className="font-[family-name:var(--font-display)] text-lg text-[var(--ink)]">
                {tpl.title}
              </p>
              <p className="mt-1 line-clamp-2 text-xs text-[var(--ink-mute)]">
                {tpl.subtitle}
              </p>
            </div>
          </div>

        </button>

        {tpl.kind === "custom" ? (
          <button
            type="button"
            className="absolute end-3 top-3 grid h-8 w-8 place-items-center rounded-full text-[var(--ink-mute)] hover:bg-[rgba(180,60,60,0.1)] hover:text-[var(--danger,#b43c3c)]"
            aria-label={isAr ? "حذف" : "Supprimer"}
            onClick={(e) => {
              e.stopPropagation();
              onDeleteCustom(tpl.id);
            }}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        ) : null}
      </div>
    );
  }

  return (
    <div className="space-y-6" dir={isAr ? "rtl" : "ltr"}>
      <div className="plea-hero">
        <p className="plea-hero__brand">{isAr ? "LexHub · مرافعة" : "LexHub · Plaidoirie"}</p>
        <h1 className="section-title" style={{ marginBottom: 8 }}>
          {isAr ? "اختروا المادة ثم نوع المرافعة" : "Choisissez la matière, puis le type"}
        </h1>
        <p className="section-sub" style={{ marginBottom: 0 }}>
          {isAr
            ? "المادة (أسرة، مدني، زجري…) توجّه المحكمة والأطراف والأقسام. النوع يساعد الذكاء الاصطناعي على صياغة صحيحة دون اختراع."
            : "La matière (famille, civil, pénal…) oriente le tribunal, les rôles et les sections. Le type aide l’IA à structurer correctement — sans inventer les faits."}
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <p className="mb-2 text-xs font-bold uppercase tracking-wider text-[var(--gold-deep)]">
            {isAr ? "١ — المادة / المجال" : "1 — Matière / domaine"}
          </p>
          <div className="flex flex-wrap gap-2" role="group" aria-label={isAr ? "تصفية حسب المادة" : "Filtrer par matière"}>
            <button
              type="button"
              className={cn(
                "rounded-full border px-3 py-1.5 text-xs font-semibold transition",
                domainFilter === "all"
                  ? "border-[var(--navy)] bg-[var(--navy)] text-white"
                  : "border-[rgba(26,43,74,0.15)] bg-white/80 text-[var(--ink)] hover:border-[var(--gold)]/40",
              )}
              onClick={() => setDomainFilter("all")}
            >
              {isAr ? "الكل" : "Toutes"}
            </button>
            {domainChips.map((key) => {
              const meta = CASE_DOMAIN_META[key];
              const active = domainFilter === key;
              return (
                <button
                  key={key}
                  type="button"
                  title={meta.hintFr}
                  className={cn(
                    "rounded-full border px-3 py-1.5 text-xs font-semibold transition",
                    active
                      ? "border-[var(--navy)] bg-[var(--navy)] text-white"
                      : "border-[rgba(26,43,74,0.15)] bg-white/80 text-[var(--ink)] hover:border-[var(--gold)]/40",
                  )}
                  onClick={() => setDomainFilter(key)}
                >
                  {isAr ? meta.ar : meta.fr}
                </button>
              );
            })}
          </div>
          {domainFilter !== "all" && CASE_DOMAIN_META[domainFilter as Exclude<CaseDomain, "Autre">] ? (
            <p className="mt-2 text-xs text-[var(--ink-soft)]">
              {CASE_DOMAIN_META[domainFilter as Exclude<CaseDomain, "Autre">].hintFr}
            </p>
          ) : (
            <p className="mt-2 text-xs text-[var(--ink-soft)]">
              {isAr
                ? "اختاروا المادة المطابقة للملف (مثال: أسرة لنفقة/حضانة)."
                : "Sélectionnez la matière du dossier (ex. Famille pour pension / garde)."}
            </p>
          )}
        </div>

        <button
          type="button"
          onClick={() => setSelectedTemplateId("libre")}
          className={cn(
            "card flex w-full items-start gap-4 p-5 text-start transition hover:border-[var(--gold)]/35",
            selectedTemplateId === "libre" &&
              "border-[var(--gold)]/45 shadow-[0_16px_40px_rgba(26,43,74,0.1)]",
          )}
        >
          <span className="grid h-11 w-11 shrink-0 place-items-center rounded-[12px] bg-[rgba(26,43,74,0.08)] text-[var(--ink)]">
            <FileEdit className="h-5 w-5" />
          </span>
          <div className="min-w-0">
            <p className="font-[family-name:var(--font-display)] text-lg text-[var(--ink)]">
              {isAr ? "بدون نموذج ثابت (حر)" : "Sans modèle fixe (libre)"}
            </p>
            <p className="mt-1 text-sm text-[var(--ink-soft)]">
              {isAr
                ? "للملفات غير النمطية — يُفضَّل مع ذلك اختيار المادة أعلاه ثم الإملاء."
                : "Pour cas atypiques — préférez quand même filtrer la matière ci-dessus, puis dicter."}
            </p>
          </div>
        </button>

        {customCards.length > 0 ? (
          <div className="space-y-3">
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--gold-deep)]">
              {isAr ? "نماذج المكتب" : "Modèles du cabinet"}
            </p>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {customCards.map(renderCard)}
            </div>
          </div>
        ) : null}

        <div className="space-y-3">
          <p className="text-xs font-bold uppercase tracking-wider text-[var(--gold-deep)]">
            {isAr ? "٢ — نوع المرافعة" : "2 — Type de plaidoirie"}
          </p>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {featuredCards.map(renderCard)}
          </div>
          {featuredCards.length === 0 ? (
            <p className="text-sm text-[var(--ink-soft)]">
              {isAr
                ? "لا نماذج في هذه المادة — جرّبوا «الكل» أو «حر»."
                : "Aucun type pour ce filtre — essayez « Toutes » ou « libre »."}
            </p>
          ) : null}
        </div>

        {otherCards.length > 0 ? (
          <div className="space-y-3">
            <button
              type="button"
              className="flex w-full items-center justify-between rounded-[14px] border border-[rgba(26,43,74,0.1)] bg-[rgba(255,252,246,0.6)] px-4 py-3 text-start text-sm font-semibold text-[var(--ink)] transition hover:border-[var(--gold)]/35"
              onClick={() => setShowOthers((v) => !v)}
              aria-expanded={showOthers}
            >
              <span>
                {isAr ? "أنواع أخرى" : "Autres types"}{" "}
                <span className="font-normal text-[var(--ink-mute)]">
                  ({otherCards.length})
                </span>
              </span>
              <ChevronDown
                className={cn(
                  "h-4 w-4 text-[var(--ink-mute)] transition",
                  showOthers && "rotate-180",
                )}
              />
            </button>
            {showOthers ? (
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {otherCards.map(renderCard)}
              </div>
            ) : null}
          </div>
        ) : null}
      </div>

      {/* Étape 2 → bouton clair : on ne montre pas d'aperçu / modal. */}
      <div className="pt-2">
        {selectedTemplateId ? (
          <button
            type="button"
            className="chip-btn primary w-full"
            onClick={() => onSelect(selectedTemplateId)}
          >
            {isAr ? "متابعة إلى الورشة →" : "Continuer vers l’étape suivante →"}
          </button>
        ) : (
          <p className="text-center text-sm text-slate-500">
            {isAr
              ? "اختاروا نوع المرافعة ثم اضغطوا المتابعة."
              : "Choisissez un type de plaidoirie, puis cliquez Continuer."}
          </p>
        )}
      </div>

      <section className="card space-y-4 p-5" aria-labelledby="plea-history-title">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-[12px] bg-[rgba(27,63,156,0.1)] text-[#1B3F9C]">
            <History className="h-5 w-5" />
          </span>
          <div>
            <h2 id="plea-history-title" className="text-base font-bold text-[var(--ink)]">
              {isAr ? "سجل المرافعات المحرّرة" : "Historique des plaidoiries"}
            </h2>
            <p className="text-xs text-[var(--ink-soft)]">
              {isAr
                ? "افتحوا، اطبعوا أو حمّلوا مرافعة محفوظة تلقائياً بعد التوليد."
                : "Rouvrez, imprimez ou téléchargez une plaidoirie enregistrée après génération."}
            </p>
          </div>
        </div>
        {draftsLoading ? (
          <p className="text-sm text-[var(--ink-soft)]">{isAr ? "جاري التحميل…" : "Chargement…"}</p>
        ) : drafts.length === 0 ? (
          <p className="text-sm text-[var(--ink-soft)]">
            {isAr
              ? "لا توجد مرافعات محفوظة بعد. أنشئوا واحدة ثم ستظهر هنا."
              : "Aucune plaidoirie enregistrée pour l’instant."}
          </p>
        ) : (
          <ul className="space-y-3">
            {drafts.map((d) => {
              const when = new Date(d.updated_at || d.created_at).toLocaleString(
                isAr ? "ar-MA" : "fr-FR",
                { dateStyle: "medium", timeStyle: "short" },
              );
              const busy = draftBusyId === d.id;
              return (
                <li
                  key={d.id}
                  className="flex flex-col gap-3 rounded-[14px] border border-[rgba(26,43,74,0.1)] bg-[rgba(255,252,246,0.75)] p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <p
                      className="line-clamp-2 break-words font-semibold text-[var(--ink)]"
                      dir="auto"
                      title={d.title || undefined}
                    >
                      {d.title || (isAr ? "بدون عنوان" : "Sans titre")}
                    </p>
                    <p className="mt-0.5 text-xs text-[var(--ink-mute)]">{when}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="chip-btn primary"
                      disabled={busy}
                      onClick={() => {
                        const tpl = d.template_id || "libre";
                        try {
                          sessionStorage.setItem(
                            PLEA_DRAFT_RESTORE_KEY,
                            JSON.stringify({
                              title: d.title,
                              body: d.body,
                              case_id: d.case_id || "",
                              template_id: tpl,
                              draft_id: d.id,
                            }),
                          );
                        } catch {
                          /* ignore */
                        }
                        window.location.assign(
                          `/redaction/${encodeURIComponent(tpl)}?draft=${encodeURIComponent(d.id)}`,
                        );
                      }}
                    >
                      {isAr ? "فتح الورشة" : "Ouvrir l'atelier"}
                    </button>
                    <button
                      type="button"
                      className="chip-btn"
                      disabled={busy}
                      onClick={() => {
                        setDraftBusyId(d.id);
                        void api
                          .downloadPlaidoirieDocx({
                            title: d.title || (isAr ? "مرافعة" : "Plaidoirie"),
                            body: d.body || "",
                          })
                          .catch(() => undefined)
                          .finally(() => setDraftBusyId(null));
                      }}
                    >
                      <Download className="me-1 inline h-3.5 w-3.5" />
                      Word
                    </button>
                    <button
                      type="button"
                      className="chip-btn"
                      disabled={busy}
                      onClick={() => {
                        setDraftBusyId(d.id);
                        void api
                          .deletePlaidoirieDraft(d.id)
                          .then(() => {
                            setDrafts((prev) => prev.filter((x) => x.id !== d.id));
                            if ((d.status || "draft") === "draft") clearPleaSession();
                            pushToast(
                              isAr ? "تم حذف المرافعة بنجاح." : "Plaidoirie supprimée avec succès.",
                              "success",
                            );
                          })
                          .catch((e) => {
                            pushToast(
                              e instanceof Error
                                ? e.message
                                : isAr
                                  ? "تعذّر الحذف."
                                  : "Suppression impossible.",
                              "error",
                            );
                          })
                          .finally(() => setDraftBusyId(null));
                      }}
                    >
                      <Trash2 className="me-1 inline h-3.5 w-3.5" />
                      {isAr ? "حذف" : "Supprimer"}
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {modalCard ? (
        <div
          className="modal-overlay open"
          role="presentation"
          onClick={() => setModalId(null)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            className="modal-card"
            style={{ maxWidth: 520 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-head">
              <div>
                <p className="modal-sub" style={{ marginBottom: 4 }}>
                  {isAr ? "تأكيد النموذج" : "Confirmer le modèle"}
                </p>
                <h2 id={titleId} className="modal-title">
                  {modalCard.title}
                </h2>
              </div>
              <button
                type="button"
                className="modal-close"
                onClick={() => setModalId(null)}
                aria-label={isAr ? "إغلاق" : "Fermer"}
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <p className="modal-sub">{modalCard.subtitle}</p>
            <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded-[16px] border border-[rgba(26,43,74,0.08)] bg-[rgba(248,244,236,0.7)] p-4 font-sans text-xs leading-relaxed text-[var(--ink-soft)]">
              {modalCard.body.slice(0, 900)}
              {modalCard.body.length > 900 ? "…" : ""}
            </pre>
            <div className="modal-foot">
              <button
                type="button"
                className="btn-ghost"
                onClick={() => setModalId(null)}
              >
                {isAr ? "إلغاء" : "Annuler"}
              </button>
              <button
                type="button"
                className="btn-create"
                onClick={() => {
                  const id = modalCard.id;
                  setModalId(null);
                  onSelect(id);
                }}
              >
                {isAr ? "متابعة" : "Continuer"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
