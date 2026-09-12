"""Extract legal article citations from Moroccan plea text (heuristic)."""

from __future__ import annotations

import re

# Art. / المادة + number + optional code name
_CITATION_RE = re.compile(
    r"(?:"
    r"(?:art(?:icle)?\.?\s*|المادة\s*)(\d+(?:\s*(?:bis|ter|quater))?)"
    r"(?:\s*(?:du|de\s+la|des|من)?\s*)?"
    r"(DOC|CPC|CM|C\.?\s*T(?:ravail)?|Code\s+du\s+travail|"
    r"مدونة\s+الأسرة|ق\.?\s*م\.?\s*م|قانون\s+المسطرة\s+المدنية|"
    r"مدونة\s+التجارة|قانون\s+الالتزامات)?"
    r"|"
    r"(DOC|CPC|CM|مدونة\s+الأسرة|ق\.?\s*م\.?\s*م)"
    r"\s*(?:art(?:icle)?\.?\s*|المادة\s*)?(\d+)"
    r")",
    re.IGNORECASE,
)

_CODE_NORM = {
    "doc": "DOC (مدونة الأسرة)",
    "مدونة الأسرة": "DOC (مدونة الأسرة)",
    "cpc": "CPC (ق.م.م)",
    "ق.م.م": "CPC (ق.م.م)",
    "قانون المسطرة المدنية": "CPC (ق.م.م)",
    "cm": "مدونة التجارة",
    "مدونة التجارة": "مدونة التجارة",
    "ct": "Code du travail",
    "c.travail": "Code du travail",
    "code du travail": "Code du travail",
}


def extract_citations(body: str, *, limit: int = 40) -> list[dict]:
    if not body or not body.strip():
        return []
    seen: set[str] = set()
    out: list[dict] = []
    for m in _CITATION_RE.finditer(body):
        g = m.groups()
        art = None
        code = None
        if g[0]:
            art = g[0].strip()
            code = (g[1] or "").strip() or None
        elif g[2]:
            code = g[2].strip()
            art = (g[3] or "").strip() or None
        if not art:
            continue
        code_key = (code or "").lower().replace(" ", "")
        code_label = None
        for k, v in _CODE_NORM.items():
            if k.replace(" ", "") in code_key or code_key in k.replace(" ", ""):
                code_label = v
                break
        if not code_label and code:
            code_label = code
        label = f"Art. {art}" + (f" — {code_label}" if code_label else "")
        key = label.lower()
        if key in seen:
            continue
        seen.add(key)
        start = max(0, m.start() - 40)
        end = min(len(body), m.end() + 80)
        excerpt = body[start:end].replace("\n", " ").strip()
        out.append(
            {
                "label": label,
                "article": art,
                "code": code_label,
                "excerpt": excerpt[:240],
                "verified": False,
                "hint": "À vérifier sur le texte officiel (BO / adala.justice.gov.ma)",
            }
        )
        if len(out) >= limit:
            break
    return out
