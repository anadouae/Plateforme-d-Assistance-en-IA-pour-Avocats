"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/** Nettoie Markdown / méta LLM pour un rendu « document officiel ». */
export function cleanSynthesisMarkdown(raw: string): string {
  let t = (raw || "").replace(/\r\n/g, "\n").trim();
  if (!t) return "";
  // Couper notes meta du modèle
  t = t.split(/\n[-–—]*\s*\*?\*?ملاحظات\s*:?\*?\*?/i)[0] || t;
  t = t.split(/\n[-–—]*\s*\*?\*?Notes?\s*:?\*?\*?/i)[0] || t;
  t = t.replace(/```[\s\S]*$/g, "");
  t = t.replace(/\*\*/g, "").replace(/__/g, "").replace(/^#{1,6}\s+/gm, "");
  t = t.replace(/^[-*]{3,}\s*$/gm, "");
  t = t.replace(/\n{3,}/g, "\n\n").trim();
  return t;
}

type SectionTone = "title" | "intro" | "body" | "law" | "close" | "default";

const TONE_CLASS: Record<SectionTone, string> = {
  title: "border-sanad-navy/25 bg-sanad-navy/[0.06]",
  intro: "border-emerald-200/80 bg-emerald-50/70",
  body: "border-amber-200/70 bg-amber-50/50",
  law: "border-sky-200/80 bg-sky-50/60",
  close: "border-sanad-gold/35 bg-[rgba(197,160,40,0.08)]",
  default: "border-sanad-border bg-white",
};

function toneForTitle(title: string): SectionTone {
  const t = title.trim();
  if (/تلخيص|خلاصة|synthèse|résumé/i.test(t)) return "title";
  if (/مقدمة|introduction/i.test(t)) return "intro";
  if (/خاتمة|conclusion|صيغة|formule/i.test(t)) return "close";
  if (/مناقشة|أحكام|قانون|أسباب|motifs|droit/i.test(t)) return "law";
  if (/محاور|ماهية|وقائع|أطراف|faits|parties/i.test(t)) return "body";
  return "default";
}

function splitSections(text: string): { title: string; body: string }[] {
  const lines = text.split("\n");
  const sections: { title: string; body: string }[] = [];
  let curTitle = "";
  let curBody: string[] = [];

  const flush = () => {
    const body = curBody.join("\n").trim();
    if (!curTitle && !body) return;
    sections.push({ title: curTitle || "", body });
    curTitle = "";
    curBody = [];
  };

  const isHeading = (line: string) => {
    const t = line.trim();
    if (!t || t.length > 90) return false;
    if (/^(المقدمة|الخاتمة|المحاور الرئيسية|صيغة التأدب|Identification|I\.|II\.|III\.)/i.test(t))
      return true;
    if (/^\d+[\.\)]\s+\S/.test(t) && t.length < 70) return true;
    if (/^#{1,3}\s/.test(t)) return true;
    if (/^(تعريف|خصائص|أسباب|آثار|انقضاء)/.test(t) && t.length < 60) return true;
    return false;
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    const t = line.trim();
    if (!t) {
      curBody.push("");
      continue;
    }
    if (isHeading(t)) {
      flush();
      curTitle = t.replace(/^#+\s*/, "");
    } else {
      curBody.push(t);
    }
  }
  flush();

  if (sections.length <= 1 && text.length > 80) {
    return [{ title: "", body: text }];
  }
  return sections.filter((s) => s.title || s.body);
}

function renderBodyLines(body: string): ReactNode {
  const lines = body.split("\n").map((l) => l.trim()).filter(Boolean);
  if (!lines.length) return null;
  const items = lines.filter((l) => /^[-•●]\s+/.test(l) || /^\d+[\.\)]\s+/.test(l));
  if (items.length >= 2 && items.length === lines.length) {
    const ordered = /^\d+/.test(items[0]);
    const Tag = ordered ? "ol" : "ul";
    return (
      <Tag className={cn("my-1 space-y-1.5 text-sm leading-relaxed text-sanad-slate", ordered ? "list-decimal pr-5" : "list-disc pr-5")}>
        {items.map((item, i) => (
          <li key={i}>{item.replace(/^[-•●]\s+/, "").replace(/^\d+[\.\)]\s+/, "")}</li>
        ))}
      </Tag>
    );
  }
  return (
    <div className="space-y-2 text-sm leading-relaxed text-sanad-slate">
      {lines.map((line, i) => (
        <p key={i} className="m-0 text-justify">
          {line}
        </p>
      ))}
    </div>
  );
}

/** Affichage option 4 : document clair, zones colorées, sans étoiles Markdown. */
export function StructuredSynthesis({
  text,
  className,
}: {
  text: string;
  className?: string;
}) {
  const cleaned = cleanSynthesisMarkdown(text);
  if (!cleaned) return null;
  const sections = splitSections(cleaned);

  return (
    <div className={cn("space-y-3", className)} dir="auto">
      {sections.map((sec, i) => {
        const tone = sec.title ? toneForTitle(sec.title) : "default";
        return (
          <section
            key={i}
            className={cn(
              "rounded-xl border px-4 py-3 shadow-[0_1px_0_rgba(15,23,42,0.04)]",
              TONE_CLASS[tone],
            )}
          >
            {sec.title ? (
              <h4 className="mb-2 text-[13px] font-bold tracking-wide text-sanad-navy">
                {sec.title}
              </h4>
            ) : null}
            {renderBodyLines(sec.body)}
          </section>
        );
      })}
    </div>
  );
}
