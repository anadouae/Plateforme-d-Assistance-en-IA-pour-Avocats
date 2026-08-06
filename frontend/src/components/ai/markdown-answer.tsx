import type { ReactNode } from "react";
import type { Citation } from "@/lib/api";
import { renderAnswerWithLinks } from "@/components/ai/source-links";
import { cn } from "@/lib/utils";

function renderInline(text: string, sources: Citation[], keyPrefix: string): ReactNode[] {
  return renderAnswerWithLinks(text, sources).map((part, i) =>
    typeof part === "string" ? <span key={`${keyPrefix}-${i}`}>{part}</span> : part,
  );
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
    <p key={key} className="my-2 leading-relaxed">
      {renderInline(text, sources, key)}
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
      className={cn("my-2 space-y-1 pl-5", ordered ? "list-decimal" : "list-disc")}
    >
      {items.map((item, i) => (
        <li key={`${key}-li-${i}`} className="leading-relaxed">
          {renderInline(item, sources, `${key}-${i}`)}
        </li>
      ))}
    </Tag>,
  );
}

/** Line-aware Markdown: headings, bullet/numbered lists, paragraphs. */
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
        <h4 key={`${key}-h3-${part++}`} className="mb-1 mt-3 text-sm font-semibold text-sanad-slate">
          {renderInline(t.slice(4), sources, `${key}-h3`)}
        </h4>,
      );
      continue;
    }
    if (t.startsWith("## ")) {
      flushAll();
      nodes.push(
        <h3
          key={`${key}-h2-${part++}`}
          className="mb-2 mt-4 text-base font-semibold text-sanad-slate first:mt-0"
        >
          {renderInline(t.slice(3), sources, `${key}-h2`)}
        </h3>,
      );
      continue;
    }
    if (t.startsWith("# ")) {
      flushAll();
      nodes.push(
        <h2
          key={`${key}-h1-${part++}`}
          className="mb-2 mt-4 text-lg font-bold text-sanad-slate first:mt-0"
        >
          {renderInline(t.slice(2), sources, `${key}-h1`)}
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
  const blocks = text.split(/\n{2,}/);
  return (
    <div className={cn("text-sm text-sanad-slate", className)}>
      {blocks.map((block, i) => renderBlock(block, sources, `block-${i}`))}
    </div>
  );
}
