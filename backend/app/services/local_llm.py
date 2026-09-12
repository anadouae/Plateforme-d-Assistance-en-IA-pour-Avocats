"""LexHub local LLM — Ollama primary (sanad-legal). Groq optional fallback only."""

from __future__ import annotations

import json
import logging
import re

from app.core.config import settings
from app.services.language import (
    get_case_analysis_prompt,
    get_chat_answer_prompt,
    parse_chat_llm_response,
    get_synthesis_prompt,
    get_system_prompt,
    normalize_locale,
    parse_llm_json,
)

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = (
    "Tu es LexHub-Legal, assistant juridique ouvert (niveau Mistral/Gemini). "
    "Réponds de façon utile et structurée. Les extraits enrichissent ta réponse — "
    "tu n'es pas limité à les recopier. N'invente pas de numéros précis absents des extraits. "
    "Structure : réponse, fondement légal, points d'attention. "
    "Termine par : « Ceci ne constitue pas un avis juridique. »"
)

SYNTHESIS_PROMPT = (
    "Tu es LexHub-Legal. Produis une synthèse structurée du document juridique marocain. "
    "Inclure : objet du document, parties, faits essentiels, enjeux juridiques, "
    "délais éventuels, risques. Cite uniquement le texte fourni. "
    "Termine par : « Ceci ne constitue pas un avis juridique. »"
)

CASE_ANALYSIS_PROMPT = (
    "Tu es LexHub-Legal. Analyse le dossier juridique à partir des pièces fournies. "
    "Structure ta réponse en : 1) Faits 2) Pièces clés 3) Enjeux juridiques "
    "4) Risques / délais 5) Points à vérifier. Ne invente aucun fait absent des extraits. "
    "Termine par : « Ceci ne constitue pas un avis juridique. »"
)


def _provider() -> str:
    return (settings.LLM_PROVIDER or "ollama").strip().lower()


def _ollama_chat(messages: list[dict], stream: bool = False, timeout: float | None = None):
    import httpx

    t = timeout if timeout is not None else settings.OLLAMA_CHAT_TIMEOUT
    return httpx.post(
        f"{settings.OLLAMA_BASE_URL}/api/chat",
        json={
            "model": settings.OLLAMA_MODEL,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": 0.1, "num_predict": settings.OLLAMA_NUM_PREDICT},
        },
        timeout=t,
    )


def _call_ollama(prompt: str, system: str = SYSTEM_PROMPT) -> str | None:
    try:
        response = _ollama_chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )
        response.raise_for_status()
        content = response.json().get("message", {}).get("content", "")
        return content.strip() or None
    except Exception as exc:
        logger.warning("Ollama unavailable (%s), trying generate API", exc)
        try:
            import httpx

            response = httpx.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": f"{system}\n\n{prompt}",
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": settings.OLLAMA_NUM_PREDICT},
                },
                timeout=settings.OLLAMA_CHAT_TIMEOUT,
            )
            response.raise_for_status()
            return response.json().get("response", "").strip() or None
        except Exception as exc2:
            logger.warning("Ollama generate failed: %s", exc2)
            return None


def _call_groq(prompt: str, system: str = SYSTEM_PROMPT) -> str | None:
    if not settings.GROQ_API_KEY:
        return None
    try:
        import httpx

        response = httpx.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.55,
                "max_tokens": 4096,
            },
            timeout=float(settings.LLM_HTTP_TIMEOUT_SEC or 30),
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.warning("Groq fallback failed: %s", exc)
        return None


def _call_kimi(prompt: str, system: str = SYSTEM_PROMPT) -> str | None:
    """Moonshot Kimi — API compatible OpenAI."""
    if not settings.KIMI_API_KEY:
        return None
    try:
        import httpx

        base = settings.KIMI_BASE_URL.rstrip("/")
        response = httpx.post(
            f"{base}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.KIMI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.KIMI_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.55,
                "max_tokens": 6144,
            },
            timeout=float(settings.LLM_HTTP_TIMEOUT_SEC or 30),
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.warning("Kimi API failed: %s", exc)
        return None


