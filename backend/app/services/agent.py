import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from app.core.config import settings
from app.schemas import Citation
from app.services.rag import search_case_documents, search_document_by_id, search_legal_corpus, is_ohada_question
from app.services.corpus_graph import find_graph_for_hits
from app.services.web_search import search_web, search_web_for_recent_laws
from app.services.citation_urls import resolve_citation_url
from app.services.reforms_corpus import search_reforms

logger = logging.getLogger(__name__)

_OCR_ATTENTION_RE = re.compile(
    r"(OCR|ocr|استخراج جزئي|جودة الاستخراج|ré-?extra|réextra|"
    r"qualité d.?extraction|extraction quality|مشوش|brouill)",
    re.I,
)


def _sanitize_attention_points(points: list, *, drop_ocr_noise: bool) -> list[str]:
    """Drop false OCR / extraction-quality warnings when the source is native Word."""
    out: list[str] = []
    for p in points or []:
        s = str(p or "").strip()
        if not s:
            continue
        if drop_ocr_noise and _OCR_ATTENTION_RE.search(s):
            continue
        out.append(s)
    return out


@dataclass
class AgentResult:
    answer: str
    source_type: str
    sources: list[Citation]
    confidence_score: int
    summary: str = ""


def _enrich_citations(citations: list[Citation]) -> list[Citation]:
    return [
        Citation(
            label=c.label,
            excerpt=c.excerpt,
            url=c.url or resolve_citation_url(c.label, c.excerpt),
        )
        for c in citations
    ]


def _with_urls(result: AgentResult) -> AgentResult:
    if not result.sources:
        return result
    return AgentResult(
        answer=result.answer,
        source_type=result.source_type,
        sources=_enrich_citations(result.sources),
        confidence_score=result.confidence_score,
        summary=result.summary,
    )


def _hits_to_citations(hits: list[dict]) -> list[Citation]:
    out: list[Citation] = []
    for h in hits:
        label = h["source"]
        excerpt = h["text"][:300]
        out.append(
            Citation(
                label=label,
                excerpt=excerpt,
                url=resolve_citation_url(label, excerpt),
            )
        )
    return out


def _merge_citations(*groups: list[Citation]) -> list[Citation]:
    seen: set[str] = set()
    merged: list[Citation] = []
    for group in groups:
        for c in group:
            key = c.label.strip().lower()
            if key and key not in seen:
                seen.add(key)
                merged.append(c)
    return merged


def _sources_text(citations: list[Citation], hits: list[dict] | None = None) -> str:
    parts: list[str] = []
    if hits:
        for h in hits[:6]:
            parts.append(f"[CORPUS — {h['source']}] {h['text'][:1200]}")
    for c in citations[:8]:
        excerpt = (c.excerpt or "")[:900]
        parts.append(f"[{c.label}] {excerpt}")
    return "\n\n".join(parts)


def _synthesize_from_sources(
    question: str,
    citations: list[Citation],
    source_type: str,
    confidence: int,
    language: str = "fr",
    hits: list[dict] | None = None,
    extra_sources_text: str = "",
    custom_prompt: str | None = None,
    llm_provider: str | None = None,
) -> AgentResult | None:
    from app.services.local_llm import synthesize_structured_answer_sync

    if not citations and not extra_sources_text:
        return None

    text = extra_sources_text
    body = _sources_text(citations, hits=hits)
    if body:
        text = f"{text}\n\n{body}".strip() if text else body

    structured = synthesize_structured_answer_sync(
        question,
        text,
        language=language,
        custom_prompt=custom_prompt,
        llm_provider=llm_provider,
    )
    if structured:
        return AgentResult(
            answer=structured["answer"],
            source_type=source_type,
            sources=citations,
            confidence_score=min(92, confidence + 12),
            summary=structured.get("summary", ""),
        )

    logger.warning("LLM synthesis failed for question (provider=%s)", llm_provider)
    return None


def direct_reforms_answer(
    citations: list[Citation],
    locale: str = "fr",
    year_filter: list[int] | None = None,
) -> tuple[str, str]:
    """Réponse directe sans LLM — secours uniquement."""
    if not citations:
        return "", ""

    if locale == "ar":
        intro = (
            f"الإصلاحات المغربية لسنة {year_filter[0]}:\n\n"
            if year_filter
            else "أبرز الإصلاحات والقوانين المغربية:\n\n"
        )
        summary_intro = "ملخص: "
        joiner = "\n"
    else:
        intro = (
            f"Textes législatifs marocains publiés en {year_filter[0]} :\n\n"
            if year_filter
            else "Principales réformes législatives marocaines :\n\n"
        )
        summary_intro = "En résumé : "
        joiner = "\n"

    lines = []
    for i, c in enumerate(citations, 1):
        lines.append(f"[{i}] {c.label} — {c.excerpt}")

    answer = intro + joiner.join(lines)
    summary = summary_intro + citations[0].excerpt
    if len(citations) > 1:
        summary += f" {'و' if locale == 'ar' else 'et'} {citations[1].label.split('—')[0].strip()}."
    return answer, summary


