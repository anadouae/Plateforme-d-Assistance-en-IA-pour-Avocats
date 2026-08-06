def generate_synthesis(document_name: str, text: str, language: str = "fr") -> dict:
    from app.services.extraction import (
        extract_amounts,
        extract_dates,
        extract_parties,
        extract_risk_clauses,
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

    preview = text[:6000].replace("\n", " ")
    llm_data = generate_synthesis_structured(document_name, text, language=locale)
    if llm_data:
        return {
            "parties": llm_data["parties"],
            "key_dates": llm_data["key_dates"],
            "amounts": llm_data["amounts"],
            "risk_clauses": llm_data["risk_clauses"],
            "attention_points": llm_data["attention_points"],
            "summary": llm_data["summary"],
            "sources": [Citation(label=document_name, excerpt=preview[:300])],
            "disclaimer": disclaimer,
        }

    parties = extract_parties(text)
    dates = extract_dates(text)
    amounts = extract_amounts(text)
    risks = extract_risk_clauses(text)
    summary = generate_synthesis_text(document_name, text, language=locale) or preview[:800]
    attention = []
    if risks:
        attention.append(f"{len(risks)} clause(s) à risque potentiel détectée(s)")

    return {
        "parties": parties,
        "key_dates": dates,
        "amounts": amounts,
        "risk_clauses": risks,
        "attention_points": attention,
        "summary": summary,
        "sources": [Citation(label=document_name, excerpt=preview[:300])],
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
        chunks.append(f"[{name}]\n{raw[:2500]}")
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
    all_text = "\n\n".join(chunks)[:5000]
    fallback_summary = all_text[:900] if all_text else case_reference
    llm_text = (
        generate_case_analysis_text(case_reference, all_text, language=locale)
        if all_text
        else None
    )
    summary = llm_text or fallback_summary

    hits = search_case_documents(cabinet_id, case_id, f"dossier {case_reference}")
    legal_issues: list[str] = []
    risks: list[str] = []
    if hits:
        for h in hits[:5]:
            label = h.get("source") or "Source"
            legal_issues.append(f"{label}: {(h.get('text') or '')[:160]}")
        risks = [f"Vérifier la pertinence de {h.get('source')}" for h in hits[:3]]

    checklist = [
        "Vérifier les pièces indexées et leur qualité OCR",
        "Contrôler les délais et échéances mentionnés",
        "Confirmer les parties et montants avec le client",
    ]
    if not key_docs:
        checklist.insert(0, "Ajouter des documents extractibles au dossier")

    confidence = 75 if hits or chunks else 30
    if llm_text:
        confidence = min(92, confidence + 10)

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