def _normalize_chat_provider(llm_provider: str | None = None) -> str:
    """Résout openai | mistral | groq | kimi | gemini | deepseek | together | sambanova | auto."""
    if getattr(settings, "LLM_FORCE_OPENAI", True) and (settings.OPENAI_API_KEY or "").strip():
        return "openai"
    raw = (llm_provider or settings.LLM_PROVIDER or "auto").strip().lower()
    if raw in ("openai", "mistral", "kimi", "groq", "gemini", "deepseek", "together", "sambanova", "auto"):
        return raw
    if settings.LLM_CHAT_CLOUD_FIRST and (
        settings.OPENAI_API_KEY
        or settings.MISTRAL_API_KEY
        or settings.GROQ_API_KEY
        or settings.KIMI_API_KEY
        or settings.GEMINI_API_KEY
        or settings.DEEPSEEK_API_KEY
        or settings.TOGETHER_API_KEY
        or settings.SAMBANOVA_API_KEY
    ):
        return "auto"
    return raw


def _call_chat_cloud(
    prompt: str,
    system: str = SYSTEM_PROMPT,
    provider_override: str | None = None,
    prior_messages: list[dict[str, str]] | None = None,
) -> str | None:
    """ChatGPT (OpenAI) en priorité via free router ; secours free-tiers si autorisé."""
    provider = _normalize_chat_provider(provider_override)

    if settings.LLM_USE_FREE_ROUTER:
        from app.services.free_llm_router import chat_free_tier

        text, used = chat_free_tier(
            prompt,
            system,
            preferred=provider if provider != "auto" else "openai",
            allow_ollama=bool(settings.LLM_ALLOW_CLOUD_FALLBACK)
            and not bool(getattr(settings, "LLM_FORCE_OPENAI", True)),
            prior_messages=prior_messages,
        )
        if text:
            logger.info("chat_cloud via free_router/%s", used)
            return text

    # Secours minimal si router désactivé / OpenAI KO
    if getattr(settings, "LLM_OPENAI_STRICT", False):
        return None
    if provider == "kimi":
        return _call_kimi(prompt, system) or _call_groq(prompt, system)
    if provider == "groq":
        return _call_groq(prompt, system) or _call_kimi(prompt, system)
    return _call_groq(prompt, system) or _call_kimi(prompt, system)


def generate_with_prompt(prompt: str, system: str = SYSTEM_PROMPT) -> str | None:
    """ChatGPT d'abord si forcé ; sinon Ollama / Groq selon LLM_PROVIDER."""
    if getattr(settings, "LLM_FORCE_OPENAI", True) and (settings.OPENAI_API_KEY or "").strip():
        raw = _call_chat_cloud(prompt, system, provider_override="openai")
        if raw:
            return raw
        if getattr(settings, "LLM_OPENAI_STRICT", False):
            return None

    provider = _provider()
    if provider == "ollama":
        result = _call_ollama(prompt, system)
        if result:
            return result
        if settings.GROQ_API_KEY and settings.LLM_ALLOW_CLOUD_FALLBACK:
            logger.info("Falling back to Groq after Ollama failure")
            return _call_groq(prompt, system)
        return None

    if provider == "groq":
        result = _call_groq(prompt, system)
        if result:
            return result
        return _call_ollama(prompt, system)

    if provider == "kimi":
        result = _call_kimi(prompt, system)
        if result:
            return result
        if settings.GROQ_API_KEY and settings.LLM_ALLOW_CLOUD_FALLBACK:
            logger.info("Falling back to Groq after Kimi failure")
            return _call_groq(prompt, system)
        return _call_ollama(prompt, system)

    # unknown → ollama only
    return _call_ollama(prompt, system)