def _infer_source_type(has_corpus: bool, has_web: bool) -> str:
    if has_corpus and has_web:
        return "rag+web"
    if has_web:
        return "web"
    return "rag"

    if has_corpus and has_web:
        return "rag+web"
    if has_web:
        return "web"
    return "rag"


def _enhance_with_llm(
    question: str,
    result: AgentResult,
    language: str = "fr",
    llm_provider: str | None = None,
) -> AgentResult:
    from app.services.local_llm import generate_from_sources_sync

    sources_text = "\n\n".join(f"[{s.label}] {s.excerpt}" for s in result.sources)
    if not sources_text:
        return result

    llm_answer = generate_from_sources_sync(
        question, sources_text, language=language, llm_provider=llm_provider
    )
    if llm_answer:
        return AgentResult(
            answer=llm_answer,
            source_type=result.source_type,
            sources=result.sources,
            confidence_score=min(95, result.confidence_score + 5),
            summary=result.summary,
        )
    return result


def _honesty_no_sources(locale: str) -> AgentResult:
    from app.services.language import msg_no_sources

    return AgentResult(
        answer=msg_no_sources(locale),
        source_type="none",
        sources=[],
        confidence_score=0,
    )


def _honesty_topic_not_found(
    locale: str,
    question: str,
    portal: Citation | None = None,
    llm_provider: str | None = None,
    custom_prompt: str | None = None,
) -> AgentResult:
    """Réponse CLAIRE style Groq/Kimi, sans inventer de n° de loi (fallback template)."""
    from app.services.language import msg_no_reliable_sources_for_topic
    from app.services.local_llm import generate_clear_ungrounded_sync
    from app.services.topic_filter import tokenize_question

    tokens = sorted(tokenize_question(question), key=len, reverse=True)
    hint = tokens[0] if tokens else ""
    sources = [portal] if portal else []

    data = generate_clear_ungrounded_sync(
        question,
        language=locale,
        custom_prompt=custom_prompt,
        llm_provider=llm_provider,
    )
    if data and data.get("answer"):
        answer = data["answer"]
        # Garde-fou : si le LLM invente quand même un n°, retirer ces refs
        if _answer_has_unsupported_law_refs(answer, ""):
            import re

            answer = re.sub(
                r"(?:loi|قانون|law)\s*(?:n[°o.]?\s*)?\d{1,3}\s*[-–]\s*\d{1,3}",
                "un texte à vérifier au Bulletin officiel",
                answer,
                flags=re.I,
            )
            answer = re.sub(r"\b\d{1,3}\s*[-–]\s*\d{1,3}\b", "[réf. à vérifier]", answer)
        return AgentResult(
            answer=answer,
            source_type="chat",
            sources=sources,
            confidence_score=35,
            summary=data.get("summary", ""),
        )

    return AgentResult(
        answer=msg_no_reliable_sources_for_topic(locale, hint),
        source_type="system",
        sources=sources,
        confidence_score=20,
        summary="",
    )


def _extract_law_refs(text: str) -> set[str]:
    """Numéros de loi du type 22-24, 21-17, Loi 09-08."""
    import re

    refs: set[str] = set()
    for m in re.finditer(r"\b(\d{1,3})\s*[-–]\s*(\d{1,3})\b", text or ""):
        refs.add(f"{m.group(1)}-{m.group(2)}")
    return refs


def _answer_has_unsupported_law_refs(answer: str, sources_blob: str) -> bool:
    """True si la réponse cite un n° de loi absent des sources."""
    cited = _extract_law_refs(answer)
    if not cited:
        return False
    blob = (sources_blob or "").lower().replace("–", "-")
    for ref in cited:
        if ref.lower() not in blob:
            return True
    return False


def _guard_result_against_invention(
    result: AgentResult,
    question: str,
    locale: str,
    sources_blob: str = "",
    llm_provider: str | None = None,
    custom_prompt: str | None = None,
) -> AgentResult:
    """Couche 4 : si invention de n° de loi → réécriture claire (pas un message sec)."""
    blob = sources_blob or "\n".join(
        f"{c.label} {c.excerpt} {c.url or ''}" for c in (result.sources or [])
    )
    if not _answer_has_unsupported_law_refs(result.answer, blob):
        return result
    portal = result.sources[0] if result.sources else None
    return _honesty_topic_not_found(
        locale,
        question,
        portal,
        llm_provider=llm_provider,
        custom_prompt=custom_prompt,
    )


