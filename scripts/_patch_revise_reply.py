#!/usr/bin/env python3
"""Patch end of revise_plaidoirie_body for reply + softer no-op."""
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "backend/app/services/plaidoirie_revise.py"
text = p.read_text(encoding="utf-8")
old = '''    title_out, body_out = _parse_title_body(raw, title_in or (title or "مرافعة"), body_in)

    def _still_thin(after: str) -> bool:
        if not need_fill:
            return False
        check = targets or thin_before
        return any(_is_section_thin(after, mk) for mk in check)

    def _intro_ok(after: str) -> bool:
        if not wants_intro:
            return True
        a, b = _norm_cmp(body_in), _norm_cmp(after)
        if len(b) >= len(a) + 60:
            return True
        # Préfixe changé = intro ajoutée en tête
        common = 0
        for x, y in zip(a, b):
            if x == y:
                common += 1
            else:
                break
        return common < min(80, max(20, len(a) // 5)) or _changed_enough(body_in, after)

    too_shy = (
        not _changed_enough(body_in, body_out)
        or (expand and len(_norm_cmp(body_out)) < len(_norm_cmp(body_in)) + 80)
        or _still_thin(body_out)
        or (wants_intro and not _intro_ok(body_out))
    )
    # Si intro OK même sans fill sections → ne pas bloquer
    if wants_intro and _intro_ok(body_out) and not need_fill:
        too_shy = False
    if too_shy:
        logger.warning(
            "revise no-op detected — retry harder case=%s fill=%s intro=%s",
            case_id or "-",
            need_fill,
            wants_intro,
        )
        retry_hint = (
            "Tu DOIS ajouter une INTRODUCTION réelle en tête du BODY (4–8 phrases), "
            "puis garder le reste. N'exige pas de remplir خامساً sauf si demandé.\\n"
            if wants_intro
            else "Tu DOIS remplir concrètement les sections visées (corps sous خامساً / لهذه الأسباب si demandés).\\n"
            "Si DÉVELOPPER : allonge nettement le passage.\\n"
        )
        retry_prompt = (
            base_prompt
            + "\\n\\n=== ALERTE ===\\n"
            "Ta réponse précédente était trop proche de l'original — INTERDIT.\\n"
            + retry_hint
            + "Sortie TITLE / BODY uniquement.\\n"
        )
        raw2, provider2 = chat_free_tier(
            retry_prompt,
            _SYSTEM,
            preferred="openai",
            strict_preferred=True,
            allow_ollama=False,
            model_override=model,
            max_tokens=8000,
            temperature=0.65,
        )
        if raw2:
            title_out, body_out = _parse_title_body(
                raw2, title_out or title_in or (title or "مرافعة"), body_in
            )
            provider = provider2 or provider
        still_shy = (
            not _changed_enough(body_in, body_out)
            or (expand and len(_norm_cmp(body_out)) < len(_norm_cmp(body_in)) + 80)
            or _still_thin(body_out)
            or (wants_intro and not _intro_ok(body_out))
        )
        if wants_intro and _intro_ok(body_out) and not need_fill:
            still_shy = False
        if still_shy:
            detail = (
                "L'IA n'a pas encore ajouté l'introduction demandée. "
                "Renvoyez simplement « ajoute une introduction » — les fautes sont acceptées."
                if wants_intro
                else (
                    "L'IA n'a pas réussi à appliquer la modification (sections encore vides "
                    "ou texte trop peu changé). Renvoyez la même demande une fois — "
                    "le langage naturel / avec fautes est accepté."
                )
            )
            raise HTTPException(status_code=502, detail=detail)

    if mapping:
        title_out = unmask_text(title_out, mapping)
        body_out = unmask_text(body_out, mapping)

    logger.info("revise via %s case=%s changed=1 fill=%s", provider, case_id or "-", need_fill)
    return title_out, body_out, provider
'''

# The file uses real newlines not escaped - read from file marker instead
start = text.find('    title_out, body_out = _parse_title_body(raw, title_in or (title or "مرافعة"), body_in)')
if start < 0:
    raise SystemExit("start not found")
end = text.find('    return title_out, body_out, provider\n', start)
if end < 0:
    raise SystemExit("end not found")
end = end + len('    return title_out, body_out, provider\n')

