"""Benchmark runner — 50 Moroccan legal questions (style Kanoun)."""

import json
from datetime import datetime, timezone
from pathlib import Path

from app.services.agent import route_and_answer
from app.services.rag import search_legal_corpus

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RESULTS_PATH = DATA_DIR / "benchmark_results.json"


def load_questions() -> list[dict]:
    path = DATA_DIR / "benchmark_questions.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _score_answer(question: dict, hits: list[dict], result) -> dict:
    expected_id = question.get("expected_source", "")
    expected_kw = [k.lower() for k in question.get("expected_keywords", [])]

    source_match = any(h.get("entry_id") == expected_id for h in hits)
    answer_lower = (result.answer or "").lower()
    kw_found = sum(1 for k in expected_kw if k in answer_lower)
    kw_score = (kw_found / len(expected_kw) * 100) if expected_kw else 0

    confidence = result.confidence_score if result else 0
    overall = 0
    if source_match:
        overall += 50
    overall += int(kw_score * 0.3)
    overall += int(confidence * 0.2)
    overall = min(100, overall)

    return {
        "id": question["id"],
        "domain": question.get("domain", ""),
        "question": question["question"],
        "expected_source": expected_id,
        "source_found": source_match,
        "keywords_matched": kw_found,
        "keywords_total": len(expected_kw),
        "confidence": confidence,
        "source_type": result.source_type if result else "none",
        "score": overall,
        "passed": overall >= 60,
    }


def run_benchmark(limit: int | None = None) -> dict:
    questions = load_questions()
    if limit:
        questions = questions[:limit]

    results = []
    for q in questions:
        hits = search_legal_corpus(q["question"])
        agent_result = route_and_answer(q["question"])
        results.append(_score_answer(q, hits, agent_result))

    passed = sum(1 for r in results if r["passed"])
    avg_score = sum(r["score"] for r in results) / len(results) if results else 0
    by_domain: dict[str, list] = {}
    for r in results:
        by_domain.setdefault(r["domain"], []).append(r["score"])

    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "pass_rate_pct": round(passed / len(results) * 100, 1) if results else 0,
        "avg_score": round(avg_score, 1),
        "by_domain": {
            d: round(sum(s) / len(s), 1) for d, s in by_domain.items()
        },
        "kanoun_reference": "Kanoun claims > ChatGPT on 50 MA legal questions",
        "results": results,
    }

    RESULTS_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def get_last_results() -> dict | None:
    if not RESULTS_PATH.exists():
        return None
    return json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