def generate_from_sources_sync(
    question: str,
    sources_text: str,
    language: str | None = None,
    llm_provider: str | None = None,
) -> str | None:
    """Rédaction cloud-first à partir d'extraits (Markdown libre)."""
    locale = normalize_locale(language)
    prompt = f"EXTRAITS :\n{sources_text}\n\nQUESTION : {question}\n\nRÉPONSE :"
    system = get_system_prompt(locale)
    if settings.LLM_CHAT_CLOUD_FIRST and (
        settings.MISTRAL_API_KEY or settings.GROQ_API_KEY or settings.KIMI_API_KEY
    ):
        raw = _call_chat_cloud(prompt, system, provider_override=llm_provider)
        if raw:
            return raw
    return generate_with_prompt(prompt, system)


def generate_open_chat_sync(
    question: str,
    language: str | None = None,
    custom_prompt: str | None = None,
    llm_provider: str | None = None,
    soft_context: str = "",
    prior_messages: list[dict[str, str]] | None = None,
) -> dict | None:
    """Réponse claire style Groq/Kimi (toujours cloud-first)."""
    from app.services.language import get_open_chat_prompt

    locale = normalize_locale(language)
    context_block = ""
    if soft_context.strip():
        context_block = (
            f"CONTEXTE / SOURCES (utilise si pertinent ; respecte aussi l'historique du chat) :\n"
            f"{soft_context.strip()}\n\n"
        )
    prompt = (
        f"{context_block}"
        f"QUESTION UTILISATEUR (message actuel — PRIORITÉ) : {question}\n\n"
        "Historique du fil dans les messages précédents : utilise-le s'il aide, "
        "mais si l'utilisateur change de sujet, suis le nouveau.\n"
        "Rédige comme Mistral Chat / Gemini : CLAIR, COMPLET, multi-points si besoin.\n"
        "Les sources ci-dessus ENRICHISSENT — ne te limite pas à un seul texte.\n"
        "N'invente pas un numéro de loi précis absent du contexte.\n"
        'Retourne UNIQUEMENT un JSON : "answer" (Markdown avec \\n\\n), "summary" (2 phrases).'
    )
    system = get_open_chat_prompt(locale, custom_prompt)
    raw = _call_chat_cloud(
        prompt,
        system,
        provider_override=llm_provider,
        prior_messages=prior_messages,
    )
    if not raw:
        raw = _call_ollama(prompt, system)
    data = parse_chat_llm_response(raw)
    if data:
        return data
    if raw and raw.strip():
        return {"answer": raw.strip(), "summary": ""}
    return None


def generate_clear_ungrounded_sync(
    question: str,
    language: str | None = None,
    custom_prompt: str | None = None,
    llm_provider: str | None = None,
    prior_messages: list[dict[str, str]] | None = None,
) -> dict | None:
    """Quand pas de source fiable : réponse claire Groq/Kimi SANS inventer de références."""
    return generate_open_chat_sync(
        question,
        language=language,
        custom_prompt=custom_prompt,
        llm_provider=llm_provider,
        soft_context=(
            "AUCUNE source juridique précise indexée pour ce thème. "
            "Réponds quand même de façon claire et utile (cadre général, méthode, vigilance), "
            "SANS aucun numéro de loi inventé. Respecte l'historique du fil."
        ),
        prior_messages=prior_messages,
    )


