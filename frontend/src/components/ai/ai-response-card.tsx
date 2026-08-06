"use client";

import { AIResult } from "@/lib/api";

import { exportAiResponsePdf } from "@/lib/export-pdf";

import { AlertTriangle, BookOpen, Download, Globe, FileText } from "lucide-react";

import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";

import { useTranslations } from "@/store/locale";
import { MarkdownAnswer } from "@/components/ai/markdown-answer";
import { renderAnswerWithLinks, SourceCitationCard } from "@/components/ai/source-links";



const sourceIcons: Record<string, typeof BookOpen> = {

  rag: BookOpen,

  web: Globe,

  document: FileText,

  "rag+web": Globe,

};



interface AIResponseCardProps {

  result: AIResult;

  className?: string;

  embedded?: boolean;

  exportLabel?: string;

}



export function AIResponseCard({ result, className, embedded, exportLabel }: AIResponseCardProps) {

  const ai = useTranslations().app.ai;

  const sourceLabels: Record<string, string> = {

    rag: ai.sourceRag,

    web: ai.sourceWeb,

    document: ai.sourceDocument,

    "rag+web": ai.sourceRagWeb,

    system: "Assistant",

    none: "Assistant",

  };

  const Icon = sourceIcons[result.source_type] || BookOpen;

  const isInformational = result.source_type === "system" || result.source_type === "none";

  const lowConfidence = !isInformational && result.confidence_score < 60;

  const pdfLabel = exportLabel || ai.exportPdf;



  return (

    <div className={cn("space-y-4", className)}>

      <div className="flex flex-wrap items-center gap-2">

        <span className="inline-flex items-center gap-1.5 rounded-full bg-sanad-blue/10 px-3 py-1 text-xs font-medium text-sanad-blue">

          <Icon className="h-3.5 w-3.5" />

          {sourceLabels[result.source_type] || result.source_type}

        </span>

        {!isInformational && (
        <span

          className={cn(

            "rounded-full px-3 py-1 text-xs font-medium",

            lowConfidence

              ? "bg-amber-100 text-amber-800"

              : "bg-green-100 text-green-800",

          )}

        >

          {ai.confidence} : {result.confidence_score} %

        </span>
        )}

        {embedded && (

          <Button

            variant="ghost"

            size="sm"

            onClick={() => exportAiResponsePdf(result)}

            className="ml-auto h-8 gap-1.5 text-xs"

          >

            <Download className="h-3.5 w-3.5" />

            {pdfLabel}

          </Button>

        )}

      </div>



      {lowConfidence && (

        <div className="flex items-start gap-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">

          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />

          {ai.lowConfidence}

        </div>

      )}



      <div

        className={cn(

          "whitespace-pre-wrap text-sm leading-relaxed text-sanad-slate",

          embedded ? "" : "rounded-lg bg-sanad-light p-4",

        )}

      >

        {renderAnswerWithLinks(result.answer, result.sources).some(
          (p) => typeof p !== "string",
        ) || result.answer.includes("##") || result.answer.includes("\n- ") ? (
          <MarkdownAnswer text={result.answer} sources={result.sources} />
        ) : (
          renderAnswerWithLinks(result.answer, result.sources)
        )}

      </div>



      {result.sources.length > 0 && (

        <div className="space-y-2">

          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">

            {ai.sources}

          </p>

          {result.sources.map((src, i) => (
            <SourceCitationCard key={i} src={src} index={i} />
          ))}

        </div>

      )}



      {result.summary &&
        !result.summary.trim().startsWith("{") &&
        !result.summary.includes('"answer"') && (

        <div className="rounded-lg border border-sanad-blue/20 bg-sanad-blue/5 p-4">

          <p className="text-xs font-semibold uppercase tracking-wide text-sanad-blue">

            Résumé

          </p>

          <p className="mt-2 text-sm leading-relaxed text-sanad-slate">
            <MarkdownAnswer text={result.summary} sources={result.sources} />
          </p>

        </div>

      )}



      <p className="text-xs italic text-slate-400">{result.disclaimer}</p>



      {!embedded && (

        <Button

          variant="outline"

          size="sm"

          onClick={() => exportAiResponsePdf(result)}

          className="gap-2"

        >

          <Download className="h-4 w-4" />

          {pdfLabel}

        </Button>

      )}

    </div>

  );

}