def answer_from_open_chat(
    question: str,
    language: str = "fr",
    custom_prompt: str | None = None,
    llm_provider: str | None = None,
    soft_citations: list[Citation] | None = None,
    soft_hits: list[dict] | None = None,
) -> AgentResult | None:
    """Mode chat_libre : LLM cloud rédige ; sources = contexte optionnel."""
    from app.services.local_llm import generate_open_chat_sync

    soft_text = ""
    citations = soft_citations or []
    if soft_hits or citations:
        soft_text = _sources_text(citations, hits=soft_hits)
    data = generate_open_chat_sync(
        question,
        language=language,
        custom_prompt=custom_prompt,
        llm_provider=llm_provider,
        soft_context=soft_text,
    )
    if not data:
        return None
    return AgentResult(
        answer=data["answer"],
        source_type="chat" if not citations else "rag+chat",
        sources=citations[:6],
        confidence_score=70 if citations else 55,
        summary=data.get("summary", ""),
    )


def answer_from_hits(
    question: str,
    hits: list[dict],
    source_type: str,
) -> AgentResult | None:
    if not hits:
        return None

    best_score = max(h["score"] for h in hits)
    citations = _hits_to_citations(hits)
    combined = "\n\n".join(f"**{h['source']}** : {h['text']}" for h in hits[:3])

    related_lines = []
    for h in hits[:2]:
        for rel in h.get("related_articles", [])[:3]:
            related_lines.append(f"- {rel['label']} ({rel.get('instrument', '')})")
    related_block = ""
    if related_lines:
        related_block = "\n\n**Articles liés (cartographie)** :\n" + "\n".join(related_lines)

    answer = (
        f"Voici les éléments pertinents trouvés pour votre question :\n\n{combined}"
        f"{related_block}\n\n"
        "Cette réponse est fondée exclusivement sur les sources identifiées ci-dessus."
    )
    return AgentResult(
        answer=answer,
        source_type=source_type,
        sources=citations,
        confidence_score=best_score,
    )