def synthesize_structured_answer_sync(
    question: str,
    sources_text: str,
    language: str | None = None,
    custom_prompt: str | None = None,
    llm_provider: str | None = None,
    prior_messages: list[dict[str, str]] | None = None,
) -> dict | None:
    """Couches 3–4 : free router / cloud rédigent une réponse claire ancrée sur les sources."""
    has_cloud = bool(
        settings.MISTRAL_API_KEY
        or settings.GROQ_API_KEY
        or settings.KIMI_API_KEY
        or settings.GEMINI_API_KEY
        or settings.DEEPSEEK_API_KEY
        or settings.TOGETHER_API_KEY
        or settings.SAMBANOVA_API_KEY
    )
    if not has_cloud and not settings.LLM_USE_GROQ_FOR_CHAT:
        return None
    prov = _normalize_chat_provider(llm_provider)
    if prov == "mistral" and not settings.MISTRAL_API_KEY:
        prov = "auto"
    if prov == "groq" and not settings.GROQ_API_KEY:
        prov = "auto"
    if prov == "kimi" and not settings.KIMI_API_KEY:
        prov = "auto"
    locale = normalize_locale(language)
    year_hint = ""
    from app.services.language import extract_year_filter, _has_substantive_legal_topic

    years = extract_year_filter(question)
    if years and not _has_substantive_legal_topic(question):
        year_hint = (
            f"\nIMPORTANT : l'utilisateur cible l'année {years[0]}. "
            "Priorise les textes de cette année ; si la liste est partielle, dis-le "
            "et élargis utilement (ex. textes liés publiés fin année précédente)."
        )
    prompt = (
        f"SOURCES (enrichissement — web + corpus + dossier + historique) :\n{sources_text}\n\n"
        f"QUESTION UTILISATEUR (message actuel — PRIORITÉ ABSOLUE) : {question}\n\n"
        f"{year_hint}\n"
        "Mode Mistral/Gemini : LLM = cerveau ouvert, sources = citations & dates.\n"
        "- Réponds au message ACTUEL (pas à l'ancien sujet du fil s'il a changé).\n"
        "- Réponse COMPLÈTE et structurée ; si panorama / liste → plusieurs domaines.\n"
        "- Priorise dossier/document s'il est présent.\n"
        "- Cite [1][2] pour les faits précis issus des sources.\n"
        "- N'invente aucun numéro précis absent des sources.\n"
        "- Sources partielles → 1 phrase de prudence + réponse utile.\n"
        "- Interdit « les sources fournies ne mentionnent pas » comme seule réponse.\n"
        "Produis le JSON demandé."
    )
    from app.services.language import get_open_chat_prompt

    # Un seul system prompt ouvert (évite double « cage sources »)
    system = get_open_chat_prompt(locale, custom_prompt) + "\n\n" + get_chat_answer_prompt(
        locale, custom_prompt
    )
    raw = _call_chat_cloud(
        prompt,
        system,
        provider_override=prov,
        prior_messages=prior_messages,
    )
    data = parse_chat_llm_response(raw)
    if not data:
        return None
    answer_raw = data.get("answer", "")
    if isinstance(answer_raw, dict):
        # Preserve Markdown structure (headings / lists), never flatten with spaces
        parts: list[str] = []
        for key, val in answer_raw.items():
            if not val:
                continue
            title = str(key).strip().replace("_", " ")
            body = str(val).strip()
            if not body.startswith("#"):
                parts.append(f"## {title.title()}\n\n{body}")
            else:
                parts.append(body)
        answer = "\n\n".join(parts).strip()
    else:
        answer = str(answer_raw).strip()
    # Normalize escaped newlines sometimes returned inside JSON strings
    answer = answer.replace("\\n", "\n").replace("\\t", "  ")
    answer = re.sub(r"\n{3,}", "\n\n", answer).strip()
    summary = str(data.get("summary", "")).strip()
    if not answer:
        return None
    return {"answer": answer, "summary": summary}


