"use client";

import { useState } from "react";
import { Loader2, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, getClientLocale, type AIResult } from "@/lib/api";
import { useBillingCredits } from "@/store/billing-credits";
import {
  StructuredSynthesis,
  cleanSynthesisMarkdown,
} from "@/components/ai/structured-synthesis";

interface DocumentAskProps {
  documentId: string;
  suggestions?: string[];
}

export function DocumentAsk({ documentId, suggestions = [] }: DocumentAskProps) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AIResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function ask(q: string) {
    const trimmed = q.trim();
    if (!trimmed || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.askDocument(documentId, trimmed, getClientLocale());
      setResult(res);
      setQuestion("");
      void useBillingCredits.getState().notifySpend("ask");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Question impossible");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      {suggestions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {suggestions.map((s) => (
            <button
              key={s}
              type="button"
              className="rounded-md border border-sanad-border px-3 py-1.5 text-left text-xs text-slate-600 hover:bg-sanad-light"
              onClick={() => setQuestion(s)}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={2}
          placeholder="Posez une question sur ce document…"
          className="min-h-[2.75rem] flex-1 resize-y rounded-md border border-sanad-border px-3 py-2 text-sm outline-none focus:border-sanad-blue"
        />
        <Button
          type="button"
          disabled={loading || !question.trim()}
          onClick={() => ask(question)}
          className="self-end"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </Button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {result && (
        <div className="rounded-md border border-sanad-border bg-sanad-light/40 p-4 text-sm text-slate-700">
          <StructuredSynthesis text={cleanSynthesisMarkdown(result.answer || "")} />
          {result.disclaimer && (
            <p className="mt-3 text-xs text-slate-500">{result.disclaimer}</p>
          )}
        </div>
      )}
    </div>
  );
}
