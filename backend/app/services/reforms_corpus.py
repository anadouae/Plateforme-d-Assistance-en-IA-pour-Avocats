"""Réformes législatives marocaines récentes (2016–2026) — source structurée."""

import json
from pathlib import Path

from app.schemas import Citation
from app.services.citation_urls import SGG_BULLETIN
from app.services.topic_filter import filter_reforms_by_topic, is_generic_recent_laws_query

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "reforms_ma_2016_2026.json"


def load_reforms() -> list[dict]:
    if not DATA_PATH.exists():
        return []
    try:
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def search_reforms(
    question: str = "",
    years_back: int = 10,
    locale: str = "fr",
    year_filter: list[int] | None = None,
) -> tuple[str, list[Citation], int]:
    """Return reforms entries as sources + combined text for LLM.

    - Question générique (« dernières lois Maroc ») → liste récente.
    - Question thématique (« قانون الحيوانات ») → seulement les réformes du thème
      (sinon vide — pas de dump hors sujet).
    """
    from datetime import datetime

    reforms = load_reforms()
    if not reforms:
        return "", [], 0

    if year_filter:
        filtered = [r for r in reforms if r.get("year") in year_filter]
    else:
        current_year = datetime.now().year
        min_year = current_year - years_back
        filtered = [r for r in reforms if r.get("year", 0) >= min_year]
    filtered.sort(key=lambda r: r.get("year", 0), reverse=True)

    if not filtered:
        return "", [], 0

    # Filtre thématique : ne jamais coller toute la liste sur un sujet précis
    if question and not is_generic_recent_laws_query(question):
        filtered = filter_reforms_by_topic(filtered, question)
        if not filtered:
            return "", [], 0
    else:
        # Liste générique / panorama année : plus large si filtre année
        limit = 14 if year_filter else 8
        filtered = filtered[:limit]

    is_ar = locale == "ar"
    citations: list[Citation] = []
    parts: list[str] = []

    for i, r in enumerate(filtered, 1):
        title = r["title_ar"] if is_ar else r["title_fr"]
        summary = r["summary_ar"] if is_ar else r["summary_fr"]
        label = f"{r['instrument']} ({r['year']}) — {title}"
        excerpt = summary
        citations.append(Citation(label=label, excerpt=excerpt, url=SGG_BULLETIN))
        parts.append(
            f"[{i}] {r['instrument']} ({r['year']}) — {title}\n"
            f"Domaine : {r.get('domain', '')}\n{summary}"
        )

    combined = "\n\n".join(parts)
    confidence = min(82, 50 + len(filtered) * 4)
    return combined, citations, confidence
