"""Contexte multi-tours : relier les questions de suivi à la conversation."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

_FOLLOWUP_RE = re.compile(
    r"(?i)\b("
    r"en\s+quelle|quelle\s+ann[eé]e|quand|quelle\s+date|date\s+d|"
    r"mise\s+[aà]\s*jour|mis[e]?\s+[aà]\s*jour|entr[eé]e\s+en\s+vigueur|"
    r"et\s+(ça|ca|cela)|et\s+pour|plus\s+de\s+d[eé]tail|explique|"
    r"c['’]?est\s+quoi|la\s+m[eê]me|celui[- ]ci|celle[- ]ci|cette\s+loi|"
    r"ce\s+projet|ce\s+texte|et\s+ensuite|pourquoi|comment\s+ça|"
    r"les\s+sanctions|les\s+peines|qui\s+a\s+adopt|"
    r"ann[eé]e|annee|update|updated|year|"
    r"pourquoi|comment|combien|lequel|laquelle|"
    r"continue|précise|precise|détail|detail|et\s+alors|ensuite|"
    r"what|why|how|when|which|same|this|that|"
    r"en\s+fran[cç]ais|in\s+french|traduis|translate"
    r")\b"
    r"|لماذا|كيف|متى|ماذا|أين|وشنو|شنو|علاش|واش|فين|نفس|هذا|هذه|ذلك|تلك|"
    r"زيد|وضح|فسر|كمل|والمزيد|بأكثر|التفاصيل|بالفرنسية|بالعربية"
)

_PRONOUN_RE = re.compile(
    r"(?i)\b(elle|il|ça|ca|cela|cette|ce|ceux|celles|y|en|lui|leur|même|meme)\b"
    r"|هذا|هذه|ذلك|تلك|هو|هي|هم|هن"
)

_LAW_RE = re.compile(
    r"(?i)(?:projet\s+de\s+loi|loi)\s*n[°ºo]?\s*([\d.]+)|n[°ºo]?\s*(19[.\s]?25)"
    r"|قانون\s*(?:رقم)?\s*([\d.]+)"
)

# Mots qui indiquent un NOUVEAU thème juridique (pas une suite)
_TOPIC_SWITCH_HINTS = re.compile(
    r"(?i)\b("
    r"immobilier|immobili[eè]re|foncier|fonci[eè]re|bail|baux|location|"
    r"propri[eé]t[eé]|copropri[eé]t[eé]|cadastre|ancfcc|"
    r"travail|salari[eé]|contrat\s+de\s+travail|cnss|"
    r"commerce|commercial|soci[eé]t[eé]|sarl|sa\b|"
    r"famille|moudawana|divorce|mariage|h[eé]ritage|"
    r"p[eé]nal|criminel|contravention|"
    r"fiscal|imp[oô]t|tva|is\b|"
    r"donn[eé]es|cndp|num[eé]rique|"
    r"عقاري|عقار|كراء|إيجار|شغل|أسرة|طلاق|زواج|ضريبي|تجاري"
    r")\b"
    r"|dimmobile|immobile\s*r|loi\s+d.?immob"
)


def load_session_history(
    db: Session,
    session_id: str | None,
    *,
    limit: int = 8,
) -> list[dict[str, str]]:
    """Historique chat retiré du CDC — toujours vide."""
    return []


def _word_count(q: str) -> int:
    return len(re.findall(r"[a-zA-ZÀ-ÿ0-9\u0600-\u06FF]+", q or ""))


def _normalize_typos(q: str) -> str:
    t = (q or "").strip()
    t = re.sub(r"(?i)\bdimmobile\b", "immobilier", t)
    t = re.sub(r"(?i)\bimmobile\s*r\b", "immobilier", t)
    t = re.sub(r"(?i)\bnanimaux\b", "animaux", t)
    t = re.sub(r"(?i)\brtestxte\b", "texte", t)
    t = re.sub(r"(?i)\bnonc[eé]\b", "énoncé", t)
    t = re.sub(r"(?i)\blioi\b", "lois", t)
    return t


def is_topic_switch(question: str, history: list[dict[str, str]]) -> bool:
    """True si la question introduit un thème juridique différent du fil."""
    if not history:
        return False
    from app.services.topic_filter import (
        is_animal_law_query,
        is_immobilier_query,
        is_panorama_laws_query,
        tokenize_question,
    )

    q = _normalize_typos(question)
    # Demande de panorama / toutes les lois 2026 = nouveau périmètre (pas suite animaux)
    if is_panorama_laws_query(q):
        return True
    # « en français », « pourquoi », « les sanctions » = suite, pas nouveau thème
    if _FOLLOWUP_RE.search(q) or _PRONOUN_RE.search(q):
        # Sauf si un thème juridique explicite est aussi présent (ex. « et pour l'immobilier ? »)
        if not _TOPIC_SWITCH_HINTS.search(q) and not is_immobilier_query(q):
            return False

    q_tokens = tokenize_question(q)
    hist_blob = " ".join(
        f"{t.get('question', '')} {t.get('summary', '')}" for t in history[-3:]
    )
    hist_tokens = tokenize_question(hist_blob)

    # Ex. « immobilier » après un fil animaux
    if _TOPIC_SWITCH_HINTS.search(q) or is_immobilier_query(q):
        if is_animal_law_query(hist_blob) and not is_animal_law_query(q):
            return True
        if q_tokens and hist_tokens and not (q_tokens & hist_tokens):
            return True
        if is_immobilier_query(q) and not is_immobilier_query(hist_blob):
            return True

    return False


def is_followup_question(question: str, history: list[dict[str, str]]) -> bool:
    if not history:
        return False
    q = _normalize_typos(question)
    if not q:
        return False
    if is_topic_switch(q, history):
        return False

    from app.services.topic_filter import tokenize_question

    words_n = _word_count(q)
    q_tokens = tokenize_question(q)

    # Pronoms / marqueurs de suite explicites
    if _FOLLOWUP_RE.search(q) or _PRONOUN_RE.search(q):
        return True

    # Très court ET sans nouveau thème → suite
    if words_n <= 6 and not q_tokens:
        return True
    if words_n <= 4 and not is_topic_switch(q, history):
        # « en français », « et les sanctions » — déjà couvert par FOLLOWUP_RE
        # Eviter de traiter « immobilier » comme suite
        if not q_tokens:
            return True
        return False

    if words_n <= 12 and not q_tokens:
        return True
    return False


def _extract_law_refs(*texts: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for m in _LAW_RE.finditer(text or ""):
            num = (m.group(1) or m.group(2) or m.group(3) or "").replace(" ", "")
            if not num:
                continue
            if num.startswith("19") and "25" in num and "." not in num:
                num = "19.25"
            label = f"projet de loi n°{num}" if num else m.group(0)
            key = label.lower()
            if key not in seen:
                seen.add(key)
                found.append(label)
    return found


def format_history_for_llm(
    history: list[dict[str, str]],
    *,
    max_turns: int = 6,
    topic_switch: bool = False,
) -> str:
    if not history:
        return ""
    if topic_switch:
        parts: list[str] = [
            "HISTORIQUE (contexte antérieur — le message actuel CHANGE DE SUJET ; "
            "réponds UNIQUEMENT au nouveau sujet, n'impose pas l'ancien thème) :"
        ]
    else:
        parts = [
            "HISTORIQUE DU FIL (relie ta réponse à ces tours si c'est une suite ; "
            "si l'utilisateur change clairement de sujet, suis le nouveau sujet) :"
        ]
    for i, turn in enumerate(history[-max_turns:], 1):
        ans = turn.get("summary") or turn.get("answer") or ""
        ans = re.sub(r"\s+", " ", ans).strip()
        if len(ans) > 700:
            ans = ans[:700] + "…"
        parts.append(f"Tour {i} — Utilisateur : {turn.get('question', '')}")
        parts.append(f"Tour {i} — Assistant : {ans}")
    return "\n".join(parts)


def history_to_chat_messages(
    history: list[dict[str, str]],
    *,
    max_turns: int = 6,
    max_answer_chars: int = 900,
) -> list[dict[str, str]]:
    """Convertit l'historique en messages OpenAI (user/assistant)."""
    messages: list[dict[str, str]] = []
    for turn in history[-max_turns:]:
        q = (turn.get("question") or "").strip()
        a = (turn.get("summary") or turn.get("answer") or "").strip()
        a = re.sub(r"\s+", " ", a)
        if len(a) > max_answer_chars:
            a = a[:max_answer_chars] + "…"
        if q:
            messages.append({"role": "user", "content": q})
        if a:
            messages.append({"role": "assistant", "content": a})
    return messages