def synthesize_web_answer_sync(
    question: str,
    sources_text: str,
    language: str | None = None,
) -> str | None:
    """Groq synthesis for web-sourced answers (fast, cloud)."""
    if not settings.GROQ_API_KEY or not settings.LLM_USE_GROQ_FOR_WEB:
        return None
    locale = normalize_locale(language)
    system = (
        get_system_prompt(locale)
        + " Tu réponds à partir des extraits web fournis, comme un assistant moderne. "
        "Adapte le pays (Maroc / France / autre) à la QUESTION. "
        "Interdit de digresser sur un autre pays. "
        "Interdit la phrase « les sources fournies ne mentionnent pas ». "
        "N'invente aucun numéro de loi absent des sources. "
        "INTERDIT de te contenter de « allez sur sgg.gov.ma » : "
        "donne 3–6 domaines / réformes concrètes trouvées dans les sources "
        "(investissement, procédure, travail, données, etc.) avec dates si présentes."
    )
    prompt = (
        f"SOURCES WEB :\n{sources_text}\n\n"
        f"QUESTION : {question}\n\n"
        "Réponds utilement avec du contenu concret (pas seulement un lien). "
        "Cite les URLs utilisées."
    )
    return _call_groq(prompt, system)


async def generate_from_sources(
    question: str,
    sources_text: str,
    language: str | None = None,
) -> str | None:
    return generate_from_sources_sync(question, sources_text, language=language)


def generate_synthesis_text(
    document_name: str,
    document_text: str,
    language: str | None = None,
) -> str | None:
    """Secours prose intelligente (sans JSON) — cloud-first."""
    locale = normalize_locale(language)
    body = _sample_document_text(document_text or "", max_chars=16000)
    prose_system = {
        "fr": (
            "Tu es LexHub-Legal (niveau Claude). "
            "Rédige une synthèse intelligente Markdown pour un avocat : "
            "adapte les titres au type réel du document (contrat, jugement, lettre…). "
            "280–500 mots. N'invente rien. Français uniquement. "
            "Termine par une section « Suite utile »."
        ),
        "ar": (
            "أنت LexHub-Legal بمستوى Claude. "
            "اكتب تلخيصاً ذكياً Markdown للمحامي مكيّفاً مع نوع الوثيقة. "
            "280–500 كلمة. لا تختلق. بالعربية. اختم بـ «ما يُستحسن فعله»."
        ),
    }.get(locale, get_synthesis_prompt(locale))
    prompt = (
        f"DOCUMENT : {document_name}\n\n"
        f"TEXTE :\n{body}\n\n"
        "Rédige la synthèse intelligente (Markdown libre, pas de JSON)."
    )
    return _llm_synthesis_chat(prompt, prose_system)


def generate_document_answer_sync(
    question: str,
    document_name: str,
    document_text: str,
    language: str | None = None,
    llm_provider: str | None = None,
) -> str | None:
    """Réponse IA basée uniquement sur le texte du document."""
    from app.services.extraction import get_document_context_excerpt
    from app.services.language import get_document_qa_prompt, normalize_locale

    locale = normalize_locale(language)
    context = get_document_context_excerpt(document_text, question, max_len=14000)
    if not context.strip():
        return None
    prompt = (
        f"DOCUMENT : {document_name}\n\n"
        f"TEXTE (extrait pertinent) :\n{context}\n\n"
        f"QUESTION : {question}\n\n"
        "Réponds en t'appuyant UNIQUEMENT sur ce texte."
    )
    system = get_document_qa_prompt(locale)
    prov = (llm_provider or _provider()).strip().lower()
    raw = _call_chat_cloud(prompt, system, provider_override=prov if prov in ("kimi", "groq") else None)
    if not raw and settings.GROQ_API_KEY:
        raw = _call_groq(prompt, system)
    if not raw and settings.KIMI_API_KEY:
        raw = _call_kimi(prompt, system)
    if not raw:
        raw = _call_ollama(prompt, system)
    return raw.strip() if raw else None


