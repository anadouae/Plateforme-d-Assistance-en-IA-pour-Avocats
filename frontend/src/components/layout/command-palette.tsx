"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import { api, type WorkspaceSearchHit } from "@/lib/api";
import { useClientLocale } from "@/store/locale";
import { cn } from "@/lib/utils";

/** Recherche globale ⌘K / Ctrl+K — style Linear / Notion. */
export function CommandPalette() {
  const router = useRouter();
  const ar = useClientLocale() === "ar";
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<WorkspaceSearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const tmr = useRef(0);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const meta = e.metaKey || e.ctrlKey;
      if (meta && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      } else if (e.key === "Escape") {
        setOpen(false);
      }
    }
    function onOpen() {
      setOpen(true);
    }
    window.addEventListener("keydown", onKey);
    window.addEventListener("lexhub-open-cmdk", onOpen);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("lexhub-open-cmdk", onOpen);
    };
  }, []);

  useEffect(() => {
    if (!open) {
      setQ("");
      setHits([]);
      return;
    }
    const t = window.setTimeout(() => inputRef.current?.focus(), 40);
    return () => window.clearTimeout(t);
  }, [open]);

  const runSearch = useCallback((term: string) => {
    window.clearTimeout(tmr.current);
    if (term.trim().length < 2) {
      setHits([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    tmr.current = window.setTimeout(() => {
      api
        .workspaceSearch(term.trim())
        .then((rows) => {
          setHits(rows);
          setActive(0);
        })
        .catch(() => setHits([]))
        .finally(() => setLoading(false));
    }, 180);
  }, []);

  function go(hit: WorkspaceSearchHit) {
    setOpen(false);
    router.push(hit.href);
  }

  if (!open) return null;

  return (
    <div className="cmdk-overlay" role="dialog" aria-modal="true" onClick={() => setOpen(false)}>
      <div
        className="cmdk-panel"
        dir={ar ? "rtl" : "ltr"}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="cmdk-input-row">
          <Search className="h-4 w-4 opacity-50" />
          <input
            ref={inputRef}
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              runSearch(e.target.value);
            }}
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") {
                e.preventDefault();
                setActive((i) => Math.min(i + 1, Math.max(0, hits.length - 1)));
              } else if (e.key === "ArrowUp") {
                e.preventDefault();
                setActive((i) => Math.max(0, i - 1));
              } else if (e.key === "Enter" && hits[active]) {
                e.preventDefault();
                go(hits[active]);
              }
            }}
            placeholder={
              ar
                ? "ابحث عن ملف، مرافعة، وثيقة…"
                : "Rechercher dossier, plaidoirie, document…"
            }
          />
          <kbd className="cmdk-kbd">esc</kbd>
        </div>
        <div className="cmdk-results">
          {loading ? (
            <p className="cmdk-empty">{ar ? "جاري البحث…" : "Recherche…"}</p>
          ) : hits.length === 0 ? (
            <p className="cmdk-empty">
              {q.trim().length < 2
                ? ar
                  ? "اكتب حرفين على الأقل"
                  : "Tapez au moins 2 caractères"
                : ar
                  ? "لا نتائج"
                  : "Aucun résultat"}
            </p>
          ) : (
            hits.map((h, i) => (
              <button
                key={`${h.kind}-${h.id}`}
                type="button"
                className={cn("cmdk-item", i === active && "is-active")}
                onMouseEnter={() => setActive(i)}
                onClick={() => go(h)}
              >
                <span className="cmdk-kind">{h.kind}</span>
                <span className="cmdk-title">{h.title}</span>
                {h.subtitle ? <span className="cmdk-sub">{h.subtitle}</span> : null}
              </button>
            ))
          )}
        </div>
        <div className="cmdk-foot">
          <span>{ar ? "↑↓ للتنقل · Enter للفتح" : "↑↓ naviguer · Entrée ouvrir"}</span>
          <span>⌘K</span>
        </div>
      </div>
    </div>
  );
}