def answer_from_document_rag(
    question: str,
    cabinet_id: str,
    case_id: str,
    document_id: str,
    document_name: str,
    fallback_text: str = "",
    language: str = "fr",
    custom_prompt: str | None = None,
    llm_provider: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> AgentResult:
    from app.services.extraction import get_document_context_excerpt
    from app.services.language import get_disclaimer, msg_doc_not_found, normalize_locale
    from app.services.local_llm import generate_document_answer_sync

    locale = normalize_locale(language)
    text = fallback_text or ""

    llm_answer = generate_document_answer_sync(
        question,
        document_name,
        text,
        language=locale,
        llm_provider=llm_provider,
        history=history,
    )
    if llm_answer:
        excerpt = get_document_context_excerpt(text, question, max_len=500)
        return AgentResult(
            answer=llm_answer,
            source_type="document",
            sources=[Citation(label=document_name, excerpt=excerpt[:300] or text[:300])],
            confidence_score=88,
        )

    hits = search_document_by_id(cabinet_id, case_id, document_id, question) if case_id else []
    if hits:
        result = answer_from_hits(question, hits, "document")
        if result:
            return _enhance_with_llm(question, result, language=locale)

    if text:
        excerpt = get_document_context_excerpt(text, question, max_len=1200)
        if excerpt:
            # Ne plus coller un mur OCR : message clair + extrait court structuré
            snippets = [s.strip() for s in re.split(r"[.\n]+", excerpt) if len(s.strip()) > 40][:6]
            if locale == "ar":
                bullets = "\n".join(f"- {s[:220]}" for s in snippets) or f"- {excerpt[:400]}"
                answer = (
                    f"## إجابة مؤقتة\n"
                    f"تعذر إكمال التحليل الذكي بالكامل. مقتطفات من « {document_name} » :\n\n"
                    f"{bullets}\n\n"
                    f"**أعد طرح السؤال** للحصول على إجابة منظمة."
                )
            else:
                bullets = "\n".join(f"- {s[:220]}" for s in snippets) or f"- {excerpt[:400]}"
                answer = (
                    f"## Réponse provisoire\n"
                    f"L’analyse IA n’a pas abouti complètement. Extraits de « {document_name} » :\n\n"
                    f"{bullets}\n\n"
                    f"**Renvoyez la question** pour une réponse structurée."
                )
            return AgentResult(
                answer=answer,
                source_type="document",
                sources=[Citation(label=document_name, excerpt=excerpt[:300])],
                confidence_score=45,
            )

    return AgentResult(
        answer=msg_doc_not_found(locale),
        source_type="document",
        sources=[],
        confidence_score=0,
    )


def answer_from_case_rag(
    question: str,
    cabinet_id: str,
    case_id: str,
    case_reference: str,
    language: str = "fr",
) -> AgentResult | None:
    hits = search_case_documents(cabinet_id, case_id, question)
    if not hits:
        return None
    result = answer_from_hits(question, hits, "document")
    if result:
        result = AgentResult(
            answer=result.answer.replace("sources identifiées", f"dossier {case_reference}"),
            source_type=result.source_type,
            sources=result.sources,
            confidence_score=result.confidence_score,
        )
        return _enhance_with_llm(question, result, language=language)
    return None


def answer_from_corpus_rag(
    question: str,
    threshold: int = 60,
    language: str = "fr",
    use_llm: bool = True,
) -> AgentResult | None:
    corpus_filter = "legal_corpus_ohada" if is_ohada_question(question) else None
    hits = search_legal_corpus(question, corpus_filter=corpus_filter)
    if not hits:
        return None
    hits = find_graph_for_hits(hits)
    best = hits[0]["score"]
    if best < 40:
        return None
    source_type = "ohada" if corpus_filter else "rag"
    result = answer_from_hits(question, hits, source_type)
    if not result:
        return None
    if use_llm and best >= threshold:
        return _enhance_with_llm(question, result, language=language)
    return result


def answer_from_web_search(
    question: str,
    language: str = "fr",
    recent: bool = False,
    custom_prompt: str | None = None,
    llm_provider: str | None = None,
) -> AgentResult | None:
    from app.services.language import normalize_locale
    from app.services.local_llm import synthesize_structured_answer_sync, synthesize_web_answer_sync

    from app.services.language import rewrite_question_for_search

    locale = normalize_locale(language)
    search_q = rewrite_question_for_search(question)
    if recent:
        text, citations, score = search_web_for_recent_laws(search_q, locale=locale)
    else:
        text, citations, score = search_web(search_q)

    if not citations:
        return None

    summary = ""
    structured = synthesize_structured_answer_sync(
        question,
        text,
        language=locale,
        custom_prompt=custom_prompt,
        llm_provider=llm_provider,
    )
    if structured:
        answer = structured["answer"]
        summary = structured.get("summary", "")
        confidence = min(82, max(score, 58) + 8)
    elif legacy := synthesize_web_answer_sync(question, text, language=locale):
        answer = (
            f"{legacy}\n\n"
            "**Sources web consultées :**\n"
            + "\n".join(f"- {c.label}" for c in citations[:6])
        )
        confidence = min(82, max(score, 58) + 8)
    else:
        answer = (
            "Recherche web — sources consultées :\n\n"
            f"{text[:2000]}\n\n"
            "Vérifiez chaque URL sur le Bulletin officiel (sgg.gov.ma) avant toute décision."
        )
        confidence = score

    return AgentResult(
        answer=answer,
        source_type="web",
        sources=citations,
        confidence_score=confidence,
        summary=summary,
    )


def _parallel_corpus_and_web(question: str, language: str = "fr") -> tuple[AgentResult | None, AgentResult | None]:
    """Run corpus RAG and web search in parallel for speed."""
    corpus_result: AgentResult | None = None
    web_result: AgentResult | None = None

    def _corpus():
        return answer_from_corpus_rag(question, threshold=40, language=language)

    def _web():
        return answer_from_web_search(question, language=language)

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_corpus = pool.submit(_corpus)
        f_web = pool.submit(_web)
        try:
            corpus_result = f_corpus.result(timeout=8)
        except Exception as exc:
            logger.warning("Parallel corpus failed: %s", exc)
        try:
            web_result = f_web.result(timeout=10)
        except Exception as exc:
            logger.warning("Parallel web failed: %s", exc)

    return corpus_result, web_result


def _merge_hybrid(question: str, corpus_result: AgentResult, web_result: AgentResult, language: str = "fr") -> AgentResult:
    from app.services.local_llm import generate_from_sources_sync
    from app.services.language import normalize_locale

    locale = normalize_locale(language)
    corpus_text = "\n\n".join(f"[{s.label}] {s.excerpt}" for s in corpus_result.sources[:3])
    web_text = "\n\n".join(f"[{s.label}] {s.excerpt}" for s in web_result.sources[:3])
    combined_sources = f"CORPUS JURIDIQUE:\n{corpus_text}\n\nSOURCES WEB:\n{web_text}"

    llm_answer = generate_from_sources_sync(question, combined_sources, language=locale)
    if llm_answer:
        answer = (
            f"{llm_answer}\n\n**Références :** corpus LexHub indexé + sources web (URLs ci-dessous)."
        )
    else:
        answer = (
            f"**Fondement corpus juridique :**\n{corpus_result.answer}\n\n"
            f"**Complément web :**\n{web_result.answer}"
        )

    return AgentResult(
        answer=answer,
        source_type="rag+web",
        sources=corpus_result.sources + web_result.sources,
        confidence_score=max(corpus_result.confidence_score, web_result.confidence_score),
    )


def route_and_answer(
    question: str,
    document_text: str | None = None,
    document_name: str | None = None,
    document_id: str | None = None,
    cabinet_id: str | None = None,
    case_id: str | None = None,
    case_reference: str | None = None,
    excerpt: str | None = None,
    confidence_threshold: int = 60,
    language: str = "fr",
    history: list[dict[str, str]] | None = None,
) -> AgentResult:
    from app.services.language import (
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
        from app.services.language import resolve_greeting_locale

        return AgentResult(
            answer=msg_greeting(resolve_greeting_locale(question, language)),
            source_type="system",
            sources=[],
            confidence_score=0,
        )

    if is_unclear_question(question):
        return AgentResult(
            answer=msg_unclear_question(locale),
            source_type="system",
            sources=[],
            confidence_score=0,
        )

    year_filter = extract_year_filter(question)
    recent = is_recent_law_query(question)

    if document_id and cabinet_id and document_name:
        return answer_from_document_rag(
            question,
            cabinet_id,
            case_id or "",
            document_id,
            document_name,
            fallback_text=document_text or "",
            language=locale,
            history=history,
        )

    if case_id and cabinet_id and not document_id:
        case_result = answer_from_case_rag(
            question, cabinet_id, case_id, case_reference or case_id, language=locale
        )
        if case_result and case_result.confidence_score >= confidence_threshold:
            return case_result

    corpus_result, web_result = _parallel_corpus_and_web(question, language=locale)

    if corpus_result and corpus_result.confidence_score >= confidence_threshold:
        return corpus_result

    if corpus_result and corpus_result.confidence_score >= 40 and web_result and web_result.sources:
        return _merge_hybrid(question, corpus_result, web_result, language=locale)

    if web_result and web_result.sources:
        return web_result

    if corpus_result:
        return corpus_result

    return AgentResult(
        answer=msg_no_sources(locale),
        source_type="none",
        sources=[],
        confidence_score=0,
    )


def route_and_search(
    question: str,
    document_text: str | None = None,
    document_name: str | None = None,
    document_id: str | None = None,
    cabinet_id: str | None = None,
    case_id: str | None = None,
    case_reference: str | None = None,
    language: str = "fr",
    custom_prompt: str | None = None,
    llm_provider: str | None = None,
    conversation_history: list | None = None,
) -> AgentResult:
    """Chat direct style Groq/Kimi : web mondial + LLM cloud (réponses claires)."""
    from app.core.config import settings
    from app.services.direct_chat import answer_like_groq_kimi

    history = [] if settings.AI_EPHEMERAL else (conversation_history or [])

    return answer_like_groq_kimi(
        question,
        language=language,
        custom_prompt=custom_prompt,
        llm_provider=llm_provider,
        document_text=document_text,
        document_name=document_name,
        document_id=document_id,
        cabinet_id=cabinet_id,
        case_id=case_id,
        case_reference=case_reference,
        conversation_history=history,
    )


def _clean_summary_md(summary: str) -> str:
    s = (summary or "").strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[-1]
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
        s = s.strip()
        if s.lower().startswith("markdown"):
            s = s[8:].lstrip()
    return s.strip()


def generate_synthesis(document_name: str, text: str, language: str = "ar") -> dict:
    from app.services.extraction import (
        extract_amounts,
        extract_dates,
        extract_parties,
    )
    from app.services.language import (
        get_disclaimer,
        msg_attention_insufficient,
        msg_insufficient_text,
        normalize_locale,
    )
    from app.services.local_llm import generate_synthesis_structured, generate_synthesis_text

    locale = normalize_locale(language)
    disclaimer = get_disclaimer(locale)

    if not text or len(text.strip()) < 20:
        return {
            "parties": [],
            "key_dates": [],
            "amounts": [],
            "risk_clauses": [],
            "attention_points": [msg_attention_insufficient(locale)],
            "summary": msg_insufficient_text(locale),
            "sources": [],
            "disclaimer": disclaimer,
        }

    from app.services.extraction import (
        is_scrambled_arabic,
        looks_like_native_arabic_prose,
        safe_repair_arabic_text,
    )
    from app.services.arabic_text_fix import audio_transcript_quality

    name_l = (document_name or "").lower()
    is_audio = name_l.endswith((".ogg", ".wav", ".mp3", ".m4a", ".webm", ".mpeg", ".mpga"))
    tq = audio_transcript_quality(text) if is_audio else None

    # DOCX / texte Word natif : ne pas « réparer » ni traiter comme OCR.
    assume_native = (not is_audio) and (
        looks_like_native_arabic_prose(text)
        or name_l.endswith((".docx", ".doc", ".odt", ".rtf"))
    )
    if not assume_native and not is_audio:
        text = safe_repair_arabic_text(text)
    elif is_audio:
        text = (text or "").strip()
    preview = text[:6000].replace("\n", " ")
    scrambled = False if assume_native else is_scrambled_arabic(text)

    llm_data = generate_synthesis_structured(
        document_name,
        text,
        language=locale,
        assume_native=assume_native,
        source_kind="audio" if is_audio else "file",
        transcript_quality=tq,
    )
    if llm_data and llm_data.get("summary"):
        summary = llm_data["summary"]
        # Refuser un « résumé » qui n'est que du texte OCR collé
        if scrambled and len(summary) > 100 and summary[:80] in text[:500]:
            summary = ""
        if summary:
            attention = _sanitize_attention_points(
                list(llm_data.get("attention_points") or []),
                drop_ocr_noise=assume_native or not scrambled,
            )
            if is_audio and tq == "poor":
                warn = {
                    "fr": "Transcription audio peu fiable — ne pas traiter les noms/lieux interprétés comme des faits. Préférez la dictée live ou ré-enregistrez.",
                    "ar": "التفريغ الصوتي غير موثوق — لا تعتمد الأسماء/الأماكن المستنتجة كوقائع. يُفضّل الإملاء المباشر أو إعادة التسجيل.",
                }.get(locale, "التفريغ الصوتي غير موثوق — لا تعتمد الأسماء/الأماكن المستنتجة كوقائع.")
                attention = [warn] + [a for a in attention if a != warn]
            if scrambled and not assume_native and not is_audio and len(text) < 12000:
                attention = [
                    {
                        "fr": "Qualité d'extraction moyenne — vérifier le PDF / ré-extraire.",
                        "ar": "جودة الاستخراج متوسطة — تحقق من PDF أو أعد الاستخراج.",
                        "en": "جودة الاستخراج متوسطة — تحقق من PDF أو أعد الاستخراج.",
                    }.get(locale, "جودة الاستخراج متوسطة — تحقق من PDF أو أعد الاستخراج.")
                ] + attention
            # Si le LLM a répondu : faire confiance à ses listes (même vides).
            # Le regex ne doit PAS remplir avec des n° de lois / phrases arabes inversées.
            parties = [x for x in (llm_data.get("parties") or []) if str(x).strip()]
            dates = [x for x in (llm_data.get("key_dates") or []) if str(x).strip()]
            amounts = [x for x in (llm_data.get("amounts") or []) if str(x).strip()]
            dates = [
                d
                for d in dates
                if not __import__("re").fullmatch(
                    r"\d\.\d{2}\.\d{3}",
                    str(d).replace("/", ".").replace("-", "."),
                )
            ]
            # Pas de « بنود المخاطر » : trop de bruit OCR / mémoires universitaires.
            # Le résumé intelligent suffit ; regex/LLM risks désactivés ici.
            if not parties and not dates and not amounts:
                parties = extract_parties(text)
                dates = extract_dates(text)
                amounts = extract_amounts(text)
            return {
                "parties": parties[:40],
                "key_dates": dates[:40],
                "amounts": amounts[:40],
                "risk_clauses": [],
                "attention_points": attention,
                "summary": _clean_summary_md(summary),
                "sources": [Citation(label=document_name, excerpt=preview[:300])],
                "disclaimer": disclaimer,
            }

    # Secours LLM prose (pas de template programmé)
    summary = generate_synthesis_text(document_name, text, language=locale)
    if summary and not (scrambled and summary[:60] in text[:400]):
        attention: list[str] = []
        if scrambled and not assume_native and len(text) < 12000:
            attention.append(
                {
                    "fr": "Qualité d'extraction moyenne — vérifier le PDF / ré-extraire.",
                    "ar": "جودة الاستخراج متوسطة — تحقق من PDF أو أعد الاستخراج.",
                    "en": "جودة الاستخراج متوسطة — تحقق من PDF أو أعد الاستخراج.",
                }.get(locale, "جودة الاستخراج متوسطة — تحقق من PDF أو أعد الاستخراج.")
            )
        return {
            "parties": extract_parties(text),
            "key_dates": extract_dates(text),
            "amounts": extract_amounts(text),
            "risk_clauses": [],
            "attention_points": attention,
            "summary": _clean_summary_md(summary),
            "sources": [Citation(label=document_name, excerpt=preview[:300])],
            "disclaimer": disclaimer,
        }

    # Dernier recours : message clair (NE PLUS coller le texte brut comme « synthèse »)
    cleaned_text = (text or "").strip()
    _fail = {
        "fr": (
            "## Synthèse IA indisponible\n\n"
            "ChatGPT n'a pas pu produire la synthèse pour cette pièce.\n\n"
            "## Que faire\n"
            "1. Cliquez **Actualiser** pour relancer l'analyse IA.\n"
            "2. Le texte brut reste dans l'aperçu à gauche.\n"
            "3. Aucune information n'a été inventée.\n"
        ),
        "ar": (
            "## تعذر التلخيص الذكي\n\n"
            "تعذر على الذكاء الاصطناعي إعداد التلخيص.\n\n"
            "## ماذا تفعل\n"
            "1. اضغطوا **تحديث**.\n"
            "2. النص المستخرج يبقى على اليسار.\n"
        ),
    }
    attention = []
    if scrambled and not assume_native:
        attention.append(
            {
                "fr": "Texte arabe brouillé — ré-extrayez puis relancez la synthèse.",
                "ar": "نص عربي مشوش — أعد الاستخراج ثم التلخيص.",
            }.get(locale, "Texte arabe brouillé — ré-extrayez puis relancez la synthèse.")
        )
    if len(cleaned_text) >= 80:
        attention.append(
            {
                "fr": "Synthèse IA non générée — relancez Actualiser.",
                "ar": "لم يُنشأ التلخيص الذكي — أعدوا تحديث.",
            }.get(locale, "Synthèse IA non générée — relancez Actualiser.")
        )
    return {
        "parties": extract_parties(cleaned_text) if cleaned_text else [],
        "key_dates": extract_dates(cleaned_text) if cleaned_text else [],
        "amounts": extract_amounts(cleaned_text) if cleaned_text else [],
        "risk_clauses": [],
        "attention_points": attention,
        "summary": _fail.get(locale, _fail["fr"]),
        "sources": [Citation(label=document_name, excerpt=preview[:300])] if cleaned_text else [],
        "disclaimer": disclaimer,
    }




def generate_case_analysis(
    case_reference: str,
    cabinet_id: str,
    case_id: str,
    documents: list[dict],
    language: str = "fr",
) -> dict:
    """Analyse complète d'un dossier à partir de tous les documents indexés / extraits."""
    from app.services.extraction import extract_amounts, extract_dates, extract_parties
    from app.services.language import get_disclaimer, normalize_locale
    from app.services.local_llm import generate_case_analysis_text

    locale = normalize_locale(language)
    disclaimer = get_disclaimer(locale)

    if not documents:
        empty_msgs = {
            "fr": {
                "facts": "Aucun document disponible dans ce dossier.",
                "checklist": ["Importer et indexer des pièces avant l'analyse"],
                "summary": "Dossier vide — aucune analyse possible.",
            },
            "ar": {
                "facts": "لا توجد وثائق في هذا الملف.",
                "checklist": ["استيراد وفهرسة الوثائق قبل التحليل"],
                "summary": "ملف فارغ — لا يمكن إجراء تحليل.",
            },
            "en": {
                "facts": "No documents available in this case.",
                "checklist": ["Import and index documents before analysis"],
                "summary": "Empty case — no analysis possible.",
            },
        }[locale]
        return {
            "case_reference": case_reference,
            "facts": empty_msgs["facts"],
            "key_documents": [],
            "legal_issues": [],
            "risks_and_deadlines": [],
            "checklist": empty_msgs["checklist"],
            "summary": empty_msgs["summary"],
            "parties": [],
            "key_dates": [],
            "amounts": [],
            "sources": [],
            "confidence_score": 0,
            "disclaimer": disclaimer,
        }

    chunks: list[str] = []
    key_docs: list[str] = []
    parties: list[str] = []
    dates: list[str] = []
    amounts: list[str] = []
    sources: list[Citation] = []

    for doc in documents:
        name = str(doc.get("name") or "document")
        raw = (doc.get("text") or "").strip()
        if not raw:
            continue
        key_docs.append(name)
        parties.extend(extract_parties(raw)[:8])
        dates.extend(extract_dates(raw)[:8])
        amounts.extend(extract_amounts(raw)[:8])
        excerpt = raw[:400].replace("\n", " ")
        chunks.append(f"[{name}]\n{raw[:6000]}")
        sources.append(Citation(label=name, excerpt=excerpt))

    def _uniq(items: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for item in items:
            key = item.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(item)
        return out

    parties, dates, amounts = _uniq(parties), _uniq(dates), _uniq(amounts)
    # Plus de contexte pour ChatGPT (toutes les pièces)
    all_text = "\n\n".join(chunks)[:22000]

    # Fallback clair si LLM échoue — pas un collage OCR
    docs_list = "\n".join(f"{i}. **{n}**" for i, n in enumerate(key_docs, 1)) or "—"
    parties_list = "\n".join(f"- {p}" for p in parties[:20]) or "- —"
    dates_list = "\n".join(f"- {d}" for d in dates[:20]) or "- —"
    amounts_list = "\n".join(f"- {a}" for a in amounts[:20]) or "- —"
    if locale == "ar":
        fallback_summary = (
            f"## تحليل الملف {case_reference}\n\n"
            f"تعذر إكمال التحليل الذكي بالكامل. بيانات مستخرجة:\n\n"
            f"### القطع\n{docs_list}\n\n"
            f"### الأطراف\n{parties_list}\n\n"
            f"### التواريخ\n{dates_list}\n\n"
            f"### المبالغ\n{amounts_list}\n\n"
            "### ما يُستحسن فعله\n"
            "1. اضغطوا **تحديث / إعادة التحليل**\n"
            "2. راجعوا القطع في تبويب الوثائق\n"
        )
    else:
        fallback_summary = (
            f"## Analyse du dossier {case_reference}\n\n"
            f"L’analyse IA n’a pas abouti complètement. Données extraites :\n\n"
            f"### Pièces\n{docs_list}\n\n"
            f"### Parties\n{parties_list}\n\n"
            f"### Dates\n{dates_list}\n\n"
            f"### Montants\n{amounts_list}\n\n"
            "### Suite utile\n"
            "1. Cliquez **Lancer l'analyse** à nouveau\n"
            "2. Vérifiez les pièces dans l’onglet Documents\n"
        )

    llm_text = None
    if all_text:
        try:
            llm_text = generate_case_analysis_text(
                case_reference, all_text, language=locale
            )
        except Exception as exc:
            logger.warning("generate_case_analysis_text failed: %s", exc)
            llm_text = None
    summary = llm_text or fallback_summary

    # Pas de RAG embeddings ici (peut bloquer longtemps) — analyse locale uniquement
    legal_issues: list[str] = []
    risks: list[str] = []
    if not key_docs:
        legal_issues = [
            "Aucune pièce extractible — importer des documents avant une analyse approfondie"
            if locale != "ar"
            else "لا توجد قطع قابلة للاستخراج — استورد وثائق قبل تحليل أعمق"
        ]
    else:
        legal_issues = [
            f"Pièce à relire : {n}" if locale != "ar" else f"قطعة للمراجعة: {n}"
            for n in key_docs[:5]
        ]
        risks = [
            "Revue manuelle des délais et des montants recommandée"
            if locale != "ar"
            else "يُستحسن مراجعة يدوية للآجال والمبالغ"
        ]

    checklist = [
        "Vérifier les pièces indexées et leur qualité OCR"
        if locale != "ar"
        else "تحقق من جودة استخراج الوثائق",
        "Contrôler les délais et échéances mentionnés"
        if locale != "ar"
        else "راجع الآجال المذكورة",
        "Confirmer les parties et montants avec le client"
        if locale != "ar"
        else "أكد الأطراف والمبالغ مع الموكل",
    ]
    if not llm_text and all_text:
        checklist.insert(
            0,
            "Analyse structurée locale (IA lente/indisponible) — relancer si besoin"
            if locale != "ar"
            else "تحليل محلي منظم (الذكاء بطيء/غير متاح) — أعد التشغيل عند الحاجة",
        )

    confidence = 55 if chunks else 25
    if llm_text:
        confidence = min(90, confidence + 25)

    return {
        "case_reference": case_reference,
        "facts": summary.split("2)")[0].strip() if "2)" in summary else summary[:800],
        "key_documents": key_docs,
        "legal_issues": legal_issues or ["À préciser selon la nature du litige"],
        "risks_and_deadlines": risks
        or ["Aucun risque automatique détecté — revue manuelle recommandée"],
        "checklist": checklist,
        "summary": summary,
        "parties": parties,
        "key_dates": dates,
        "amounts": amounts,
        "sources": sources[:15],
        "confidence_score": confidence,
        "disclaimer": disclaimer,
    }


def finalize_agent_result(result: AgentResult) -> AgentResult:
    return _with_urls(result)


def citations_to_json(sources: list[Citation]) -> str:
    return json.dumps([s.model_dump() for s in sources], ensure_ascii=False)
