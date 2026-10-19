import type { ReactNode } from "react";
import type { Citation } from "@/lib/api";
import { renderAnswerWithLinks } from "@/components/ai/source-links";
import { cn } from "@/lib/utils";

/** Inline: **gras**, *italique*, `code`, puis liens [n]. */
function renderInlineMarkdown(
  text: string,
  sources: Citation[],
  keyPrefix: string,
): ReactNode[] {
  const nodes: ReactNode[] = [];
  // Split on **bold**, *italic*, `code` (ordre: bold avant italic)
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let last = 0;
  let i = 0;
  for (const m of text.matchAll(re)) {
    const idx = m.index ?? 0;
    if (idx > last) {
      nodes.push(
        ...renderAnswerWithLinks(text.slice(last, idx), sources).map((p, j) =>
          typeof p === "string" ? (
            <span key={`${keyPrefix}-t-${i}-${j}`}>{p}</span>
          ) : (
            p
          ),
        ),
      );
    }
    const token = m[0];
    if (token.startsWith("**") && token.endsWith("**")) {
      nodes.push(
        <strong
          key={`${keyPrefix}-b-${i++}`}
          className="font-semibold text-sanad-navy"
        >
          {token.slice(2, -2)}
        </strong>,
      );
    } else if (token.startsWith("*") && token.endsWith("*")) {
      nodes.push(
        <em key={`${keyPrefix}-i-${i++}`} className="italic text-slate-700">
          {token.slice(1, -1)}
        </em>,
      );
    } else if (token.startsWith("`") && token.endsWith("`")) {
      nodes.push(
        <code
          key={`${keyPrefix}-c-${i++}`}
          className="rounded bg-slate-100 px-1 py-0.5 font-mono text-[0.85em] text-sky-800"
        >
          {token.slice(1, -1)}
        </code>,
      );
    }
    last = idx + token.length;
  }
  if (last < text.length) {
    nodes.push(
      ...renderAnswerWithLinks(text.slice(last), sources).map((p, j) =>
        typeof p === "string" ? (
          <span key={`${keyPrefix}-e-${j}`}>{p}</span>
        ) : (
          p
        ),
      ),
    );
  }
  return nodes.length ? nodes : [<span key={`${keyPrefix}-empty`}>{text}</span>];
}

function flushParagraph(
  lines: string[],
  sources: Citation[],
  key: string,
  out: ReactNode[],
) {
  const text = lines.join("\n").trim();
  if (!text) return;
  out.push(
    <p key={key} className="my-2 leading-relaxed text-slate-700">
      {renderInlineMarkdown(text, sources, key)}
    </p>,
  );
}

function flushList(
  items: string[],
  sources: Citation[],
  key: string,
  out: ReactNode[],
  ordered: boolean,
) {
  if (items.length === 0) return;
  const Tag = ordered ? "ol" : "ul";
  out.push(
    <Tag
      key={key}
      className={cn(
        "my-2 list-outside space-y-1.5 ps-5 text-slate-700",
        ordered ? "list-decimal marker:font-semibold marker:text-sanad-navy" : "list-disc marker:text-sanad-blue",
      )}
    >
      {items.map((item, i) => (
        <li key={`${key}-li-${i}`} className="leading-relaxed ps-1">
          {renderInlineMarkdown(item, sources, `${key}-${i}`)}
        </li>
      ))}
    </Tag>,
  );
}

/** Line-aware Markdown: headings, bullet/numbered lists, paragraphs, bold. */
function renderBlock(
  block: string,
  sources: Citation[],
  key: string,
): ReactNode {
  const trimmed = block.trim();
  if (!trimmed) return null;

  const lines = trimmed.split("\n");
  const nodes: ReactNode[] = [];
  let para: string[] = [];
  let bullets: string[] = [];
  let numbers: string[] = [];
  let part = 0;

  const flushAll = () => {
    flushParagraph(para, sources, `${key}-p-${part++}`, nodes);
    para = [];
    flushList(bullets, sources, `${key}-ul-${part++}`, nodes, false);
    bullets = [];
    flushList(numbers, sources, `${key}-ol-${part++}`, nodes, true);
    numbers = [];
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    const t = line.trim();
    if (!t) {
      flushAll();
      continue;
    }

    if (t.startsWith("### ")) {
      flushAll();
      nodes.push(
        <h4
          key={`${key}-h3-${part++}`}
          className="mb-1 mt-3 text-sm font-semibold text-sky-900"
        >
          {renderInlineMarkdown(t.slice(4), sources, `${key}-h3`)}
        </h4>,
      );
      continue;
    }
    if (t.startsWith("## ")) {
      flushAll();
      nodes.push(
        <h3
          key={`${key}-h2-${part++}`}
          className="mb-2 mt-4 border-b border-sanad-border/60 pb-1 text-base font-semibold text-sanad-navy first:mt-0"
        >
          {renderInlineMarkdown(t.slice(3), sources, `${key}-h2`)}
        </h3>,
      );
      continue;
    }
    if (t.startsWith("# ")) {
      flushAll();
      nodes.push(
        <h2
          key={`${key}-h1-${part++}`}
          className="mb-2 mt-4 text-lg font-bold text-sanad-navy first:mt-0"
        >
          {renderInlineMarkdown(t.slice(2), sources, `${key}-h1`)}
        </h2>,
      );
      continue;
    }

    const bullet = t.match(/^[-*•]\s+(.+)$/);
    if (bullet) {
      flushParagraph(para, sources, `${key}-p-${part++}`, nodes);
      para = [];
      flushList(numbers, sources, `${key}-ol-${part++}`, nodes, true);
      numbers = [];
      bullets.push(bullet[1]);
      continue;
    }

    const numbered = t.match(/^\d+[.)]\s+(.+)$/);
    if (numbered) {
      flushParagraph(para, sources, `${key}-p-${part++}`, nodes);
      para = [];
      flushList(bullets, sources, `${key}-ul-${part++}`, nodes, false);
      bullets = [];
      numbers.push(numbered[1]);
      continue;
    }

    flushList(bullets, sources, `${key}-ul-${part++}`, nodes, false);
    bullets = [];
    flushList(numbers, sources, `${key}-ol-${part++}`, nodes, true);
    numbers = [];
    para.push(t);
  }

  flushAll();
  if (nodes.length === 0) return null;
  if (nodes.length === 1) return nodes[0];
  return <div key={key}>{nodes}</div>;
}

export function MarkdownAnswer({
  text,
  sources = [],
  className,
}: {
  text: string;
  sources?: Citation[];
  className?: string;
}) {
  const cleaned = (text || "")
    .replace(/\r\n/g, "\n")
    .replace(/```[\w]*\n?/g, "")
    .trim();
  const blocks = cleaned.split(/\n{2,}/);
  return (
    <div className={cn("text-sm text-sanad-slate", className)}>
      {blocks.map((block, i) => renderBlock(block, sources, `block-${i}`))}
    </div>
  );
}