new = r'''    title_out, body_out, reply_out = _parse_title_body(
        raw, title_in or (title or "مرافعة"), body_in
    )

    def _still_thin(after: str) -> bool:
        if not need_fill:
            return False
        check = targets or thin_before
        return any(_is_section_thin(after, mk) for mk in check)

    def _intro_ok(after: str) -> bool:
        if not wants_intro:
            return True
        a, b = _norm_cmp(body_in), _norm_cmp(after)
        if len(b) >= len(a) + 60:
            return True
        common = 0
        for x, y in zip(a, b):
            if x == y:
                common += 1
            else:
                break
        return common < min(80, max(20, len(a) // 5)) or _changed_enough(body_in, after)

    too_shy = (
        not _changed_enough(body_in, body_out)
        or (expand and len(_norm_cmp(body_out)) < len(_norm_cmp(body_in)) + 80)
        or _still_thin(body_out)
        or (wants_intro and not _intro_ok(body_out))
    )
    if wants_intro and _intro_ok(body_out) and not need_fill:
        too_shy = False
    if need_fill and not _still_thin(body_out):
        too_shy = False
    if wants_explain and reply_out and _changed_enough(body_in, body_out):
        too_shy = False
    if too_shy:
        logger.warning(
            "revise no-op detected — retry harder case=%s fill=%s intro=%s",
            case_id or "-",
            need_fill,
            wants_intro,
        )
        retry_hint = (
            "Tu DOIS ajouter une INTRODUCTION réelle en tête du BODY (4–8 phrases), "
            "puis garder le reste. N'exige pas de remplir خامساً sauf si demandé.\n"
            if wants_intro
            else (
                "Tu DOIS remplir concrètement les sections visées "
                "(corps sous خامساً / لهذه الأسباب si demandés).\n"
                "Si DÉVELOPPER : allonge nettement le passage.\n"
                "Si QUESTION : ajoute aussi ASSISTANT_REPLY en français.\n"
            )
        )
        retry_prompt = (
            base_prompt
            + "\n\n=== ALERTE ===\n"
            "Ta réponse précédente était trop proche de l'original — INTERDIT.\n"
            + retry_hint
            + "Sortie ASSISTANT_REPLY (si question) + TITLE / BODY uniquement.\n"
        )
        raw2, provider2 = chat_free_tier(
            retry_prompt,
            _SYSTEM,
            preferred="openai",
            strict_preferred=True,
            allow_ollama=False,
            model_override=model,
            max_tokens=8000,
            temperature=0.65,
        )
        if raw2:
            title_out, body_out, reply2 = _parse_title_body(
                raw2, title_out or title_in or (title or "مرافعة"), body_in
            )
            if reply2:
                reply_out = reply2
            provider = provider2 or provider
        still_shy = (
            not _changed_enough(body_in, body_out)
            or (expand and len(_norm_cmp(body_out)) < len(_norm_cmp(body_in)) + 80)
            or _still_thin(body_out)
            or (wants_intro and not _intro_ok(body_out))
        )
        if wants_intro and _intro_ok(body_out) and not need_fill:
            still_shy = False
        if need_fill and not _still_thin(body_out):
            still_shy = False
        if wants_explain and reply_out and len(reply_out) >= 40:
            if _changed_enough(body_in, body_out) or abs(len(body_out) - len(body_in)) >= 30:
                still_shy = False
        if still_shy:
            detail = (
                "L'IA n'a pas encore ajouté l'introduction demandée. "
                "Renvoyez simplement « ajoute une introduction » — les fautes sont acceptées."
                if wants_intro
                else (
                    "L'IA n'a pas réussi à appliquer la modification (sections encore vides "
                    "ou texte trop peu changé). Renvoyez la même demande une fois — "
                    "le langage naturel / avec fautes est accepté."
                )
            )
            raise HTTPException(status_code=502, detail=detail)

    if mapping:
        title_out = unmask_text(title_out, mapping)
        body_out = unmask_text(body_out, mapping)
        if reply_out:
            reply_out = unmask_text(reply_out, mapping)

    if wants_explain and not reply_out:
        reply_out = (
            "« لهذه الأسباب » (pour ces motifs) est le titre de clôture de la plaidoirie : "
            "sous ce titre, l’avocat doit écrire les الملتمسات — les demandes concrètes "
            "(ex. النفقة، الحضانة، التعويض) déduites des faits déjà exposés. "
            "J’ai complété / mis à jour le corps sous ce titre dans le document."
        )

    logger.info("revise via %s case=%s changed=1 fill=%s", provider, case_id or "-", need_fill)
    return title_out, body_out, provider, reply_out or ""
'''

p.write_text(text[:start] + new + text[end:], encoding="utf-8")
print("patched revise end ok")
