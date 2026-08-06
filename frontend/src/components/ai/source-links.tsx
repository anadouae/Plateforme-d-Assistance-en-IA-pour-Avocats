import type { ReactNode } from "react";
import { ExternalLink } from "lucide-react";
import type { Citation } from "@/lib/api";

const REF_RE = /\[(\d+)\]/g;

function citationUrl(src: Citation): string | null {
  if (src.url) return src.url;
  const match = src.label.match(/https?:\/\/[^\s—]+/);
  return match ? match[0].replace(/[.,)]+$/, "") : null;
}

function displayLabel(label: string): string {
  return label.replace(/\s*—\s*https?:\/\/\S+$/, "").trim();
}

export function renderAnswerWithLinks(
  answer: string,
  sources: Citation[],
): ReactNode[] {
  const parts: ReactNode[] = [];
  let last = 0;
  let key = 0;

  for (const match of answer.matchAll(REF_RE)) {
    const idx = match.index ?? 0;
    if (idx > last) {
      parts.push(answer.slice(last, idx));
    }
    const n = Number(match[1]);
    const src = sources[n - 1];
    const href = src ? citationUrl(src) : null;
    if (href) {
      parts.push(
        <a
          key={`ref-${key++}`}
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium text-sanad-blue hover:underline"
          title={src ? displayLabel(src.label) : undefined}
        >
          [{n}]
        </a>,
      );
    } else {
      parts.push(match[0]);
    }
    last = idx + match[0].length;
  }

  if (last < answer.length) {
    parts.push(answer.slice(last));
  }
  return parts.length ? parts : [answer];
}

export function SourceCitationCard({ src, index }: { src: Citation; index: number }) {
  const href = citationUrl(src);
  const title = displayLabel(src.label);

  return (
    <div className="rounded-lg border border-sanad-border bg-white p-3 text-sm">
      <div className="flex items-start justify-between gap-2">
        {href ? (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 font-medium text-sanad-blue hover:underline"
          >
            <span>
              [{index + 1}] {title}
            </span>
            <ExternalLink className="h-3.5 w-3.5 shrink-0" />
          </a>
        ) : (
          <p className="font-medium text-sanad-blue">
            [{index + 1}] {title}
          </p>
        )}
      </div>
      {src.excerpt && (
        <p className="mt-1 text-slate-600 line-clamp-2">{src.excerpt}</p>
      )}
    </div>
  );
}