def _sample_document_text(text: str, max_chars: int = 28000) -> str:
    """Échantillonne début / milieu / fin pour les longs documents."""
    cleaned = (text or "").strip()
    if len(cleaned) <= max_chars:
        return cleaned
    head = int(max_chars * 0.42)
    mid = int(max_chars * 0.28)
    tail = max_chars - head - mid
    center = len(cleaned) // 2
    mid_start = max(0, center - mid // 2)
    return (
        cleaned[:head]
        + "\n\n[…]\n\n"
        + cleaned[mid_start : mid_start + mid]
        + "\n\n[…]\n\n"
        + cleaned[-tail:]
    )


def _llm_synthesis_chat(prompt: str, system: str) -> str | None:
    """Cloud-first (routeur) pour une synthèse digne d'un cabinet."""
    provider = _normalize_chat_provider(_provider())
    raw = _call_chat_cloud(prompt, system, provider_override=provider)
    if not raw and settings.GROQ_API_KEY:
        raw = _call_groq(prompt, system)
    if not raw and settings.KIMI_API_KEY:
        raw = _call_kimi(prompt, system)
    if not raw:
        logger.info("Synthesis: cloud unavailable — skip Ollama CPU fallback")
    return raw.strip() if raw else None


def generate_synthesis_structured(
    document_name: str,
    document_text: str,
    language: str | None = None,
    *,
    assume_native: bool = False,
    source_kind: str = "file",
    transcript_quality: str | None = None,
) -> dict | None:
    """Synthèse intelligente LLM (tout type de pièce) — JSON riche, pas de squelette vide."""
    from app.services.extraction import is_scrambled_arabic, safe_repair_arabic_text

    locale = normalize_locale(language)
    # Word / prose native : ne pas « réparer » BIDI ni injecter un hint OCR faux.
    if assume_native:
        cleaned = (document_text or "").strip()
    else:
        cleaned = safe_repair_arabic_text(document_text or "")
    if len(cleaned.strip()) < 20:
        return None

    scramble_hint = ""
    if not assume_native and is_scrambled_arabic(cleaned):
        scramble_hint = (
            "\nATTENTION : OCR arabe partiellement désordonné. "
            "Synthétise uniquement les faits clairement lisibles. "
            "N'invente aucune loi ni partie. "
            "Si le sens est trop douteux, indique-le dans attention_points.\n"
        )

    audio_hint = ""
    if source_kind == "audio" or (document_name or "").lower().endswith(
        (".ogg", ".wav", ".mp3", ".m4a", ".webm", ".mpeg")
    ):
        q = (transcript_quality or "medium").lower()
        if q == "poor":
            audio_hint = (
                "\nATTENTION CRITIQUE — TRANSCRIPTION AUDIO FAIBLE : "
                "Le texte est un déchiffrage Whisper approximatif. "
                "INTERDIT d'interpréter un mot déformé comme une ville "
                "(ex. inventer مكناس), un nom de juge, une accusation précise. "
                "Dans summary : dis clairement que le déchiffrage est peu fiable, "
                "cite seulement les fragments sûrs entre guillemets, "
                "et mets dans attention_points : « إعادة التفريغ أو الإملاء المباشر موصى به ». "
                "Listes parties/dates/amounts vides si non explicites.\n"
            )
        else:
            audio_hint = (
                "\nSOURCE AUDIO : transcription automatique. "
                "N'invente pas de lieux ni d'identités absents du texte. "
                "Si un mot est ambigu, signale-le dans attention_points.\n"
            )

    body = _sample_document_text(cleaned, max_chars=24000)
    prompt = (
        f"DOCUMENT : {document_name}\n\n"
        f"TEXTE COMPLET / ÉCHANTILLON REPRÉSENTATIF :\n{body}\n\n"
        f"{scramble_hint}{audio_hint}"
        "Produis le JSON de synthèse INTELLIGENTE demandé. "
        "Comprends d'abord le type de document, puis rédige un summary utile à l'avocat. "
        "N'invente rien."
    )

    system = get_synthesis_prompt(locale)
    raw = _llm_synthesis_chat(prompt, system)
    data = parse_llm_json(raw) if raw else None

    # 2) Si le JSON échoue mais qu'on a du prose LLM → seconde passe stricte JSON
    if not data and raw and len(raw.strip()) > 120:
        repair_prompt = (
            "Convertis STRICTEMENT le texte suivant en JSON valide avec les clés "
            "document_type, parties, key_dates, amounts, risk_clauses, attention_points, summary. "
            "Ne perds pas le fond intelligent du résumé.\n\n"
            f"TEXTE:\n{raw[:8000]}"
        )
        repaired = _llm_synthesis_chat(repair_prompt, system)
        data = parse_llm_json(repaired) if repaired else None

    # 3) Dernier recours : demander un summary Markdown intelligent (sans JSON)
    if not data:
        prose_system = {
            "fr": (
                "Tu es LexHub-Legal. Rédige une synthèse intelligente Markdown "
                "pour un avocat (280–500 mots), adaptée au type réel du document. "
                "N'invente rien. Français uniquement."
            ),
            "ar": (
                "أنت LexHub-Legal. اكتب تلخيصاً ذكياً Markdown للمحامي (280–500 كلمة) "
                "مكيّفاً مع نوع الوثيقة. لا تختلق. بالعربية فقط."
            ),
        }.get(locale, "Write an intelligent legal Markdown synthesis. Do not invent.")
        prose = _llm_synthesis_chat(
            f"DOCUMENT : {document_name}\n\nTEXTE :\n{body[:16000]}\n\n"
            f"{scramble_hint}{audio_hint}Rédige la synthèse.",
            prose_system,
        )
        if prose and len(prose.strip()) >= 120 and prose.strip()[:80] not in cleaned[:800]:
            return {
                "document_type": "",
                "parties": [],
                "key_dates": [],
                "amounts": [],
                "risk_clauses": [],
                "attention_points": [],
                "summary": prose.strip(),
            }
        return None

    def _as_list(key: str) -> list[str]:
        val = data.get(key, [])
        if not isinstance(val, list):
            return [str(val)] if val else []
        return [str(item).strip() for item in val if str(item).strip()][:40]

    summary = str(data.get("summary", "")).strip()
    if not summary:
        return None
    # Rejeter un collage OCR brut
    if len(summary) > 100 and summary[:90] in cleaned[:900]:
        return None

    doc_type = str(data.get("document_type") or "").strip()
    attention = _as_list("attention_points")
    if doc_type:
        type_label = {
            "fr": f"Type de pièce : {doc_type}",
            "ar": f"نوع الوثيقة : {doc_type}",
            "en": f"Document type: {doc_type}",
        }.get(locale, f"نوع الوثيقة : {doc_type}")
        attention = [type_label] + attention

    return {
        "document_type": doc_type,
        "parties": _as_list("parties"),
        "key_dates": _as_list("key_dates"),
        "amounts": _as_list("amounts"),
        "risk_clauses": _as_list("risk_clauses"),
        "attention_points": attention[:20],
        "summary": summary,
    }


def generate_case_analysis_text(
    case_reference: str,
    sources_text: str,
    language: str | None = None,
) -> str | None:
    """
    Analyse dossier via LLM — timeout HTTP court (ne pas utiliser OLLAMA_CHAT_TIMEOUT=600).
    En échec / lenteur → None (l'appelant fournit un résumé extractif).
    """
    locale = normalize_locale(language)
    prompt = (
        f"DOSSIER : {case_reference}\n\n"
        f"PIÈCES / EXTRAITS :\n{(sources_text or '')[:5000]}\n\n"
        "Analyse concise du dossier (faits, enjeux, points d'attention). "
        "400 mots max. N'invente rien."
    )
    system = get_case_analysis_prompt(locale)

    # Cloud uniquement. Ollama CPU bloque l'UI plusieurs minutes.
    try:
        if settings.MISTRAL_API_KEY or settings.GROQ_API_KEY or settings.KIMI_API_KEY:
            raw = _call_chat_cloud(prompt, system)
            if raw and len(raw.strip()) > 40:
                return raw.strip()
    except Exception as exc:
        logger.warning("Case analysis cloud failed: %s", exc)
    logger.info("Case analysis: skip Ollama — extractive fallback")
    return None


def generate_stream_chunks(
    question: str,
    sources_text: str,
    language: str | None = None,
):
    """Yield text chunks for SSE — Ollama streaming first."""
    if not settings.LLM_CHAT_USE_OLLAMA:
        return

    locale = normalize_locale(language)
    prompt = f"EXTRAITS :\n{sources_text}\n\nQUESTION : {question}"
    messages = [
        {"role": "system", "content": get_system_prompt(locale)},
        {"role": "user", "content": prompt},
    ]

    if _provider() == "ollama" or not settings.GROQ_API_KEY:
        try:
            import httpx

            with httpx.Client(timeout=180.0) as client:
                with client.stream(
                    "POST",
                    f"{settings.OLLAMA_BASE_URL}/api/chat",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "messages": messages,
                        "stream": True,
                        "options": {"temperature": 0.1, "num_predict": settings.OLLAMA_NUM_PREDICT},
                    },
                ) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line:
                            continue
                        data = json.loads(line)
                        delta = data.get("message", {}).get("content", "")
                        if delta:
                            yield delta
                        if data.get("done"):
                            return
                    return
        except Exception as exc:
            logger.warning("Ollama stream failed: %s", exc)

    if settings.GROQ_API_KEY and settings.LLM_ALLOW_CLOUD_FALLBACK:
        try:
            import httpx

            with httpx.Client(timeout=float(settings.LLM_HTTP_TIMEOUT_SEC or 30)) as client:
                with client.stream(
                    "POST",
                    GROQ_API_URL,
                    headers={
                        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": GROQ_MODEL,
                        "messages": messages,
                        "temperature": 0.1,
                        "max_tokens": 2048,
                        "stream": True,
                    },
                ) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line.startswith("data: "):
                            continue
                        payload = line[6:]
                        if payload.strip() == "[DONE]":
                            break
                        chunk = json.loads(payload)
                        delta = chunk["choices"][0].get("delta", {}).get("content", "")
                        if delta:
                            yield delta
                    return
        except Exception as exc:
            logger.warning("Groq stream failed: %s", exc)

    full = generate_from_sources_sync(question, sources_text, language=locale)
    if full:
        words = full.split(" ")
        for i in range(0, len(words), 3):
            yield " ".join(words[i : i + 3]) + " "


