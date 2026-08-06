from pathlib import Path

src = Path(__file__).resolve().parents[1] / "backend" / "app" / "services" / "agent.py.recovered"
text = src.read_text(encoding="utf-8")

old = """    from app.services.language import (
        is_greeting,
        is_recent_law_query,
        msg_greeting,
        msg_no_sources,
        msg_recent_laws_not_indexed,
        normalize_locale,
        resolve_response_language,
    )

    locale = resolve_response_language(question, language)

    if is_greeting(question):
        greet_locale = detect_language(question, fallback=locale)
        return AgentResult(answer=msg_greeting(greet_locale), source_type="system", sources=[], confidence_score=0)

    if is_unclear_question(question):
        return AgentResult(
            answer=msg_unclear_question(locale),
            source_type="system",
            sources=[],
            confidence_score=0,
        )

    year_filter = extract_year_filter(question)
    recent = is_recent_law_query(question)
        return answer_from_document_rag(
            question,
            cabinet_id,
            case_id,
            document_id,
            document_name,
            fallback_text=document_text or "",
            language=locale,
        )
"""

new = """    from app.services.language import (
        detect_language,
        extract_year_filter,
        is_greeting,
        is_recent_law_query,
        is_unclear_question,
        msg_greeting,
        msg_no_sources,
        msg_recent_laws_not_indexed,
        msg_unclear_question,
        resolve_response_language,
    )

    locale = resolve_response_language(question, language)

    if is_greeting(question):
        greet_locale = detect_language(question, fallback=locale)
        return AgentResult(answer=msg_greeting(greet_locale), source_type="system", sources=[], confidence_score=0)

    if is_unclear_question(question):
        return AgentResult(
            answer=msg_unclear_question(locale),
            source_type="system",
            sources=[],
            confidence_score=0,
        )

    year_filter = extract_year_filter(question)
    recent = is_recent_law_query(question)

    if document_id and cabinet_id and case_id and document_name:
        return answer_from_document_rag(
            question,
            cabinet_id,
            case_id,
            document_id,
            document_name,
            fallback_text=document_text or "",
            language=locale,
        )
"""

if old not in text:
    raise SystemExit("route_and_answer block not found")
text = text.replace(old, new, 1)

needle = "    # Recherche parallèle : réformes récentes + web (+ corpus sauf requêtes « lois récentes »)\n"
insert = (
    "    year_filter = extract_year_filter(question)\n"
    "    recent = is_recent_law_query(question)\n\n"
    + needle
)
marker_check = (
    "year_filter = extract_year_filter(question)\n"
    "    recent = is_recent_law_query(question)\n\n"
    "    # Recherche parallèle"
)
if marker_check not in text:
    if needle not in text:
        raise SystemExit("parallel search marker not found")
    text = text.replace(needle, insert, 1)

marker = "def generate_synthesis(document_name: str, text: str) -> dict:"
idx = text.find(marker)
if idx < 0:
    raise SystemExit("generate_synthesis not found")

tail = Path(__file__).with_name("agent_tail.py").read_text(encoding="utf-8")
text = text[:idx] + tail

out = src.with_name("agent.py")
out.write_text(text, encoding="utf-8")
compile(text, str(out), "exec")
print("OK wrote", out, "bytes", out.stat().st_size)
