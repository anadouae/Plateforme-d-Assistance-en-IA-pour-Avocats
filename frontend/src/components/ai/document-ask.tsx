"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, Send, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MarkdownAnswer } from "@/components/ai/markdown-answer";
import { api, getClientLocale, type Citation } from "@/lib/api";
import { useBillingCredits } from "@/store/billing-credits";
import { cn } from "@/lib/utils";

interface DocumentAskProps {
  documentId: string;
  suggestions?: string[];
}

type ChatMsg = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Citation[];
  disclaimer?: string;
  at: number;
};

export function DocumentAsk({ documentId, suggestions = [] }: DocumentAskProps) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const locale = getClientLocale();
  const uiFr = locale !== "ar";

  useEffect(() => {
    setMessages([]);
    setError(null);
    setQuestion("");
  }, [documentId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  async function ask(q: string) {
    const trimmed = q.trim();
    if (!trimmed || loading) return;
    const userMsg: ChatMsg = {
      id: `u-${Date.now()}`,
      role: "user",
      content: trimmed,
      at: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");
    setLoading(true);
    setError(null);
    try {
      const history = [...messages, userMsg]
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content }));
      const res = await api.askDocument(documentId, trimmed, getClientLocale(), history);
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          content: res.answer || (uiFr ? "Pas de réponse." : "لا إجابة."),
          sources: res.sources,
          disclaimer: res.disclaimer,
          at: Date.now(),
        },
      ]);
      void useBillingCredits.getState().notifySpend("ask");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Question impossible";
      setError(msg);
      setMessages((prev) => [
        ...prev,
        {
          id: `a-err-${Date.now()}`,
          role: "assistant",
          content: uiFr
            ? `Impossible de répondre : ${msg}`
            : `تعذر الرد : ${msg}`,
          at: Date.now(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {suggestions.length > 0 && messages.length === 0 && (
        <div className="flex flex-wrap gap-2">
          {suggestions.map((s) => (
            <button
              key={s}
              type="button"
              className="rounded-full border border-sanad-border bg-white px-3 py-1.5 text-left text-xs text-slate-600 shadow-sm transition hover:border-sanad-blue/40 hover:bg-sanad-light"
              onClick={() => void ask(s)}
              disabled={loading}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <div
        className={cn(
          "flex max-h-[min(52vh,420px)] min-h-[180px] flex-col gap-3 overflow-y-auto rounded-xl border border-sanad-border bg-slate-50/80 p-3",
          messages.length === 0 && "items-center justify-center",
        )}
      >
        {messages.length === 0 && !loading ? (
          <p className="px-4 text-center text-sm text-slate-500">
            {uiFr
              ? "Posez une question sur ce document — comme un chat. Les réponses sont structurées (titres, listes, gras)."
              : "اطرحوا سؤالاً عن الوثيقة — كمحادثة. الإجابات منظمة (عناوين، قوائم، خط عريض)."}
          </p>
        ) : null}

        {messages.map((m) => (
          <div
            key={m.id}
            className={cn(
              "max-w-[92%] rounded-2xl px-3.5 py-2.5 text-sm shadow-sm",
              m.role === "user"
                ? "ml-auto bg-sanad-navy text-white"
                : "mr-auto border border-sanad-border bg-white text-slate-800",
            )}
            dir={/[\u0600-\u06FF]/.test(m.content) ? "rtl" : "ltr"}
          >
            {m.role === "user" ? (
              <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
            ) : (
              <>
                <MarkdownAnswer text={m.content} sources={m.sources || []} />
                {m.disclaimer ? (
                  <p className="mt-2 border-t border-slate-100 pt-2 text-[11px] text-slate-400">
                    {m.disclaimer}
                  </p>
                ) : null}
              </>
            )}
          </div>
        ))}

        {loading ? (
          <div className="mr-auto flex items-center gap-2 rounded-2xl border border-sanad-border bg-white px-3.5 py-2.5 text-sm text-sanad-blue shadow-sm">
            <Loader2 className="h-4 w-4 animate-spin" />
            {uiFr ? "L’IA lit le document…" : "الذكاء الاصطناعي يقرأ الوثيقة…"}
          </div>
        ) : null}
        <div ref={bottomRef} />
      </div>

      {error && !loading ? (
        <p className="text-xs text-red-600">{error}</p>
      ) : null}

      <div className="flex items-end gap-2">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void ask(question);
            }
          }}
          rows={2}
          placeholder={
            uiFr
              ? "Posez une question sur ce document… (Entrée pour envoyer)"
              : "اطرحوا سؤالاً عن الوثيقة…"
          }
          className="min-h-[2.75rem] flex-1 resize-y rounded-xl border border-sanad-border bg-white px-3 py-2 text-sm outline-none focus:border-sanad-blue"
          disabled={loading}
        />
        <Button
          type="button"
          disabled={loading || !question.trim()}
          onClick={() => void ask(question)}
          className="self-end rounded-full"
          aria-label="Envoyer"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </Button>
        {messages.length > 0 ? (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="self-end text-slate-400 hover:text-red-600"
            title={uiFr ? "Effacer le chat" : "مسح المحادثة"}
            onClick={() => {
              setMessages([]);
              setError(null);
            }}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        ) : null}
      </div>
    </div>
  );
}