def llm_health() -> dict:
    """Status for /health endpoint."""
    ollama_ok = False
    try:
        import httpx

        r = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=3.0)
        ollama_ok = r.status_code == 200
    except Exception:
        ollama_ok = False

    provider = _provider()
    model = settings.KIMI_MODEL if provider == "kimi" else settings.OLLAMA_MODEL
    free_router = {}
    try:
        from app.services.free_llm_router import router_status

        free_router = router_status()
    except Exception:
        free_router = {}
    return {
        "provider": provider,
        "model": model,
        "ollama": ollama_ok,
        "mistral": bool(settings.MISTRAL_API_KEY),
        "kimi": bool(settings.KIMI_API_KEY),
        "gemini": bool(settings.GEMINI_API_KEY),
        "deepseek": bool(settings.DEEPSEEK_API_KEY),
        "together": bool(settings.TOGETHER_API_KEY),
        "sambanova": bool(settings.SAMBANOVA_API_KEY),
        "free_router": bool(settings.LLM_USE_FREE_ROUTER),
        "free_tiers": free_router,
        "cloud_fallback": bool(settings.LLM_ALLOW_CLOUD_FALLBACK),
        "groq_for_web": bool(settings.GROQ_API_KEY and settings.LLM_USE_GROQ_FOR_WEB),
        "groq_for_chat": bool(settings.GROQ_API_KEY and settings.LLM_USE_GROQ_FOR_CHAT),
    }