def _history_topic_anchor(history: list[dict[str, str]], current_q: str = "") -> str:
    """Mots-clés du fil — uniquement si le message actuel reste sur le même thème."""
    from app.services.topic_filter import is_animal_law_query, is_immobilier_query

    if current_q and is_topic_switch(current_q, history):
        return ""

    blob = " ".join(
        f"{t.get('question', '')} {t.get('summary', '')} {(t.get('answer') or '')[:400]}"
        for t in history[-4:]
    )
    # Si la question actuelle est immobilière, ancre immobilier même avec historique animal
    if current_q and is_immobilier_query(current_q):
        return (
            "droit immobilier Maroc lois baux commerciaux 49-16 "
            "baux habitation 67-12 droits réels 39-08 propriété"
        )
    if is_animal_law_query(blob) and not (current_q and is_immobilier_query(current_q)):
        laws = _extract_law_refs(blob)
        law = laws[0] if laws else "projet de loi n°19.25"
        return f"animaux errants Maroc {law} sanctions identification"
    if is_immobilier_query(blob):
        return (
            "droit immobilier Maroc lois baux 49-16 67-12 "
            "droits réels propriété ANCFCC"
        )
    return ""


def resolve_with_history(
    question: str,
    history: list[dict[str, str]],
) -> tuple[str, str, bool]:
    """
    Retourne (question_pour_recherche, bloc_historique_llm, est_suivi).
    """
    q = _normalize_typos(question)
    switched = is_topic_switch(q, history) if history else False
    hist_block = format_history_for_llm(history, topic_switch=switched)
    if not history:
        from app.services.topic_filter import is_panorama_laws_query, is_immobilier_query

        if is_panorama_laws_query(q):
            return (
                f"{q}\n\n"
                "PANORAMA LÉGISLATIF : dresse une LISTE STRUCTURÉE par domaine "
                "(finances, élections, procédure, commerce, animaux, immobilier…) "
                "des lois / projets adoptés ou publiés en 2026 au Maroc, avec numéro et résumé. "
                "Ne te limite PAS à un seul texte.",
                hist_block,
                False,
            )
        return q, hist_block, False

    last = history[-1]
    prev_q = last.get("question") or ""
    prev_a = last.get("summary") or last.get("answer") or ""
    followup = is_followup_question(q, history)
    topic_anchor = _history_topic_anchor(history, q)

    if switched:
        # Nouveau sujet : recherche libre, historique seulement informatif
        from app.services.topic_filter import is_immobilier_query, is_panorama_laws_query

        resolved = q
        if is_panorama_laws_query(q):
            resolved = (
                f"{q}\n\n"
                "IMPORTANT : l'utilisateur veut TOUTES les lois / réformes 2026 au Maroc "
                "(panorama multi-domaines), PAS seulement la loi animaux 19.25. "
                "Structure par domaine : finances, élections, procédure civile, commerce, "
                "immobilier, animaux, conventions… Avec numéro + résumé pour chaque texte. "
                "Utilise les sources web et le corpus ; indique ce qui est adopté vs en discussion."
            )
            resolved = (
                f"{resolved}\nMots-clés recherche : lois Maroc 2026 Bulletin officiel "
                f"loi de finances élections Code commerce procédure civile"
            )
            return resolved, hist_block, False
        if is_immobilier_query(q):
            resolved = (
                f"{q}\n\n"
                "Sujet : DROIT IMMOBILIER marocain. "
                "Liste les lois pertinentes (baux, propriété, droits réels…) "
                "avec numéro, intitulé et énoncé / résumé des dispositions clés. "
                "Ne parle PAS des animaux errants ni de la loi 19.25."
            )
            topic_anchor = (
                "lois immobilières Maroc 49-16 67-12 39-08 "
                "baux commerciaux habitation propriété"
            )
            resolved = f"{resolved}\nMots-clés recherche : {topic_anchor}"
        return resolved, hist_block, False

    laws = _extract_law_refs(prev_q, prev_a, q)
    law_bit = f" ({laws[0]})" if laws else ""

    if followup:
        # Ancrage LÉGER pour la recherche web seulement — le LLM reçoit la question brute
        resolved = q
        if topic_anchor:
            resolved = f"{q}\nMots-clés recherche : {topic_anchor}"
        elif law_bit:
            resolved = f"{q}\nMots-clés recherche : {laws[0] if laws else ''} Maroc"
        return resolved, hist_block, True

    resolved = q
    if topic_anchor and not switched:
        resolved = f"{q}\nMots-clés recherche : {topic_anchor}"
    return resolved, hist_block, False
