"""Chat direct style Groq / Kimi / Cursor — LLM cloud + web mondial."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from app.schemas import Citation

logger = logging.getLogger(__name__)


def answer_like_groq_kimi(
    question: str,
    *,
    language: str = "fr",
    custom_prompt: str | None = None,
    llm_provider: str | None = None,
    document_text: str | None = None,
    document_name: str | None = None,
    document_id: str | None = None,
    cabinet_id: str | None = None,
    case_id: str | None = None,
    case_reference: str | None = None,
    conversation_history: list | None = None,
):
    """
    Pipeline simple (comme Groq chat / Kimi / Cursor) :
    1) chercher sur le web (monde) + corpus léger
    2) envoyer question + extraits au LLM cloud
    3) renvoyer une réponse claire et développée
    """
    from app.services.agent import (
        AgentResult,
        _hits_to_citations,
        _merge_citations,
        _sources_text,
        answer_from_document_rag,
    )
    from app.services.conversation import history_to_chat_messages, resolve_with_history
    from app.services.language import (
        is_greeting,
        is_recent_law_query,
        msg_greeting,
        normalize_locale,
        resolve_greeting_locale,
        resolve_response_language,
    )
    from app.services.local_llm import (
        generate_clear_ungrounded_sync,
        generate_open_chat_sync,
        synthesize_structured_answer_sync,
    )
    from app.services.rag import search_case_documents, search_legal_corpus_fast
    from app.services.reforms_corpus import search_reforms
    from app.services.conversation import is_topic_switch
    from app.services.topic_filter import (
        filter_citations_by_topic,
        filter_hits_by_topic,
        is_animal_law_query,
        is_immobilier_query,
        is_noise_citation,
        is_panorama_laws_query,
        is_thin_legal_context,
    )
    from app.services.web_search import search_web, search_web_for_recent_laws

    locale = resolve_response_language(question, language)
    history = conversation_history or []
    panorama = is_panorama_laws_query(question)
    switched = is_topic_switch(question, history) if history else False
    if panorama:
        switched = True
    search_q, hist_block, is_followup = resolve_with_history(question, history)
    prior_messages = history_to_chat_messages(history)
    # Ancrage sujet : question actuelle d'abord ; historique seulement si PAS de changement de sujet
    animal_topic = False if panorama else (
        is_animal_law_query(question) or is_animal_law_query(search_q)
    )
    if not panorama and not animal_topic and not switched and history and is_followup:
        hist_blob = " ".join((t.get("question") or "") for t in history[-3:])
        animal_topic = is_animal_law_query(hist_blob)
    immo_topic = False if panorama else (
        is_immobilier_query(question) or is_immobilier_query(search_q)
    )
    if animal_topic and immo_topic:
        # Priorité au message actuel
        animal_topic = is_animal_law_query(question)
        immo_topic = is_immobilier_query(question) and not animal_topic

    if is_greeting(question) and not history and not is_followup:
        return AgentResult(
            answer=msg_greeting(resolve_greeting_locale(question, language)),
            source_type="system",
            sources=[],
            confidence_score=0,
        )

    if document_id and cabinet_id and case_id and document_name:
        return answer_from_document_rag(
            question,
            cabinet_id,
            case_id,
            document_id,
            document_name,
            fallback_text=document_text or "",
            language=locale,
            custom_prompt=custom_prompt,
            llm_provider=llm_provider,
        )

    web_citations: list[Citation] = []
    corpus_hits: list[dict] = []
    case_hits: list[dict] = []
    recent = (
        panorama
        or is_recent_law_query(search_q)
        or is_recent_law_query(question)
        or (is_followup and not switched)
        or animal_topic
        or immo_topic
    )
    # Recherche = boost, pas remplacement de la question utilisateur
    if panorama:
        filter_q = (
            "lois adoptées Maroc 2026 Bulletin officiel "
            "loi de finances élections procédure civile Code commerce"
        )
    elif animal_topic:
        filter_q = f"{question} projet loi 19.25 animaux errants Maroc"
    elif immo_topic:
        filter_q = (
            f"{question} droit immobilier Maroc baux 49-16 67-12 "
            "droits réels 39-08 ANCFCC"
        )
    else:
        filter_q = search_q or question

    reform_citations: list[Citation] = []
    reform_text = ""

    def _web():
        nonlocal web_citations
        try:
            if panorama or recent or animal_topic:
                _, citations, _ = search_web_for_recent_laws(
                    filter_q, max_results=12 if panorama else 8, locale=locale
                )
            else:
                _, citations, _ = search_web(filter_q, max_results=6)
            web_citations = citations or []
            if panorama:
                # Enrichir avec plusieurs axes 2026
                extra_queries = [
                    "loi de finances 2026 Maroc",
                    "loi organique élections 2026 Maroc",
                    "Code procédure civile 2026 Maroc Bulletin officiel",
                    "projet loi 71.24 Code commerce Maroc",
                    "loi 19.25 animaux errants Maroc 2026",
                ]
                more_all: list[Citation] = []
                for eq in extra_queries:
                    try:
                        _, more, _ = search_web(eq, max_results=3)
                        if more:
                            more_all.extend(more)
                    except Exception:
                        pass
                if more_all:
                    web_citations = _merge_citations(web_citations, more_all)
            elif (recent or animal_topic) and is_thin_legal_context(web_citations, filter_q):
                _, more, _ = search_web(filter_q, max_results=6)
                if more:
                    web_citations = filter_citations_by_topic(
                        _merge_citations(web_citations, more),
                        filter_q,
                        keep_official_portal=True,
                    )
        except Exception as exc:
            logger.warning("direct web search failed: %s", exc)

    def _corpus():
        nonlocal corpus_hits, reform_citations, reform_text
        try:
            if not panorama:
                raw = search_legal_corpus_fast(filter_q) or []
                topical = filter_hits_by_topic(raw, filter_q)
                # Soft : garder aussi des hits non filtrés si peu de match
                corpus_hits = topical if len(topical) >= 2 else (topical + raw)[:8]
        except Exception as exc:
            logger.warning("direct corpus search failed: %s", exc)
        try:
            if panorama:
                reform_text, reform_citations, _ = search_reforms(
                    "",
                    locale=locale,
                    years_back=2,
                    year_filter=[2025, 2026],
                )
                # Si peu de fiches 2025-26, élargir
                if len(reform_citations) < 3:
                    t2, c2, _ = search_reforms(
                        "réformes législatives Maroc 2026",
                        locale=locale,
                        years_back=3,
                    )
                    if c2:
                        reform_text = (reform_text + "\n\n" + t2).strip()
                        reform_citations = _merge_citations(reform_citations, c2)
            else:
                reform_q = filter_q if (animal_topic or immo_topic) else search_q
                reform_text, reform_citations, _ = search_reforms(
                    reform_q,
                    locale=locale,
                    years_back=25 if immo_topic else 12,
                )
        except Exception as exc:
            logger.warning("direct reforms search failed: %s", exc)

    def _case():
        nonlocal case_hits
        if not (case_id and cabinet_id):
            return
        try:
            raw = search_case_documents(cabinet_id, case_id, filter_q) or []
            case_hits = filter_hits_by_topic(raw, filter_q)
        except Exception as exc:
            logger.warning("direct case search failed: %s", exc)

    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = [pool.submit(_web), pool.submit(_corpus), pool.submit(_case)]
        for f in futs:
            try:
                f.result(timeout=18)
            except Exception as exc:
                logger.warning("direct search worker: %s", exc)

    case_citations = _hits_to_citations(case_hits) if case_hits else []
    corpus_citations = _hits_to_citations(corpus_hits[:5]) if corpus_hits else []
    merged = _merge_citations(reform_citations, case_citations, web_citations, corpus_citations)
    # Soft partout : sources = enrichissement (comme Mistral/Gemini + web)
    all_citations = filter_citations_by_topic(
        [c for c in merged if not is_noise_citation(c, question)],
        question if not panorama else "lois Maroc 2026 finances élections commerce procédure",
        keep_official_portal=True,
        soft=True,
    )
    if panorama and len(all_citations) < 4:
        all_citations = [c for c in merged if not is_noise_citation(c, question)][:14]

    soft = _sources_text(all_citations, hits=None)
    if reform_text:
        soft = f"FICHES RÉFORMES (enrichissement) :\n{reform_text}\n\n{soft}".strip()
    if panorama:
        soft = (
            "L'utilisateur veut un PANORAMA multi-domaines (pas un seul texte). "
            "Liste par domaine avec numéro + résumé ; distingue adopté / discussion / presse.\n\n"
            f"{soft}"
        ).strip()
    if hist_block and not switched:
        soft = f"{hist_block}\n\n{soft}".strip()
    elif hist_block and switched:
        soft = f"{hist_block}\n\n{soft}".strip()
    if document_text and document_name:
        soft = f"[DOCUMENT — {document_name}]\n{document_text[:4000]}\n\n{soft}".strip()

    thin = is_thin_legal_context(all_citations, question)
    has_press = bool(all_citations)

    # Toujours la question BRUTE à l'LLM (comme Mistral chat) — search_q sert au web seulement
    ask = question

    open_ctx = soft if soft.strip() else (
        "Aucune source web indexée pour ce tour. "
        "Réponds comme un excellent chat juridique (cadre, méthode, vigilance) ; "
        "n'invente pas de numéro de loi précis."
    )

    # Chemin principal : chat ouvert enrichi (qualité Mistral/Gemini)
    data = generate_open_chat_sync(
        ask,
        language=locale,
        custom_prompt=custom_prompt,
        llm_provider=llm_provider,
        soft_context=open_ctx,
        prior_messages=prior_messages if not switched else (
            prior_messages[-2:] if prior_messages else None
        ),
    )
    if data and data.get("answer") and len(data["answer"].strip()) > 60:
        st = "rag+web" if (web_citations and (corpus_hits or case_hits or reform_citations)) else (
            "web" if web_citations else ("document" if case_hits else "chat")
        )
        return AgentResult(
            answer=data["answer"],
            source_type=st,
            sources=all_citations[:12],
            confidence_score=72 if has_press else 58,
            summary=data.get("summary", ""),
        )

    # Repli structuré si open chat trop court / échec parse
    if soft.strip():
        structured = synthesize_structured_answer_sync(
            ask,
            soft,
            language=locale,
            custom_prompt=custom_prompt,
            llm_provider=llm_provider,
            prior_messages=prior_messages if not switched else None,
        )
        if structured and structured.get("answer") and len(structured["answer"].strip()) > 80:
            return AgentResult(
                answer=structured["answer"],
                source_type="web" if web_citations else "rag",
                sources=all_citations[:12],
                confidence_score=70 if has_press or not thin else 55,
                summary=structured.get("summary", ""),
            )

    ungrounded = generate_clear_ungrounded_sync(
        ask,
        language=locale,
        custom_prompt=custom_prompt,
        llm_provider=llm_provider,
        prior_messages=prior_messages,
    )
    if ungrounded and ungrounded.get("answer"):
        return AgentResult(
            answer=ungrounded["answer"],
            source_type="chat",
            sources=all_citations[:5],
            confidence_score=45,
            summary=ungrounded.get("summary", ""),
        )

    if all_citations:
        locale_n = normalize_locale(locale)
        intro = {
            "fr": (
                "## Réponse\n\n"
                "Voici ce que la recherche a trouvé "
                "(moteurs cloud momentanément saturés — synthèse automatique) :\n\n"
            ),
            "ar": (
                "## الإجابة\n\n"
                "إليك ما وجدته عبر البحث "
                "(المحركات السحابية مشغولة مؤقتاً — ملخص تلقائي) :\n\n"
            ),
            "en": (
                "## Answer\n\n"
                "Here is what search found "
                "(cloud engines temporarily rate-limited — automatic digest):\n\n"
            ),
        }[locale_n]
        bullets = []
        for i, c in enumerate(all_citations[:6], 1):
            excerpt = (c.excerpt or "").strip()
            if len(excerpt) > 350:
                excerpt = excerpt[:350] + "…"
            bullets.append(f"### [{i}] {c.label}\n\n{excerpt}\n")
        practice = {
            "fr": (
                "\n## En pratique\n\n"
                "- Relancez dans 1–2 minutes, ou changez de moteur (Gemini / DeepSeek / SambaNova)."
            ),
            "ar": (
                "\n## عملياً\n\n"
                "- أعد المحاولة بعد دقيقة، أو بدّل المحرك (Gemini / DeepSeek / SambaNova)."
            ),
            "en": (
                "\n## In practice\n\n"
                "- Retry in 1–2 minutes, or switch engine (Gemini / DeepSeek / SambaNova)."
            ),
        }[locale_n]
        return AgentResult(
            answer=intro + "\n".join(bullets) + practice,
            source_type="web" if web_citations else "rag",
            sources=all_citations[:8],
            confidence_score=40,
            summary="",
        )

    locale_n = normalize_locale(locale)
    fallback = {
        "fr": (
            "## Réponse\n\n"
            "Les moteurs cloud sont temporairement indisponibles et aucune source "
            "utile n’a pu être récupérée.\n\n"
            "## En pratique\n\n"
            "1. Attendez 1–2 minutes puis réessayez.\n"
            "2. Changez de moteur : **Auto / Gemini / DeepSeek / SambaNova / Groq / Kimi**.\n"
            "3. Vérifiez aussi le Bulletin officiel : sgg.gov.ma"
        ),
        "ar": (
            "## الإجابة\n\n"
            "المحركات السحابية غير متاحة مؤقتاً ولم تُسترجع مصادر مفيدة.\n\n"
            "## عملياً\n\n"
            "1. انتظر دقيقة ثم أعد المحاولة.\n"
            "2. بدّل المحرك: **Auto / Gemini / DeepSeek / SambaNova**.\n"
            "3. راجع الجريدة الرسمية: sgg.gov.ma"
        ),
        "en": (
            "## Answer\n\n"
            "Cloud engines are temporarily unavailable and no useful sources were retrieved.\n\n"
            "## In practice\n\n"
            "1. Wait 1–2 minutes and retry.\n"
            "2. Switch engine: **Auto / Gemini / DeepSeek / SambaNova / Groq / Kimi**.\n"
            "3. Check the official gazette: sgg.gov.ma"
        ),
    }[locale_n]
    return AgentResult(
        answer=fallback,
        source_type="system",
        sources=[],
        confidence_score=15,
        summary="",
    )
