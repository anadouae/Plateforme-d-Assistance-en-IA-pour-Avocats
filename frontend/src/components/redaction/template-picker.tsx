"use client";

import { useEffect, useId, useMemo, useState } from "react";
import { FileEdit, FileText, LayoutTemplate, Trash2, X } from "lucide-react";
import type { CabinetPlaidoirieTemplate } from "@/lib/api";
import type { PlaidoirieTemplate } from "@/lib/plaidoirie-templates";
import { useLocaleStore, useTranslations } from "@/store/locale";
import { cn } from "@/lib/utils";

type Props = {
  systemTemplates: PlaidoirieTemplate[];
  customTemplates: CabinetPlaidoirieTemplate[];
  onSelect: (id: string) => void;
  onDeleteCustom: (id: string) => void;
};

type Step = "choose" | "browse";

type CardItem = {
  kind: "system" | "custom";
  id: string;
  title: string;
  subtitle: string;
  body: string;
};

/**
 * Parcours d’origine :
 * 1) النماذج / الصفحة الفارغة
 * 2) grille + aperçu au survol + modal → متابعة
 * Design Sanad (parchment / ink / gold) uniquement.
 */
export function TemplatePicker({
  systemTemplates,
  customTemplates,
  onSelect,
  onDeleteCustom,
}: Props) {
  const locale = useLocaleStore((s) => s.locale);
  const t = useTranslations();
  const isAr = locale === "ar";
  const [step, setStep] = useState<Step>("choose");
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [modalId, setModalId] = useState<string | null>(null);
  const titleId = useId();

  const cards = useMemo<CardItem[]>(() => {
    const custom = customTemplates.map((tpl) => ({
      kind: "custom" as const,
      id: tpl.id,
      title: tpl.name,
      subtitle: isAr ? "نموذج المكتب" : "Modèle du cabinet",
      body: tpl.body,
    }));
    const system = systemTemplates
      .filter((tpl) => tpl.id !== "libre")
      .map((tpl) => ({
        kind: "system" as const,
        id: tpl.id,
        title: isAr ? tpl.labelAr : tpl.labelFr,
        subtitle: isAr
          ? `${tpl.domain} · ${tpl.jurisdiction}`
          : `${tpl.domain} · ${tpl.labelFr}`,
        body: tpl.body,
      }));
    return [...custom, ...system];
  }, [customTemplates, systemTemplates, isAr]);

  const modalCard = cards.find((c) => c.id === modalId) ?? null;

  useEffect(() => {
    if (!modalId) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setModalId(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [modalId]);

  return (
    <div className="space-y-6" dir={isAr ? "rtl" : "ltr"}>
      <div>
        <h1 className="section-title">{t.nav.redaction}</h1>
        <p className="section-sub">
          {step === "choose"
            ? isAr
              ? "اختر نموذجاً جاهزاً أو ابدأ من صفحة فارغة."
              : "Choisissez un modèle prêt ou partez d’une page vierge."
            : isAr
              ? "مرّر على البطاقة لمعاينة المحتوى، ثم انقر للمتابعة."
              : "Survolez une carte pour l’aperçu, puis cliquez pour continuer."}
        </p>
      </div>

      {step === "choose" ? (
        <div className="grid gap-4 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => setStep("browse")}
            className="card group flex min-h-[200px] flex-col items-start gap-4 p-7 text-start transition hover:-translate-y-0.5 hover:border-[var(--gold)]/35"
          >
            <span className="grid h-12 w-12 place-items-center rounded-[14px] bg-[rgba(184,148,74,0.14)] text-[var(--gold-deep)]">
              <LayoutTemplate className="h-6 w-6" />
            </span>
            <div>
              <p className="font-[family-name:var(--font-display)] text-2xl text-[var(--ink)]">
                {isAr ? "النماذج" : "Les modèles"}
              </p>
              <p className="mt-2 text-sm leading-relaxed text-[var(--ink-soft)]">
                {isAr
                  ? "تصفّح النماذج الجاهزة مع معاينة عند التمرير."
                  : "Parcourez les modèles prêts avec aperçu au survol."}
              </p>
            </div>
            <span className="mt-auto text-sm font-semibold text-[var(--gold-deep)]">
              {isAr ? "فتح المكتبة ←" : "Ouvrir la bibliothèque →"}
            </span>
          </button>

          <button
            type="button"
            onClick={() => onSelect("libre")}
            className="card group flex min-h-[200px] flex-col items-start gap-4 p-7 text-start transition hover:-translate-y-0.5 hover:border-[var(--gold)]/35"
          >
            <span className="grid h-12 w-12 place-items-center rounded-[14px] bg-[rgba(26,43,74,0.08)] text-[var(--ink)]">
              <FileEdit className="h-6 w-6" />
            </span>
            <div>
              <p className="font-[family-name:var(--font-display)] text-2xl text-[var(--ink)]">
                {isAr ? "الصفحة الفارغة" : "Page vierge"}
              </p>
              <p className="mt-2 text-sm leading-relaxed text-[var(--ink-soft)]">
                {isAr
                  ? "ابدأ من الصفر — إملاء، ملف أو كتابة مباشرة."
                  : "Partez d’une feuille blanche — dictée, fichier ou saisie."}
              </p>
            </div>
            <span className="mt-auto text-sm font-semibold text-[var(--ink)]">
              {isAr ? "البدء الآن ←" : "Commencer maintenant →"}
            </span>
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm font-semibold text-[var(--ink)]">
              {isAr ? "مكتبة النماذج" : "Bibliothèque de modèles"}
            </p>
            <button
              type="button"
              className="btn-ghost !py-2 !text-sm"
              onClick={() => {
                setStep("choose");
                setPreviewId(null);
              }}
            >
              {isAr ? "← رجوع" : "← Retour"}
            </button>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {cards.map((tpl) => {
              const active = previewId === tpl.id;
              return (
                <div
                  key={tpl.id}
                  className="relative"
                  onMouseEnter={() => setPreviewId(tpl.id)}
                  onMouseLeave={() => setPreviewId(null)}
                >
                  <button
                    type="button"
                    onFocus={() => setPreviewId(tpl.id)}
                    onBlur={() => setPreviewId(null)}
                    onClick={() => setModalId(tpl.id)}
                    className={cn(
                      "card relative w-full overflow-hidden p-5 text-start transition",
                      "hover:-translate-y-0.5 hover:border-[var(--gold)]/40",
                      active &&
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

                    {active ? (
                      <div className="pointer-events-none absolute inset-x-3 bottom-3 top-[4.5rem] overflow-hidden rounded-[14px] border border-[rgba(26,43,74,0.08)] bg-[rgba(255,252,246,0.96)] p-3 shadow-lg">
                        <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-[var(--gold-deep)]">
                          {isAr ? "معاينة" : "Aperçu"}
                        </p>
                        <pre className="max-h-[140px] overflow-hidden whitespace-pre-wrap font-sans text-[11px] leading-relaxed text-[var(--ink-soft)]">
                          {tpl.body.slice(0, 420)}
                          {tpl.body.length > 420 ? "…" : ""}
                        </pre>
                      </div>
                    ) : null}
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
            })}
          </div>
        </div>
      )}

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
