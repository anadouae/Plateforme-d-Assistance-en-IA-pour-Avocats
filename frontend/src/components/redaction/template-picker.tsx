"use client";

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { FilePlus2, LayoutGrid, Trash2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { CabinetPlaidoirieTemplate } from "@/lib/api";
import type { PlaidoirieTemplate } from "@/lib/plaidoirie-templates";
import { cn } from "@/lib/utils";

type Mode = "choose" | "browse";

type Props = {
  systemTemplates: PlaidoirieTemplate[];
  customTemplates: CabinetPlaidoirieTemplate[];
  onSelect: (id: string) => void;
  onDeleteCustom: (id: string) => void;
};

/**
 * Étape 1 : choisir un départ → navigation vers l’espace dictée.
 */
export function TemplatePicker({
  systemTemplates,
  customTemplates,
  onSelect,
  onDeleteCustom,
}: Props) {
  const [mode, setMode] = useState<Mode>("choose");
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [hoverId, setHoverId] = useState<string | null>(null);

  const allCards = useMemo(() => {
    const sys = systemTemplates.map((t) => ({
      kind: "system" as const,
      id: t.id,
      label: t.labelAr,
      sub: t.labelFr,
      domain: t.domain,
      body: t.body,
      jurisdiction: t.jurisdiction,
    }));
    const custom = customTemplates.map((t) => ({
      kind: "custom" as const,
      id: t.id,
      label: t.name,
      sub: "نموذج المكتب",
      domain: t.base_type || "حر",
      body: t.body,
      jurisdiction: "Cabinet",
    }));
    return [...custom, ...sys];
  }, [systemTemplates, customTemplates]);

  const openCard = allCards.find((c) => c.id === previewId);
  const hoverCard = allCards.find((c) => c.id === hoverId);

  function confirmPick(id: string) {
    setPreviewId(null);
    onSelect(id);
  }

  return (
    <Card className="border-sanad-gold/25">
      <CardHeader className="pb-2">
        <CardTitle className="text-base" dir="rtl">
          اختر نقطة البداية
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => confirmPick("libre")}
            className={cn(
              "flex flex-col items-start gap-2 rounded-2xl border px-4 py-5 text-start transition",
              "hover:-translate-y-0.5 hover:border-sanad-gold hover:shadow-md",
              "border-sanad-border bg-white",
            )}
          >
            <span className="flex items-center gap-2 text-sm font-semibold text-sanad-navy">
              <FilePlus2 className="h-5 w-5 text-sanad-gold" />
              صفحة فارغة
            </span>
          </button>

          <button
            type="button"
            onClick={() => setMode("browse")}
            className={cn(
              "flex flex-col items-start gap-2 rounded-2xl border px-4 py-5 text-start transition",
              "hover:-translate-y-0.5 hover:shadow-md",
              mode === "browse"
                ? "border-sanad-gold bg-sanad-gold/10 shadow-sm"
                : "border-sanad-border bg-white",
            )}
          >
            <span className="flex items-center gap-2 text-sm font-semibold text-sanad-navy">
              <LayoutGrid className="h-5 w-5 text-sanad-gold" />
              النماذج
            </span>
          </button>
        </div>

        {mode === "browse" && (
          <div className="relative">
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {allCards.map((card) => (
                <div
                  key={`${card.kind}-${card.id}`}
                  className="relative"
                  onMouseEnter={() => setHoverId(card.id)}
                  onMouseLeave={() => setHoverId((id) => (id === card.id ? null : id))}
                >
                  <button
                    type="button"
                    onClick={() => setPreviewId(card.id)}
                    className={cn(
                      "flex w-full flex-col gap-1 rounded-xl border px-3 py-3 text-start transition",
                      "border-sanad-border bg-white hover:border-sanad-gold hover:bg-sanad-gold/5",
                    )}
                  >
                    <span className="text-sm font-semibold text-sanad-navy" dir="rtl">
                      {card.label}
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {card.sub} · {card.domain}
                    </span>
                  </button>
                  {card.kind === "custom" && (
                    <button
                      type="button"
                      className="absolute end-1 top-1 rounded p-1 text-slate-400 hover:bg-red-50 hover:text-red-600"
                      title="حذف"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteCustom(card.id);
                      }}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  )}

                  <AnimatePresence>
                    {hoverId === card.id && hoverCard && previewId !== card.id && (
                      <motion.div
                        initial={{ opacity: 0, y: 6, scale: 0.98 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 4 }}
                        className="pointer-events-none absolute start-0 top-full z-20 mt-2 w-[min(320px,80vw)] overflow-hidden rounded-xl border border-sanad-gold/40 bg-white p-3 shadow-2xl"
                      >
                        <pre
                          dir="rtl"
                          className="max-h-40 overflow-hidden whitespace-pre-wrap font-arabic text-[11px] leading-relaxed text-sanad-navy"
                        >
                          {hoverCard.body.slice(0, 420)}
                          {hoverCard.body.length > 420 ? "…" : ""}
                        </pre>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </div>
          </div>
        )}

        <AnimatePresence>
          {openCard && (
            <>
              <motion.div
                className="fixed inset-0 z-40 bg-sanad-navy/30 backdrop-blur-[2px]"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setPreviewId(null)}
              />
              <motion.div
                role="dialog"
                aria-modal
                initial={{ opacity: 0, y: 24, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 12, scale: 0.98 }}
                className="fixed inset-4 z-50 m-auto flex max-h-[min(880px,92vh)] max-w-3xl flex-col overflow-hidden rounded-2xl border border-sanad-border bg-white shadow-2xl md:inset-8"
              >
                <div className="flex items-start justify-between gap-3 border-b border-sanad-stone px-4 py-3">
                  <div dir="rtl" className="min-w-0 text-right">
                    <p className="truncate font-semibold text-sanad-navy">{openCard.label}</p>
                    <p className="text-xs text-slate-500">
                      {openCard.sub} · {openCard.jurisdiction}
                    </p>
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    className="h-8 w-8 shrink-0 p-0"
                    onClick={() => setPreviewId(null)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
                <div className="min-h-0 flex-1 overflow-auto px-4 py-3">
                  <pre
                    dir="rtl"
                    className="whitespace-pre-wrap font-arabic text-sm leading-8 text-sanad-navy"
                  >
                    {openCard.body}
                  </pre>
                </div>
                <div className="flex flex-wrap justify-end gap-2 border-t border-sanad-stone px-4 py-3">
                  <Button type="button" variant="ghost" onClick={() => setPreviewId(null)}>
                    إغلاق
                  </Button>
                  <Button type="button" onClick={() => confirmPick(openCard.id)}>
                    متابعة
                  </Button>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}
